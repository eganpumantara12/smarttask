#!/usr/bin/env bash
# Backup database PostgreSQL ke ./backups (BL-09 / NFR-03). Jadwalkan harian lewat cron, mis.:
#   0 2 * * *  cd /opt/smarttask && ./scripts/backup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
FILE="backups/smarttask_$(date +%Y%m%d_%H%M%S).sql.gz"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$FILE"
echo "Backup tersimpan: $FILE"
# simpan 14 backup terakhir
ls -1t backups/smarttask_*.sql.gz | tail -n +15 | xargs -r rm --
