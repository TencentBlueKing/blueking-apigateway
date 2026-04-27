#!/bin/bash

CURRENT_DIR=$(pwd)

# 支持两种模式：
#   ./run.sh zach.devcloud.woa.com  → 使用域名访问（外部/有域名解析时）
#   ./run.sh                        → 默认使用 127.0.0.1:6006 直接访问 APISIX（服务器内部 e2e 测试）

if [[ -z $1 ]]; then
    BK_API_URL_TMPL="http://127.0.0.1:6006/api/{api_name}"
else
    DOMAIN=$1
    BK_API_URL_TMPL="http://bkapi.${DOMAIN}/api/{api_name}"
fi

# sync httpbin
docker run --rm \
    -v $CURRENT_DIR/httpbin/:/data/ \
    -e BK_APIGW_NAME=httpbin \
    -e BK_API_URL_TMPL="$BK_API_URL_TMPL" \
    -e BK_APP_CODE=bk_apigateway \
    -e BK_APP_SECRET=358627d8-d3e8-4522-8f16-b5530776bbb8 \
    --network=host \
    hub.bktencent.com/blueking/apigw-manager:3.0.3


# sync smoke
docker run --rm \
    -v $CURRENT_DIR/smoke/:/data/ \
    -e BK_APIGW_NAME=smoke \
    -e BK_API_URL_TMPL="$BK_API_URL_TMPL" \
    -e BK_APP_CODE=bk_apigateway \
    -e BK_APP_SECRET=358627d8-d3e8-4522-8f16-b5530776bbb8 \
    --network=host \
    hub.bktencent.com/blueking/apigw-manager:3.0.3

# sync smoke stage2
docker run \
    -v $CURRENT_DIR/smoke/:/data/ \
    -e BK_APIGW_NAME=smoke \
    -e BK_API_URL_TMPL="$BK_API_URL_TMPL" \
    -e BK_APP_CODE=bk_apigateway \
    -e BK_APP_SECRET=358627d8-d3e8-4522-8f16-b5530776bbb8 \
    --network=host \
    hub.bktencent.com/blueking/apigw-manager:3.0.3 \
    bash -c  'source /apigw-manager/bin/functions.sh && call_definition_command_or_exit sync_apigw_stage /data/definition.yaml --gateway-name=smoke --namespace="stage2" && call_definition_command_or_exit create_version_and_release_apigw /data/definition.yaml'
