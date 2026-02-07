#!/usr/bin/env python3
"""
数据库自动备份脚本
"""

import os
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import subprocess


class DatabaseBackup:
    """数据库备份"""

    def __init__(
        self,
        db_path: str = "./data/litekb.db",
        backup_dir: str = "./data/backups",
        keep_days: int = 7,
    ):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.keep_days = keep_days

    def create_backup(self) -> Path:
        """创建备份"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"litekb_{timestamp}.sql.gz"
        backup_path = self.backup_dir / backup_name

        if self.db_path.suffix == ".db":
            # SQLite 备份
            return self._backup_sqlite(backup_path)
        else:
            # PostgreSQL 备份
            return self._backup_postgres(backup_path)

    def _backup_sqlite(self, backup_path: Path) -> Path:
        """SQLite 备份"""
        # 创建临时复制
        temp_path = backup_path.with_suffix(".db")
        shutil.copy(self.db_path, temp_path)

        # 压缩
        with open(temp_path, "rb") as f_in:
            with gzip.open(backup_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        temp_path.unlink()
        return backup_path

    def _backup_postgres(self, backup_path: Path) -> Path:
        """PostgreSQL 备份"""
        env = os.environ.copy()
        env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "")

        db_name = os.getenv("POSTGRES_DB", "litekb")
        db_user = os.getenv("POSTGRES_USER", "litekb")
        db_host = os.getenv("POSTGRES_HOST", "localhost")

        cmd = [
            "pg_dump",
            "-h",
            db_host,
            "-U",
            db_user,
            "-d",
            db_name,
            "-F",
            "c",  # custom format
            "-f",
            str(backup_path),
        ]

        result = subprocess.run(cmd, env=env, capture_output=True)

        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr.decode()}")

        return backup_path

    def cleanup_old_backups(self):
        """清理旧备份"""
        cutoff = datetime.now() - timedelta(days=self.keep_days)

        for backup in self.backup_dir.glob("litekb_*.sql.gz"):
            if backup.stat().st_mtime < cutoff.timestamp():
                backup.unlink()
                print(f"Removed: {backup}")

    def restore_backup(self, backup_path: Path):
        """恢复备份"""
        if backup_path.suffix == ".gz":
            temp_path = backup_path.with_suffix(".db")

            with gzip.open(backup_path, "rb") as f_in:
                with open(temp_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            shutil.copy(temp_path, self.db_path)
            temp_path.unlink()
        else:
            shutil.copy(backup_path, self.db_path)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Database backup tool")
    parser.add_argument("action", choices=["backup", "restore", "cleanup"])
    parser.add_argument("--path", help="Backup file path (for restore)")
    parser.add_argument("--keep", type=int, default=7, help="Days to keep backups")

    args = parser.parse_args()

    backup = DatabaseBackup(keep_days=args.keep)

    if args.action == "backup":
        path = backup.create_backup()
        print(f"Backup created: {path}")

    elif args.action == "cleanup":
        backup.cleanup_old_backups()
        print("Cleanup completed")

    elif args.action == "restore":
        if not args.path:
            print("Error: --path required for restore")
            return
        backup.restore_backup(Path(args.path))
        print(f"Restored from: {args.path}")


if __name__ == "__main__":
    main()
