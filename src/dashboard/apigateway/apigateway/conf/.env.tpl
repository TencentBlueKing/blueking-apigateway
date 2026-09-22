ENCRYPT_KEY="dGVzdDMzNDA4YWJlNDMyNGJmYzE4Mjk4NGM3ZXRlc3Q="
BK_APP_SECRET="egrKq5TnJvlFiPLIrtquv3Mow792xVgTzqTiSrVkUIk="

DASHBOARD_CSRF_COOKIE_DOMAIN=".example.com"
# DASHBOARD_CSRF_COOKIE_NAME="bk_apigateway_csrftoken"
BK_LOGIN_URL="http://paas.example.com/login"

BK_API_URL_TMPL="https://bkapi.example.com/api/{api_name}"

BK_IAM_V4_ENABLED="false"
BK_IAM_V4_MANAGERS="admin"

BK_APIGW_DATABASE_HOST="localhost"

BK_APIGW_DATABASE_NAME="bk_apigateway"
BK_APIGW_DATABASE_HOST="localhost"
BK_APIGW_DATABASE_PORT=3306
BK_APIGW_DATABASE_USER="root"
BK_APIGW_DATABASE_PASSWORD=""

BK_ESB_DATABASE_NAME="bk_esb"
BK_ESB_DATABASE_HOST="localhost"
BK_ESB_DATABASE_PORT=3306
BK_ESB_DATABASE_USER="root"
BK_ESB_DATABASE_PASSWORD=""

BK_APIGW_REDIS_PASSWORD=""

# add the frontend domain, will add to CORS_ORIGIN_REGEX_WHITELIST
DASHBOARD_FE_URL="http://apigw.example.com"
# EE 可设为 false 关闭 ESB 的数据库、接口、任务及初始化；未设置默认为 true。
# TE 忽略此开关，保留外部 ESB 依赖；多租户模式沿用原有禁用 ESB 的行为。
ENABLE_ESB=true
