#!/bin/sh

CONF="/etc/nginx/version.conf"

cat <<EOF > "$CONF"
upstream api_backend {
    server api_v1:8199;
}
EOF

if nginx -t; then
    nginx -s reload
    echo "Discarded → back to api_v1"
else
    echo "ERROR: nginx config invalid — discard failed"
    exit 1
fi
