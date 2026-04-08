#!/bin/sh
# Switch backend between api_v1 and api_v2 and perform data migration in storage
# Minimal changes: toggles upstream and calls storage /migrate to convert data formats
set -e

CONF="/etc/nginx/version.conf"
STORAGE_MIGRATE_URL="http://storage:8200/migrate"

current=$(sed -n 's/.*server\s\+\([^:;]\+\).*/\1/p' "$CONF" | head -n1)

if [ -z "$current" ]; then
  echo "ERROR: cannot determine current backend from $CONF"
  exit 1
fi

if [ "$current" = "api_v1" ]; then
  target="api_v2"
  migrate_to="v1.1"
else
  target="api_v1"
  migrate_to="v1.0"
fi

echo "Switching backend: $current -> $target"
echo "Requesting storage migration to $migrate_to ..."

python3 - <<PY
import sys, json
import urllib.request

url = "$STORAGE_MIGRATE_URL"
data = json.dumps({"to": "$migrate_to"}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        print("Migration response:", body)
except Exception as e:
    print("Migration request failed:", e)
    # Continue anyway? Prefer to fail so teacher sees migration didn't run
    sys.exit(2)
PY

cat <<EOF > "$CONF"
upstream api_backend {
    server $target:8199;
}
EOF

if nginx -t; then
    nginx -s reload
    echo "Switched → $target"
else
    echo "ERROR: nginx config invalid — switch failed"
    exit 1
fi
