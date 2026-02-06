# LiteKB Database Migrations

## Quick Start

### 1. Initialize migrations (first time)
```bash
cd backend
alembic init alembic
```

### 2. Create a new migration
```bash
alembic revision -m "your_migration_name"
```

### 3. Run migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision>

# Show current revision
alembic current

# Show migration history
alembic history

# Rollback one migration
alembic downgrade -1
```

### 4. Generate SQL (for review)
```bash
alembic upgrade --sql > migration.sql
```

## Migration Commands

| Command | Description |
|---------|-------------|
| `alembic revision -m "name"` | Create new migration |
| `alembic upgrade head` | Apply all migrations |
| `alembic upgrade +1` | Apply next migration |
| `alembic downgrade -1` | Rollback one migration |
| `alembic history` | Show migration history |
| `alembic heads` | Show current heads |
| `alembic branches` | Show branch points |
| `alembic current` | Show current revision |

## Auto-generate Migrations

If you change `models.py`, you can auto-generate migrations:

```bash
# Show what would be generated
alembic revision --autogenerate -m "description"

# Then review and apply
alembic upgrade head
```

## Configuration

Edit `alembic.ini` to configure database URL:

```ini
sqlalchemy.url = sqlite:///./data/litekb.db
# or for PostgreSQL
# sqlalchemy.url = postgresql://user:pass@localhost/litekb
```

## Troubleshooting

### Migration fails
```bash
# Check pending migrations
alembic pending

# Show current state
alembic current -v

# Stamp a specific revision (if needed)
alembic stamp <revision>
```

### Conflicts
```bash
# Show merged heads
alembic merge heads -m "merge"

# Then upgrade to merged head
alembic upgrade head
```

## Best Practices

1. **Always review** auto-generated migrations
2. **Test migrations** in development first
3. **Backup database** before production migrations
4. **Document** migration rationale
5. **Use meaningful names** for migrations
