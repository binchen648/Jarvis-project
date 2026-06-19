#!/bin/bash
# Jarvis Database Backup Script
set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME=${DB_NAME:-jarvis}
DB_USER=${DB_USER:-postgres}
DB_CONTAINER=${DB_CONTAINER:-jarvisproject-db-1}
RETENTION_DAYS=${RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

echo "=== Database Backup ==="
echo "Backing up $DB_NAME..."

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backup saved: $BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Clean up old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete

echo "=== Backup complete ==="
