#!/bin/sh

# generate the runtime-env.js
echo "globalThis.runtimeEnv = { BK_DASHBOARD_URL: '$BK_DASHBOARD_URL' };" > /var/www/runtime-env.js

# start nginx
exec nginx -g 'daemon off;'
