# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import os

import pymysql
from tencent_apigateway_common.env import Env

from conf.log_utils import get_logging_config, makedirs_when_not_exists

pymysql.install_as_MySQLdb()
# Patch version info to forcedly pass Django client check
pymysql.version_info = 1, 4, 2, "final", 0

env = Env()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
BK_APP_CODE = env.str("BK_APP_CODE", "bk_apigateway")
BK_APP_SECRET = env.str("BK_APP_SECRET")
SECRET_KEY = env.str("SECRET_KEY", BK_APP_SECRET)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "esb",
    "esb.bkcore",
    "django_prometheus",
)

MIDDLEWARE_CLASSES = (
    # 这个必须在最前
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "esb.middlewares.APICommonMiddleware",
    "esb.middlewares.DebugHelperMiddleware",
    # 这个必须在最后
    "django_prometheus.middleware.PrometheusAfterMiddleware",
)

ROOT_URLCONF = "urls"

WSGI_APPLICATION = "wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "esb.jinja2.environment",
        },
    },
]


# mysql pool options
DJ_POOL_OPTIONS = {"pool_size": 10, "max_overflow": 100, "recycle": 600}

# Internationalization

# LANGUAGE_CODE = 'zh-hans'
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True

# timezone
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True


# language
# 避免循环引用
def _(s):
    return s


LANGUAGES = (
    ("en", _("English")),
    ("zh-hans", _("简体中文")),
)
LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
    os.path.join(BASE_DIR, "locale/locale_api"),
)

# Authentication
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

# Static files
SITE_URL = "/"

STATIC_URL = SITE_URL + "static/"

STATIC_VERSION = "1.0"

STATIC_ROOT = "staticfiles"


# database 配置
DATABASES = {
    "default": {
        "ENGINE": env.str("BK_ESB_DATABASE_ENGINE", "django.db.backends.mysql"),
        "NAME": env.str("BK_ESB_DATABASE_NAME"),
        "USER": env.str("BK_ESB_DATABASE_USER", ""),
        "PASSWORD": env.str("BK_ESB_DATABASE_PASSWORD", ""),
        "HOST": env.str("BK_ESB_DATABASE_HOST", ""),
        "PORT": env.int("BK_ESB_DATABASE_PORT", 3306),
        "TEST_CHARSET": env.str("DATABASE_TEST_CHARSET", "utf8"),
        "TEST_COLLATION": env.str(
            "DATABASE_TEST_COLLATION",
            "utf8_general_ci",
        ),
    },
}

## database ssl
BK_ESB_DATABASE_TLS_ENABLED = env.bool("BK_ESB_DATABASE_TLS_ENABLED", False)
if BK_ESB_DATABASE_TLS_ENABLED:
    default_ssl_options = {
        "ca": env.str("BK_ESB_DATABASE_TLS_CERT_CA_FILE", ""),
    }
    # mTLS
    default_cert_file = env.str("BK_ESB_DATABASE_TLS_CERT_FILE", "")
    default_key_file = env.str("BK_ESB_DATABASE_TLS_CERT_KEY_FILE", "")
    if default_cert_file and default_key_file:
        default_ssl_options["cert"] = default_cert_file
        default_ssl_options["key"] = default_key_file

    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}

    DATABASES["default"]["OPTIONS"]["ssl"] = default_ssl_options


# log 配置
LOG_DIR = env.str("BK_ESB_LOG_PATH", "")
LOGGING = get_logging_config(
    env.str("LOG_LEVEL", "WARNING"),
    LOG_DIR,
    log_to_file=env.bool("BK_ESB_LOG_TO_FILE", False) and bool(LOG_DIR),
    log_api_log_to_file=bool(LOG_DIR),
)
makedirs_when_not_exists(LOG_DIR)

# 功能开关
BK_AUTH_ENABLED = env.bool("BK_AUTH_ENABLED", True)
API_GATEWAY_ADAPTER_ENABLED = env.bool("API_GATEWAY_ADAPTER_ENABLED", True)
MYSQL_POOL_ENABLED = env.bool("BK_ESB_MYSQL_POOL_ENABLED", True)

# https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-DATA_UPLOAD_MAX_MEMORY_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = env.str("BK_ESB_DATA_UPLOAD_MAX_MEMORY_SIZE", 10485760)  # 10MB

