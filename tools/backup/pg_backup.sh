#!/usr/bin/env bash
# PostgreSQL のバックアップ（論理バックアップ・カスタム形式）。日次で実行し、古いものを自動で削除する。
#   usage: tools/backup/pg_backup.sh [保存先ディレクトリ]
#   環境変数: PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE（既定 localhost:5432 / cathreport）
#             KEEP_DAYS（日次の保存日数・既定 30）  KEEP_MONTHS（月初分の保存月数・既定 12）
#   cron の例（毎日 2:30）: 30 2 * * * /opt/cath-report/tools/backup/pg_backup.sh /var/backups/cath-report >> /var/log/cath-backup.log 2>&1
#   Docker の例: docker compose exec -T db pg_dump -U cathreport -Fc cathreport > cathreport_$(date +%Y%m%d).dump
set -euo pipefail
DEST="${1:-./backups}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-cathreport}" PGDATABASE="${PGDATABASE:-cathreport}"
KEEP_DAYS="${KEEP_DAYS:-30}"
KEEP_MONTHS="${KEEP_MONTHS:-12}"
mkdir -p "$DEST/daily" "$DEST/monthly"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$DEST/daily/${PGDATABASE}_${STAMP}.dump"
TMP="$FILE.part"

pg_dump --format=custom --compress=6 --no-owner --file="$TMP" "$PGDATABASE"
# 取得したファイルを読めるか確認してから確定する（壊れたバックアップを残さない）
pg_restore --list "$TMP" > /dev/null
mv "$TMP" "$FILE"
sha256sum "$FILE" > "$FILE.sha256"
echo "$(date '+%F %T') バックアップ: $FILE ($(du -h "$FILE" | cut -f1))"

# 月初は月次として保存
if [ "$(date +%d)" = "01" ]; then
  cp "$FILE" "$FILE.sha256" "$DEST/monthly/"
fi
# 保存期間を過ぎたものを削除
find "$DEST/daily" -name "*.dump*" -mtime +"$KEEP_DAYS" -delete
find "$DEST/monthly" -name "*.dump*" -mtime +"$((KEEP_MONTHS * 31))" -delete
