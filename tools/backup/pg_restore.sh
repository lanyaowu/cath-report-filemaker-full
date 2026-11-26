#!/usr/bin/env bash
# PostgreSQL の復元。指定したバックアップで、復元先の DB を作り直す（既存のデータは消える）。
#   usage: tools/backup/pg_restore.sh <バックアップ(.dump)> [復元先 DB 名]
#   例：本番を止めずに確認用 DB へ復元 → tools/backup/pg_restore.sh backups/daily/cathreport_20261120_023000.dump cathreport_check
#   注意：本番 DB へ戻すときは、アプリを停止してから実行すること。
set -euo pipefail
FILE="${1:?バックアップファイルを指定してください}"
TARGET="${2:-${PGDATABASE:-cathreport}}"
export PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-cathreport}"
if [ -f "$FILE.sha256" ]; then sha256sum --check --quiet "$FILE.sha256"; fi
echo "復元先: $TARGET（既存のデータは削除されます）"
if [ -z "${YES:-}" ]; then read -r -p "続けますか？ [yes/no] " a; [ "$a" = "yes" ] || exit 1; fi
dropdb --if-exists "$TARGET"
createdb "$TARGET"
pg_restore --no-owner --exit-on-error --dbname="$TARGET" "$FILE"
psql -d "$TARGET" -Atc "SELECT 'patients=' || (SELECT count(*) FROM patients) || ' reports=' || (SELECT count(*) FROM cath_reports) || ' audit_log=' || (SELECT count(*) FROM audit_log)"
echo "復元しました: $TARGET"