# component esb_conf
ESB_SITE_ESB_CONF = "components.esb_conf.config"

# 默认超时时间
REQUEST_TIMEOUT_SECS = 30

ESB_TOKEN = env.str("ESB_TOKEN")
ESB_COMPONENTS_SWAGGER_TOKEN = env.str("ESB_COMPONENTS_SWAGGER_TOKEN", "673919d2d8714252a40d148601187e70")

BK_ESB_GATEWAY_NAME = env.str("BK_ESB_GATEWAY_NAME", "bk-esb")

# esb ssl root dir
SSL_ROOT_DIR = env.str("BK_ESB_CERT_PATH", "/cert")

# 缓存配置
BK_TOKEN_CACHE_MAXSIZE = env.int("BK_TOKEN_CACHE_MAXSIZE", 2000)
BK_TOKEN_CACHE_TTL_SECONDS = env.int("BK_TOKEN_CACHE_TTL_SECONDS", 60)
LIST_APP_SECRETS_CACHE_MAXSIZE = env.int("LIST_APP_SECRETS_CACHE_MAXSIZE", 2000)
LIST_APP_SECRETS_CACHE_TTL = env.int("LIST_APP_SECRETS_CACHE_TTL", 300)
VERIFY_APP_SECRET_RESULT_CACHE_MAXSIZE = env.int("VERIFY_APP_SECRET_RESULT_CACHE_MAXSIZE", 2000)
VERIFY_APP_SECRET_RESULT_CACHE_TTL = env.int("VERIFY_APP_SECRET_RESULT_CACHE_TTL", 300)
DB_CHANNEL_REFRESH_INTERVAL = env.int("DB_CHANNEL_REFRESH_INTERVAL", 300)
BK_ESB_JWT_PUBLIC_KEY_CACHE_MAXSIZE = env.int("BK_ESB_JWT_PUBLIC_KEY_CACHE_MAXSIZE", 100)
BK_ESB_JWT_PUBLIC_KEY_CACHE_TTL = env.int("BK_ESB_JWT_PUBLIC_KEY_CACHE_TTL", 86400)

# ==============================================================================
# 第三方接口配置
# ==============================================================================
# paas host
PAAS_HOST = env.str("BK_PAAS_URL", "")

# host for bk login
HOST_BK_LOGIN = env.str("BK_PAAS_LOGIN_URL", "")

BK_AUTH_API_URL = env.str("BK_AUTH_API_URL", "")

# apps
BK_IAM_URL = env.str("BK_IAM_URL", "")
BK_DOCS_CENTER_URL = env.str("BK_DOCS_CENTER_URL", "")
BK_GSEKIT_URL = env.str("BK_GSEKIT_URL", "")
BK_ITSM_URL = env.str("BK_ITSM_URL", "")
BK_SOPS_URL = env.str("BK_SOPS_URL", "")
BK_LOG_SEARCH_URL = env.str("BK_LOG_SEARCH_URL", "")

# host for cc
HOST_CC = env.str("BK_CMDB_URL", "")

# host for cc v3
HOST_CC_V3 = env.str("BK_CMDB_V3_URL", "")

# host for job, default 80 for http/8443 for https
HOST_JOB = env.str("BK_JOB_URL", "")

# JOB 是否启用 SSL 验证
JOB_SSL = env.bool("JOB_SSL", True)

# host for gse, default 80 for http/8443 for https
HOST_GSE = env.str("BK_GSE_URL", "")

# host for gse proc
GSE_PROC_HOST = env.str("BK_GSE_PROC_HOST", "")
GSE_PROC_PORT = env.str("BK_GSE_PROC_PORT", "")

# host for gse cacheapi
GSE_CACHEAPI_HOST = env.str("BK_GSE_CACHEAPI_HOST", "")
GSE_CACHEAPI_PORT = env.str("BK_GSE_CACHEAPI_PORT", "")

# host for gse process management service
GSE_PMS_HOST = env.str("BK_GSE_PMS_URL", "")

# host for gse config
BK_GSE_CONFIG_ADDR = env.str("BK_GSE_CONFIG_URL", "")

# host for DATA，数据平台监控告警系统，default 80 for http/8443 for https
HOST_DATA = env.str("BK_DATA_URL", "")

