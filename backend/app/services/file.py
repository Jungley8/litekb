"""
文件上传服务
"""

import tempfile
import os
from typing import Optional
from fastapi import UploadFile
from loguru import logger


class FileService:
    """文件服务"""

    ALLOWED_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/markdown": ".md",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }

    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    async def save_upload(self, file: UploadFile, kb_id: str) -> dict:
        """保存上传的文件"""
        # 验证类型
        content_type = file.content_type
        if content_type not in self.ALLOWED_TYPES:
            raise ValueError(f"不支持的文件类型: {content_type}")

        # 验证大小
        file_size = 0
        content = b""
        async for chunk in file:
            file_size += len(chunk)
            if file_size > self.MAX_SIZE:
                raise ValueError("文件大小超出限制 (10MB)")
            content += chunk

        # 保存到临时文件
        ext = self.ALLOWED_TYPES.get(content_type, ".tmp")
        temp_path = f"/tmp/{kb_id}_{file.filename}{ext}"

        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {temp_path}")

        return {
            "path": temp_path,
            "filename": file.filename,
            "content_type": content_type,
            "size": file_size,
        }

    async def delete_file(self, path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception as e:
            logger.error(f"Delete file failed: {e}")
        return False


file_service = FileService()
