#!/usr/bin/env bash
# Pulihkan database dari file backup: ./scripts/restore.sh backups/smarttask_XXXX.sql.gz
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -eq 1 ] || { echo "Pemakaian: $0 <file.sql.gz>"; exit 1; }
read -r -p "Ini akan MENIMPA data saat ini. Lanjut? (ketik ya) " ok
[ "$ok" = "ya" ] || exit 1
docker compose stop api
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" -c "CREATE DATABASE $POSTGRES_DB;"'
gunzip -c "$1" | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose start api
echo "Restore selesai."
