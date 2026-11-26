#!/usr/bin/env bash
# MongoDB のバックアップ（Node.js 版・Spring Boot（MongoDB）版。開発・検証用）
#   usage: tools/backup/mongo_backup.sh [保存先]   環境変数 MONGODB_URI（既定 mongodb://localhost:27017/cathreport）・KEEP_DAYS（既定 30）
#   復元: mongorestore --uri "$MONGODB_URI" --drop --gzip --archive=<ファイル>
set -euo pipefail
DEST="${1:-./backups}"
URI="${MONGODB_URI:-mongodb://localhost:27017/cathreport}"
mkdir -p "$DEST"
FILE="$DEST/mongo_$(date +%Y%m%d_%H%M%S).archive.gz"
mongodump --uri "$URI" --gzip --archive="$FILE"
echo "$(date '+%F %T') バックアップ: $FILE"
find "$DEST" -name "mongo_*.archive.gz" -mtime +"${KEEP_DAYS:-30}" -delete