# host for DATA BKSQL service
DATA_BKSQL_HOST = env.str("BK_DATA_BKSQL_URL", "")

# host for DATA PROCESSORAPI
DATA_PROCESSORAPI_HOST = env.str("BK_DATA_PROCESSORAPI_URL", "")

# host for DATA Modelflow service
DATA_MODELFLOW_HOST = env.str("BK_DATA_MODELFLOW_URL", "")

# host for data v3
DATAV3_AUTHAPI_HOST = env.str("BK_DATA_V3_AUTHAPI_URL", "")
DATAV3_ACCESSAPI_HOST = env.str("BK_DATA_V3_ACCESSAPI_URL", "")
DATAV3_DATABUSAPI_HOST = env.str("BK_DATA_V3_DATABUSAPI_URL", "")
DATAV3_DATAFLOWAPI_HOST = env.str("BK_DATA_V3_DATAFLOWAPI_URL", "")
DATAV3_DATAMANAGEAPI_HOST = env.str("BK_DATA_V3_DATAMANAGEAPI_URL", "")
DATAV3_DATAQUERYAPI_HOST = env.str("BK_DATA_V3_DATAQUERYAPI_URL", "")
DATAV3_METAAPI_HOST = env.str("BK_DATA_V3_METAAPI_URL", "")
DATAV3_STOREKITAPI_HOST = env.str("BK_DATA_V3_STOREKITAPI_URL", "")
DATAV3_BKSQL_HOST = env.str("BK_DATA_V3_BKSQL_URL", "")
DATAV3_MODELAPI_HOST = env.str("BK_DATA_V3_MODELAPI_URL", "")
DATAV3_DATACUBEAPI_HOST = env.str("BK_DATA_V3_DATACUBEAPI_URL", "")
DATAV3_ALGORITHMAPI_HOST = env.str("BK_DATA_V3_ALGORITHMAPI_URL", "")
DATAV3_DATALABAPI_HOST = env.str("BK_DATA_V3_DATALABAPI_URL", "")
DATAV3_AIOPSAPI_HOST = env.str("BK_DATA_V3_AIOPSAPI_URL", "")
DATAV3_RESOURCECENTERAPI_HOST = env.str("BK_DATA_V3_RESOURCECENTERAPI_URL", "")
DATAV3_QUERYENGINEAPI_HOST = env.str("BK_DATA_V3_QUERYENGINEAPI_URL", "")
DATAV3_LANGSERVER_HOST = env.str("BK_DATA_V3_LANGSERVER_URL", "")

# host for fta,  default 80 for http/8443 for https
HOST_FTA = env.str("BK_FTA_URL", "")

# devops
DEVOPS_HOST = env.str("BK_DEVOPS_URL", "")

# cicdkit
CICDKIT_HOST = env.str("BK_CICDKIT_URL", "")

# monitor
MONITOR_HOST = env.str("BK_MONITOR_URL", "")
MONITOR_V3_HOST = env.str("BK_MONITOR_V3_URL", "")

# user_manage
USERMGR_HOST = env.str("BK_USERMGR_URL", "")

# bk_log
BK_LOG_HOST = env.str("BK_LOG_URL", "")

# nodeman
NODEMAN_HOST = env.str("BK_NODEMAN_URL", "")

# bscp
BK_BSCP_API_ADDR = env.str("BK_BSCP_API_URL", "")

# bk-ssm
BK_SSM_API_URL = env.str("BK_SSM_API_URL", "")
BK_SSM_ACCESS_TOKEN_CACHE_MAXSIZE = env.int("BK_SSM_ACCESS_TOKEN_CACHE_MAXSIZE", 2000)
BK_SSM_ACCESS_TOKEN_CACHE_TTL_SECONDS = env.int("BK_SSM_ACCESS_TOKEN_CACHE_TTL_SECONDS", 300)

# 从环境变量获取同步通道数据时豁免的自定义通道列表，格式为字符串，格式为：
# [{"board": "default", "method": "get", "path": "/cmsi/send_xxxx"}]
EXCLUDE_OFFICIAL_CHANNELS_WHEN_SYNCING = env.str("BK_ESB_EXCLUDE_OFFICIAL_CHANNELS_WHEN_SYNCING", default="")
