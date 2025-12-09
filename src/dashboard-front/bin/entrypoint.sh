#!/bin/sh

# generate the runtime-env.js
sed -i "s#_BK_DASHBOARD_URL_#$BK_DASHBOARD_URL#g" /var/www/index.html
sed -i "s#_BK_SITE_PATH_#$BK_DASHBOARD_SUBPATH#g" /var/www/index.html
sed -i "s#_BK_STATIC_URL_#$BK_DASHBOARD_SUBPATH#g" /var/www/index.html

# start nginx
exec nginx -g 'daemon off;'
