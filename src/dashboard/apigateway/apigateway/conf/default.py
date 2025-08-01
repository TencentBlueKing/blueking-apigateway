#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from pathlib import Path
from typing import List
from urllib.parse import quote

import pymysql
import urllib3
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.mysql.features import DatabaseFeatures
from django.utils.encoding import force_bytes

from apigateway.common.env import Env
from apigateway.conf.celery_conf import *  # noqa
from apigateway.conf.celery_conf import CELERY_BEAT_SCHEDULE
from apigateway.conf.log_utils import build_logging_config
from apigateway.conf.utils import PatchFeatures, get_default_keepalive_options

pymysql.install_as_MySQLdb()
# Patch version info to force pass Django client check
pymysql.version_info = 1, 4, 6, "final", 0

# 目前 Django 仅是对 5.7 做了软性的不兼容改动，在没有使用 8.0 特异的功能时，对 5.7 版本的使用无影响
DatabaseFeatures.minimum_database_version = PatchFeatures.minimum_database_version

# Patch the SSL module for compatibility with legacy CA credentials.
# https://stackoverflow.com/questions/72479812/how-to-change-tweak-python-3-10-default-ssl-settings-for-requests-sslv3-alert
urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"

env = Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
BK_APP_CODE = env.str("BK_APP_CODE", "bk_apigateway")
BK_APP_SECRET = env.str("BK_APP_SECRET")
SECRET_KEY = env.str("SECRET_KEY", BK_APP_SECRET)

DEFAULT_TEST_APP = {
    "bk_app_code": env.str("DEFAULT_TEST_APP_CODE", BK_APP_CODE),
    "bk_app_secret": env.str("DEFAULT_TEST_APP_SECRET", BK_APP_SECRET),
}

# ==============================================================================
# django basic
# ==============================================================================
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)
# 是否为本地开发环境
IS_LOCAL = env.bool("DASHBOARD_IS_LOCAL", default=False)

# te 还是 ee
EDITION = env.str("EDITION", "ee")

# 是否开启多租户模式
ENABLE_MULTI_TENANT_MODE = env.bool("ENABLE_MULTI_TENANT_MODE", default=False)

# for apigw-manager sdk and other blueking sdks
BK_APP_TENANT_ID = ""
if ENABLE_MULTI_TENANT_MODE:
    BK_APP_TENANT_ID = "system"

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "raven.contrib.django.raven_compat",
    "djangoql",
    "django_celery_beat",
    "rest_framework",
    "drf_yasg",
    "corsheaders",
    "apigateway.apigateway",
    "apigateway.apps.monitor",
    "apigateway.schema",
    "apigateway.core",
    "apigateway.apps.gateway",
    "apigateway.apps.plugin",
    "apigateway.apps.label",
    "apigateway.apps.permission",
    "apigateway.apps.audit",
    "apigateway.apps.metrics",
    "apigateway.apps.support",
    "apigateway.apps.openapi",
    "apigateway.apps.programmable_gateway",
    "django_prometheus",
    "bkpaas_auth",
    "apigateway.account",
    "apigateway.apps.feature",
    "apigateway.apps.docs",
    "apigateway.apps.api_debug",
    "apigateway.apps.mcp_server",
    "apigw_manager.apigw",
    "apigateway.controller",
    "apigateway.healthz",
    # 蓝鲸通知中心
    "bk_notice_sdk",
]

# 非多租户模式才会有 esb 相关的模型
if not ENABLE_MULTI_TENANT_MODE:
    INSTALLED_APPS += [
        "apigateway.apps.esb",
        "apigateway.apps.esb.bkcore",
    ]

MIDDLEWARE = [
    # 这个必须在最前
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "apigateway.common.middlewares.request_id.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 蓝鲸静态资源服务
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "bkpaas_auth.middlewares.CookieLoginMiddleware",
    "apigw_manager.apigw.authentication.ApiGatewayJWTGenericMiddleware",
    "apigateway.account.middlewares.ApiGatewayJWTAppMiddleware",
    "apigateway.account.middlewares.ApiGatewayJWTUserMiddleware",
    "apigateway.account.middlewares.SelfAppCodeAppSecretLoginMiddleware",
    # 这个必须在最后
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "apigateway.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"

DATABASE_ROUTERS = [
    "apigateway.utils.db_router.DBRouter",
]

# django 3.2 add
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# CSRF Config
CSRF_TRUSTED_ORIGINS = env.list("DASHBOARD_CSRF_TRUSTED_ORIGINS", default=[])
CSRF_COOKIE_DOMAIN = env.str("DASHBOARD_CSRF_COOKIE_DOMAIN")
CSRF_COOKIE_NAME = env.str("DASHBOARD_CSRF_COOKIE_NAME", f"{BK_APP_CODE}_csrftoken")

# Session Config
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_COOKIE_NAME = env.str("DASHBOARD_SESSION_COOKIE_NAME", f"{BK_APP_CODE}_sessionid")
SESSION_COOKIE_DOMAIN = CSRF_COOKIE_DOMAIN or env.str("DASHBOARD_SESSION_COOKIE_DOMAIN")

# CORS Config
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_REGEX_WHITELIST: List[str] = env.list("CORS_ORIGIN_REGEX_WHITELIST", default=[])

# Internationalization
LANGUAGE_CODE = "zh-hans"
USE_I18N = True
USE_L10N = True

# timezone
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGES = (
    ("en", "English"),
    ("zh-cn", "简体中文"),
    ("zh-hans", "简体中文"),
)

LANGUAGE_COOKIE_PATH = "/"
# 国际化 cookie 信息必须跟整个蓝鲸体系保存一致
LANGUAGE_COOKIE_NAME = "blueking_language"
# 国际化 cookie 默认写在整个蓝鲸的根域下
LANGUAGE_COOKIE_DOMAIN = env.str("DASHBOARD_LANGUAGE_COOKIE_DOMAIN", None) or CSRF_COOKIE_DOMAIN

# 站点 URL
SITE_URL = "/"

# Static files (CSS, JavaScript, Images)
STATIC_VERSION = "1.0"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# static root and dirs to find static
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/backend/static/"

# About whitenoise
WHITENOISE_STATIC_PREFIX = "/backend/static/"

AUTHENTICATION_BACKENDS = [
    "bkpaas_auth.backends.DjangoAuthUserCompatibleBackend",
]

AUTH_USER_MODEL = "account.AuthUser"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apigateway.common.exception_handler.custom_exception_handler",
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "apigateway.common.permissions.GatewayPermission",
    ),
    "DEFAULT_PAGINATION_CLASS": "apigateway.common.pagination.StandardLimitOffsetPagination",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.SessionAuthentication",),
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S %z",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

SWAGGER_SETTINGS = {
    "DEFAULT_AUTO_SCHEMA_CLASS": "apigateway.common.swagger.BkStandardResponseSwaggerAutoSchema",
}

# https://docs.djangoproject.com/en/3.2/ref/checks/
# disable warnings: db_table '<table_name>' is used by multiple models
SILENCED_SYSTEM_CHECKS = ["models.W035"]

# Database
DATABASES = {
    "default": {
        "ENGINE": env.str("BK_APIGW_DATABASE_ENGINE", "django.db.backends.mysql"),
        "NAME": env.str("BK_APIGW_DATABASE_NAME", BK_APP_CODE),
        "USER": env.str("BK_APIGW_DATABASE_USER", BK_APP_CODE),
        "PASSWORD": env.str("BK_APIGW_DATABASE_PASSWORD", ""),
        "HOST": env.str("BK_APIGW_DATABASE_HOST", "localhost"),
        "PORT": env.int("BK_APIGW_DATABASE_PORT", 3306),
        "OPTIONS": {
            "isolation_level": env.str("BK_APIGW_DATABASE_ISOLATION_LEVEL", "READ COMMITTED"),
        },
    },
}

# 非多租户模式才会有 esb 相关的模型
if not ENABLE_MULTI_TENANT_MODE:
    DATABASES["bkcore"] = {
        "ENGINE": env.str("BK_ESB_DATABASE_ENGINE", "django.db.backends.mysql"),
        "NAME": env.str("BK_ESB_DATABASE_NAME", "bk_esb"),
        "USER": env.str("BK_ESB_DATABASE_USER", BK_APP_CODE),
        "PASSWORD": env.str("BK_ESB_DATABASE_PASSWORD", ""),
        "HOST": env.str("BK_ESB_DATABASE_HOST", "localhost"),
        "PORT": env.int("BK_ESB_DATABASE_PORT", 3306),
        "OPTIONS": {
            "isolation_level": env.str("BK_ESB_DATABASE_ISOLATION_LEVEL", "READ COMMITTED"),
        },
    }

# database ssl
BK_APIGW_DATABASE_TLS_ENABLED = env.bool("BK_APIGW_DATABASE_TLS_ENABLED", False)
if BK_APIGW_DATABASE_TLS_ENABLED:
    default_ssl_options = {
        "ca": env.str("BK_APIGW_DATABASE_TLS_CERT_CA_FILE", ""),
    }
    # mTLS
    default_cert_file = env.str("BK_APIGW_DATABASE_TLS_CERT_FILE", "")
    default_key_file = env.str("BK_APIGW_DATABASE_TLS_CERT_KEY_FILE", "")
    if default_cert_file and default_key_file:
        default_ssl_options["cert"] = default_cert_file
        default_ssl_options["key"] = default_key_file

    # 跳过主机名/IP 验证，会降低安全性，正式环境需要设置为 True
    check_hostname = env.bool("BK_APIGW_DATABASE_TLS_CHECK_HOSTNAME", True)
    default_ssl_options["check_hostname"] = check_hostname

    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}

    DATABASES["default"]["OPTIONS"]["ssl"] = default_ssl_options

BK_ESB_DATABASE_TLS_ENABLED = env.bool("BK_ESB_DATABASE_TLS_ENABLED", False)
if BK_ESB_DATABASE_TLS_ENABLED:
    bkcore_ssl_options = {
        "ca": env.str("BK_ESB_DATABASE_TLS_CERT_CA_FILE", ""),
    }
    # mTLS
    bkcore_cert_file = env.str("BK_ESB_DATABASE_TLS_CERT_FILE", "")
    bkcore_key_file = env.str("BK_ESB_DATABASE_TLS_CERT_KEY_FILE", "")
    if bkcore_cert_file and bkcore_key_file:
        bkcore_ssl_options["cert"] = bkcore_cert_file
        bkcore_ssl_options["key"] = bkcore_key_file

    # 跳过主机名/IP 验证，会降低安全性，正式环境需要设置为 True
    check_hostname = env.bool("BK_ESB_DATABASE_TLS_CHECK_HOSTNAME", True)
    bkcore_ssl_options["check_hostname"] = check_hostname

    if "OPTIONS" not in DATABASES["bkcore"]:
        DATABASES["bkcore"]["OPTIONS"] = {}

    DATABASES["bkcore"]["OPTIONS"]["ssl"] = bkcore_ssl_options

# database ssl
BK_APIGW_DATABASE_TLS_ENABLED = env.bool("BK_APIGW_DATABASE_TLS_ENABLED", False)
if BK_APIGW_DATABASE_TLS_ENABLED:
    default_ssl_options = {
        "ca": env.str("BK_APIGW_DATABASE_TLS_CERT_CA_FILE", ""),
    }
    # mTLS
    default_cert_file = env.str("BK_APIGW_DATABASE_TLS_CERT_FILE", "")
    default_key_file = env.str("BK_APIGW_DATABASE_TLS_CERT_KEY_FILE", "")
    if default_cert_file and default_key_file:
        default_ssl_options["cert"] = default_cert_file
        default_ssl_options["key"] = default_key_file

    # 跳过主机名/IP 验证，会降低安全性，正式环境需要设置为 True
    check_hostname = env.bool("BK_APIGW_DATABASE_TLS_CHECK_HOSTNAME", True)
    default_ssl_options["check_hostname"] = check_hostname

    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}

    DATABASES["default"]["OPTIONS"]["ssl"] = default_ssl_options

BK_ESB_DATABASE_TLS_ENABLED = env.bool("BK_ESB_DATABASE_TLS_ENABLED", False)
if BK_ESB_DATABASE_TLS_ENABLED:
    bkcore_ssl_options = {
        "ca": env.str("BK_ESB_DATABASE_TLS_CERT_CA_FILE", ""),
    }
    # mTLS
    bkcore_cert_file = env.str("BK_ESB_DATABASE_TLS_CERT_FILE", "")
    bkcore_key_file = env.str("BK_ESB_DATABASE_TLS_CERT_KEY_FILE", "")
    if bkcore_cert_file and bkcore_key_file:
        bkcore_ssl_options["cert"] = bkcore_cert_file
        bkcore_ssl_options["key"] = bkcore_key_file

    # 跳过主机名/IP 验证，会降低安全性，正式环境需要设置为 True
    check_hostname = env.bool("BK_ESB_DATABASE_TLS_CHECK_HOSTNAME", True)
    bkcore_ssl_options["check_hostname"] = check_hostname

    if "OPTIONS" not in DATABASES["bkcore"]:
        DATABASES["bkcore"]["OPTIONS"] = {}

    DATABASES["bkcore"]["OPTIONS"]["ssl"] = bkcore_ssl_options

# ==============================================================================
# redis 配置
# ==============================================================================
REDIS_HOST = env.str("BK_APIGW_REDIS_HOST", "localhost")
REDIS_PORT = env.int("BK_APIGW_REDIS_PORT", 6379)
REDIS_PASSWORD = env.str("BK_APIGW_REDIS_PASSWORD", "")
REDIS_PREFIX = env.str("BK_APIGW_REDIS_PREFIX", "apigw::")
REDIS_MAX_CONNECTIONS = env.int("BK_APIGW_REDIS_MAX_CONNECTIONS", 100)
REDIS_DB = env.int("BK_APIGW_REDIS_DB", 0)
# redis tls
REDIS_TLS_ENABLED = env.bool("BK_APIGW_REDIS_TLS_ENABLED", False)
REDIS_TLS_CERT_CA_FILE = env.str("BK_APIGW_REDIS_TLS_CERT_CA_FILE", "")
REDIS_TLS_CERT_FILE = env.str("BK_APIGW_REDIS_TLS_CERT_FILE", "")
REDIS_TLS_CERT_KEY_FILE = env.str("BK_APIGW_REDIS_TLS_CERT_KEY_FILE", "")
REDIS_TLS_CHECK_HOSTNAME = env.bool("BK_APIGW_REDIS_TLS_CHECK_HOSTNAME", True)

# redis lock 配置
REDIS_PUBLISH_LOCK_TIMEOUT = env.int("BK_APIGW_PUBLISH_LOCK_TIMEOUT", 5)
REDIS_PUBLISH_LOCK_RETRY_GET_TIMES = env.int("BK_APIGW_PUBLISH_LOCK_RETRY_GET_TIMES", 3)

DEFAULT_REDIS_CONFIG = CHANNEL_REDIS_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "password": REDIS_PASSWORD,
    "max_connections": REDIS_MAX_CONNECTIONS,
    "db": REDIS_DB,
    "tls_enabled": REDIS_TLS_ENABLED,
    "tls_cert_ca_file": REDIS_TLS_CERT_CA_FILE,
    "tls_cert_file": REDIS_TLS_CERT_FILE,
    "tls_cert_key_file": REDIS_TLS_CERT_KEY_FILE,
    "tls_check_hostname": REDIS_TLS_CHECK_HOSTNAME,
}

# ==============================================================================
# etcd 配置
# ==============================================================================
ETCD_CONFIG = {
    "host": env.str("BK_ETCD_HOST", default="localhost"),
    "port": env.int("BK_ETCD_PORT", default=2379),
    "user": env.str("BK_ETCD_USER", default=None),
    "password": env.str("BK_ETCD_PASSWORD", default=None),
    "ca_cert": env.str("BK_ETCD_CA_PATH", default=None),
    "cert_cert": env.str("BK_ETCD_CERT_PATH", default=None),
    "cert_key": env.str("BK_ETCD_KEY_PATH", default=None),
}

# ==============================================================================
# celery 配置
# ==============================================================================
# 开启 CeleryWorker 发送任务事件
CELERY_WORKER_SEND_TASK_EVENTS = True
# 开启任务发送 sent 事件
CELERY_TASK_SEND_SENT_EVENT = True

REDIS_CONNECTION_OPTIONS = {
    "socket_timeout": 3,
    "socket_connect_timeout": 3,
    "socket_keepalive": True,
    "socket_keepalive_options": get_default_keepalive_options(),
}
RABBITMQ_VHOST = env.str("BK_APIGW_RABBITMQ_VHOST", "")
RABBITMQ_PORT = env.str("BK_APIGW_RABBITMQ_PORT", "")
RABBITMQ_HOST = env.str("BK_APIGW_RABBITMQ_HOST", "")
RABBITMQ_USER = env.str("BK_APIGW_RABBITMQ_USER", "")
RABBITMQ_PASSWORD = env.str("BK_APIGW_RABBITMQ_PASSWORD", "")
if all([RABBITMQ_VHOST, RABBITMQ_PORT, RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASSWORD]):
    # this section not support tls, both rabbitmq and redis
    CELERY_BROKER_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"
    CELERY_RESULT_BACKEND = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    # 如果没有使用 Redis 作为 Broker，请不要启用该配置，详见：
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#broker-transport-options
    CELERY_BROKER_TRANSPORT_OPTIONS = REDIS_CONNECTION_OPTIONS
    CELERY_BROKER_URL = f"redis://:{quote(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_RESULT_BACKEND = f"redis://:{quote(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    CELERY_TASK_DEFAULT_QUEUE = env.str(
        "BK_APIGW_CELERY_TASK_DEFAULT_QUEUE", f"{REDIS_PREFIX}bk_apigateway_dashboard_celery"
    )
    # support tls
    if REDIS_TLS_ENABLED:
        query_string_params = {
            "ssl_cert_reqs": "CERT_REQUIRED",
            "ssl_ca_certs": REDIS_TLS_CERT_CA_FILE,
        }
        if REDIS_TLS_CERT_KEY_FILE and REDIS_TLS_CERT_FILE:
            query_string_params["ssl_keyfile"] = REDIS_TLS_CERT_KEY_FILE
            query_string_params["ssl_certfile"] = REDIS_TLS_CERT_FILE

        import urllib.parse

        broker_url = f"rediss://:{quote(REDIS_PASSWORD)}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}?{urllib.parse.urlencode(query_string_params)}"
        CELERY_BROKER_URL = broker_url
        CELERY_RESULT_BACKEND = broker_url

if env.bool("FEATURE_FLAG_ENABLE_RUN_DATA_METRICS", True):
    CELERY_BEAT_SCHEDULE.update(
        {
            "apigateway.apps.metrics.tasks.statistics_request_by_day": {
                "task": "apigateway.apps.metrics.tasks.statistics_request_by_day",
                "schedule": crontab(minute=30, hour=8),  # noqa: F405
            },
            "apigateway.apps.permission.tasks.renew_app_resource_permission": {
                "task": "apigateway.apps.permission.tasks.renew_app_resource_permission",
                "schedule": crontab(minute=50, hour=10),
            },
        }
    )

# 清理任务相关配置
CLEAN_TABLE_INTERVAL_DAYS = env.int("CLEAN_TABLE_INTERVAL_DAYS", 365)

# ==============================================================================
# log 配置
# ==============================================================================
LOG_LEVEL = env.str("LOG_LEVEL", "WARNING")
# 用于存放日志文件的目录，默认值为空，表示不使用任何文件，所有日志直接输出到控制台。
# 可配置为有效目录，支持相对或绝对地址，比如："logs" 或 "/var/lib/app_logs/"。
# 配置本选项后，原有的控制台日志输出将关闭。
LOG_DIR = env.str("BK_APIGW_LOG_PATH", default=None)
# 日志文件格式，可选值为：json/text
LOGGING_FILE_FORMAT = env.str("LOGGING_FILE_FORMAT", default="json")

if LOG_DIR is None:
    logging_to_console = True
    logging_directory = None
else:
    logging_to_console = False
    # The dir allows both absolute and relative path, when it's relative, combine
    # the value with project's base directory
    logging_directory = Path(BASE_DIR) / Path(LOG_DIR)
    logging_directory.mkdir(exist_ok=True)

# 是否总是打印日志到控制台，默认关闭
LOGGING_ALWAYS_CONSOLE = env.bool("LOGGING_ALWAYS_CONSOLE", False)
if LOGGING_ALWAYS_CONSOLE:
    logging_to_console = True

LOGGING = build_logging_config(LOG_LEVEL, logging_to_console, logging_directory, LOGGING_FILE_FORMAT)

# sentry 配置
RAVEN_CONFIG = {
    "dsn": env.str("BK_APIGW_SENTRY_DSN", ""),
}

# ==============================================================================
# crypto
# ==============================================================================
# legacy apigateway custom crypto
CRYPTO_TYPE_APIGW_CUSTOM = "APIGW_CUSTOM"

ENCRYPT_KEY = env.str("ENCRYPT_KEY")
JWT_CRYPTO_KEY = ENCRYPT_KEY
LOG_LINK_SECRET = ENCRYPT_KEY

# bk crypto, support 'SHANGMI' , 'CLASSIC'
BK_CRYPTO_TYPE = env.str("BK_CRYPTO_TYPE", CRYPTO_TYPE_APIGW_CUSTOM)
if BK_CRYPTO_TYPE not in ("SHANGMI", "CLASSIC", CRYPTO_TYPE_APIGW_CUSTOM):
    raise ImproperlyConfigured(
        f"Set BK_CRYPTO_TYPE environment variable, should be one of 'SHANGMI' , 'CLASSIC', current is {BK_CRYPTO_TYPE}"
    )
ENCRYPT_CIPHER_TYPE = "SM4CTR" if BK_CRYPTO_TYPE == "SHANGMI" else "FernetCipher"
BKKRILL_ENCRYPT_SECRET_KEY = force_bytes(env.str("BKKRILL_ENCRYPT_SECRET_KEY", ""))
if BK_CRYPTO_TYPE != CRYPTO_TYPE_APIGW_CUSTOM and BKKRILL_ENCRYPT_SECRET_KEY == "":
    raise ImproperlyConfigured(
        f"the BK_CRYPTO_TYPE is {BK_CRYPTO_TYPE}, so the BKKRILL_ENCRYPT_SECRET_KEY can not be empty"
    )

# use the same nonce, should not be changed at all!!!!!!
CRYPTO_NONCE = env.str("BK_APIGW_CRYPTO_NONCE", "q76rE8srRuYM")

# ==============================================================================
# 模板变量
# ==============================================================================
BK_API_URL_TMPL = env.str("BK_API_URL_TMPL", "").rstrip("/")
BK_API_INNER_URL_TMPL = env.str("BK_API_INNER_URL_TMPL", "") or BK_API_URL_TMPL
API_RESOURCE_URL_TMPL = env.str("API_RESOURCE_URL_TMPL", "")
API_DOCS_URL_TMPL = env.str("API_DOCS_URL_TMPL", "")
RESOURCE_DOC_URL_TMPL = env.str("RESOURCE_DOC_URL_TMPL", "")
COMPONENT_DOC_URL_TMPL = env.str("COMPONENT_DOC_URL_TMPL", "")

BK_COMPONENT_API_URL = env.str("BK_COMPONENT_API_URL", "")
BK_COMPONENT_API_INNER_URL = env.str("BK_COMPONENT_API_INNER_URL", "") or BK_COMPONENT_API_URL
BK_PAAS3_API_URL = BK_API_INNER_URL_TMPL.format(api_name="bkpaas3")
BK_PAAS3_API_TIMEOUT = env.int("BK_PAAS3_API_TIMEOUT", 30)
BK_APIGATEWAY_API_URL = env.str("BK_APIGATEWAY_API_URL", "")

BK_AUTH_API_URL = env.str("BK_AUTH_API_URL", "")

# ==============================================================================
# AI Open API 配置
# ==============================================================================
AI_OPEN_API_BASE_URL = env.str("AI_OPEN_API_BASE_URL", "")
AI_MODEL = env.str("AI_MODEL", "")
AI_API_KEY = env.str("AI_API_KEY", "")
AI_APP_CODE = env.str("AI_APP_CODE", BK_APP_CODE)
AI_APP_SECRET = env.str("AI_APP_SECRET", BK_APP_SECRET)
AI_BKAUTH_ENABLED = env.bool("AI_BKAUTH_ENABLED", False)

# ==============================================================================
# 网关全局配置
# ==============================================================================
DASHBOARD_URL = env.str("DASHBOARD_URL", "").rstrip("/")

DASHBOARD_FE_URL = env.str("DASHBOARD_FE_URL", "").rstrip("/")
# 将前端 URL 默认添加到 CORS 白名单，可不配置环境变量 CORS_ORIGIN_REGEX_WHITELIST
if DASHBOARD_FE_URL and DASHBOARD_FE_URL not in CORS_ORIGIN_REGEX_WHITELIST:
    CORS_ORIGIN_REGEX_WHITELIST.append(DASHBOARD_FE_URL)
GATEWAY_DEFAULT_CREATOR = env.str("GATEWAY_DEFAULT_CREATOR", "admin")
DEFAULT_USER_AUTH_TYPE = "default"

APIGW_MANAGERS = env.list("APIGW_MANAGERS", default=["admin"])

# 网关 jwt 签发者，必须与 apigateway 后端服务保持一致，
# apigw-manager sdk 利用 issuer 支持获取不同网关实例同名网关的公钥，以支持同一后端服务接入不同网关实例
JWT_ISSUER = env.str("BK_APIGW_JWT_ISSUER", "APIGW")

# 检查保留的官方网关名
CHECK_RESERVED_GATEWAY_NAME = True
# 保留的网关名前缀，检查保留网关名时，不允许在管理端创建此前缀的网关
RESERVED_GATEWAY_NAME_PREFIXES = ["bk-", "bp-"]
# 官方网关命名前缀，仅做标记
OFFICIAL_GATEWAY_NAME_PREFIXES = ["bk-"]
# 网关名校验白名单
IGNORE_GATEWAY_NAME_CHECK_WHITELIST = env.list("IGNORE_GATEWAY_NAME_CHECK_WHITELIST", default=["bkpaas3", "paasv3"])

# 允许管理端更新网关认证信息
DEFAULT_ALLOW_UPDATE_API_AUTH = True

# 网关用户认证配置
API_USER_AUTH_CONFIGS = {
    "default": {
        "user_type": "default",
        "from_bk_token": True,
        "from_username": True,
    }
}

# 特殊的网关认证配置，在网关同步时，会更新网关的这些配置
SPECIAL_GATEWAY_AUTH_CONFIGS = {
    "bk-auth": {
        "unfiltered_sensitive_keys": ["bk_token", "access_token"],
    },
}

BK_LOGIN_TICKET_KEY = "bk_token"
BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME = {
    "bk_token": "bk_token",
}

BK_API_DEFAULT_STAGE_MAPPINGS = env.dict("BK_API_DEFAULT_STAGE_MAPPINGS", default={})

FAKE_SEND_NOTICE = env.bool("FAKE_SEND_NOTICE", default=False)

# for some legacy gateways, they support both `;` nad `&` as separator of query string
# so we do a special process for them
LEGACY_INVALID_PARAMS_GATEWAY_NAMES = env.list("LEGACY_INVALID_PARAMS_GATEWAY_NAMES", default=[])

# 使用网关 bk-esb 管理组件 API 的权限
USE_GATEWAY_BK_ESB_MANAGE_COMPONENT_PERMISSIONS = env.bool("USE_GATEWAY_BK_ESB_MANAGE_COMPONENT_PERMISSIONS", True)

# paas 开发者中心权限续期地址
BK_PAAS3_URL = env.str("BK_PAAS3_URL", "")
PAAS_RENEW_API_PERMISSION_URL = f"{BK_PAAS3_URL}/developer-center/apps/{{bk_app_code}}/cloudapi"

# Requests pool config
REQUESTS_POOL_CONNECTIONS = env.int("REQUESTS_POOL_CONNECTIONS", default=20)
REQUESTS_POOL_MAXSIZE = env.int("REQUESTS_POOL_MAXSIZE", default=20)


# ==============================================================================
# API 使用指南文档地址
# ==============================================================================
# 可编程网关开发文档链接地址
PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_PYTHON_URL = env.str(
    "PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_PYTHON_URL",
    "https://github.com/TencentBlueKing/bk-apigateway-framework/blob/master/docs/python.md",
)
PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_GO_URL = env.str(
    "PROGRAMMABLE_GATEWAY_DEV_GUIDELINE_GO_URL",
    "https://github.com/TencentBlueKing/bk-apigateway-framework/blob/master/docs/golang.md",
)

# access token 文档链接地址
BK_ACCESS_TOKEN_DOC_URL = env.str(
    "BK_ACCESS_TOKEN_DOC_URL",
    "https://bk.tencent.com/docs/markdown/ZH/APIGateway/1.14/UserGuide/Explanation/access-token.md",
)

DOCS_URLS = {
    "USE_GATEWAY_API": "https://bk.tencent.com/docs/markdown/ZH/APIGateway/1.14/UserGuide/HowTo/call-gateway-api.md",
    "ACCESS_TOKEN_API": BK_ACCESS_TOKEN_DOC_URL,
}

# ==============================================================================
# bkpaas-auth 配置
# ==============================================================================

BKAUTH_TOKEN_APP_CODE = BK_APP_CODE
BKAUTH_TOKEN_SECRET_KEY = BK_APP_SECRET

# 用户登录态认证类型，默认为 bk_token，te 版本会被 te_default.py 中的值覆盖
BKAUTH_BACKEND_TYPE = "bk_token"

# 启用多租户模式
BKAUTH_ENABLE_MULTI_TENANT_MODE = ENABLE_MULTI_TENANT_MODE

# 验证用户信息的网关 API(租户版本) => 走网关，不走 esb
# FIXME: remove `and ENABLE_MULTI_TENANT_MODE` when all env has the newest bk-login
if EDITION == "ee" and ENABLE_MULTI_TENANT_MODE:
    BKAUTH_USER_INFO_APIGW_URL = (
        BK_API_URL_TMPL.format(api_name="bk-login") + "/prod/login/api/v3/open/bk-tokens/userinfo/"
    )
else:
    # 只在 te 生效，并且会被 te_default.py 中的值覆盖
    BKAUTH_USER_COOKIE_VERIFY_URL = f"{BK_COMPONENT_API_INNER_URL}/api/c/compapi/v2/bk_login/is_login/"
    BKAUTH_TOKEN_USER_INFO_ENDPOINT = f"{BK_COMPONENT_API_INNER_URL}/api/c/compapi/v2/bk_login/get_user/"

# ==============================================================================
# login 配置
# ==============================================================================
BK_LOGIN_URL = env.str("BK_LOGIN_URL", default="/")
# 登录小窗相关
BK_LOGIN_PLAIN_URL = env.str("BK_LOGIN_PLAIN_URL", default=BK_LOGIN_URL.rstrip("/") + "/plain/")
BK_LOGIN_PLAIN_WINDOW_WIDTH = env.int("BK_LOGIN_PLAIN_WINDOW_WIDTH", default=700)
BK_LOGIN_PLAIN_WINDOW_HEIGHT = env.int("BK_LOGIN_PLAIN_WINDOW_HEIGHT", default=550)

# ==============================================================================
# bkrepo 配置
# ==============================================================================
BKREPO_ENDPOINT_URL = env.str("BKREPO_ENDPOINT_URL", "")
BKREPO_USERNAME = env.str("BKREPO_USERNAME", "bk_apigateway")
BKREPO_PASSWORD = env.str("BKREPO_PASSWORD", "")
BKREPO_PROJECT = env.str("BKREPO_PROJECT", "bk_apigateway")
BKREPO_GENERIC_BUCKET = env.str("BKREPO_GENERIC_BUCKET", "generic")

# pypi 镜像源配置
PYPI_MIRRORS_CONFIG = {
    "default": {
        "repository_url": env.str("DEFAULT_PYPI_REPOSITORY_URL", ""),
        "index_url": env.str("DEFAULT_PYPI_INDEX_URL", ""),
        "username": env.str("DEFAULT_PYPI_USERNAME", ""),
        "password": env.str("DEFAULT_PYPI_PASSWORD", ""),
    }
}

PYPI_MIRRORS_REPOSITORY = env.str("PYPI_INDEX_URL", "https://pypi.org/simple/")

# maven 仓库配置
MAVEN_MIRRORS_CONFIG = {
    "default": {
        "repository_url": env.str("DEFAULT_MAVEN_REPOSITORY_URL", ""),
        "repository_id": env.str("DEFAULT_MAVEN_REPOSITORY_ID", "bkpaas-maven"),
        "username": env.str("DEFAULT_MAVEN_USERNAME", "bk_apigateway"),
        "password": env.str("DEFAULT_MAVEN_PASSWORD", "bk_apigateway"),
    }
}

# ==============================================================================
# 蓝鲸通知中心配置
# ==============================================================================
ENABLE_BK_NOTICE = env.bool("ENABLE_BK_NOTICE", False)

# 对接通知中心的环境，默认为生产环境
BK_NOTICE_ENV = BK_API_DEFAULT_STAGE_MAPPINGS.get("bk-notice", "prod")
BK_NOTICE = {
    "STAGE": BK_NOTICE_ENV,
    "LANGUAGE_COOKIE_NAME": LANGUAGE_COOKIE_NAME,
    "DEFAULT_LANGUAGE": "en",
    "PLATFORM": BK_APP_CODE,  # 平台注册的 code，用于获取系统通知消息时进行过滤
    "BK_API_URL_TMPL": BK_API_URL_TMPL,
    "BK_API_APP_CODE": BK_APP_CODE,  # 用于调用 apigw 认证
    "BK_API_SECRET_KEY": BK_APP_SECRET,  # 用于调用 apigw 认证
}

# ==============================================================================
# 版本日志
# ==============================================================================
VERSION_LOG_DIR = os.path.join(BASE_DIR, "data/version_log")

# ==============================================================================
# 网关响应错误码说明文档
# ==============================================================================
API_RESPONSE_ERR_CODE_DOC_DIR = os.path.join(BASE_DIR, "data/knowledge_doc/api_response")

# ==============================================================================
# 访问日志
# ==============================================================================
ACCESS_LOG_CONFIG = {
    "es_time_field_name": env.str("BK_APIGW_ES_TIME_FIELD_NAME", "dtEventTimeStamp"),
    "es_index": env.str("BK_APIGW_API_LOG_ES_INDEX", "2_bklog_bkapigateway_apigateway_container*"),
}

BK_ESB_ACCESS_LOG_CONFIG = {
    "es_time_field_name": env.str("BK_ESB_ES_TIME_FIELD_NAME", "dtEventTimeStamp"),
    "es_index": env.str("BK_ESB_API_LOG_ES_INDEX", "2_bklog_bkapigateway_esb_container*"),
}


# ==============================================================================
# prometheus 配置
# ==============================================================================
PROMETHEUS_METRIC_NAME_PREFIX = env.str("PROMETHEUS_METRIC_NAME_PREFIX", "bk_apigateway_")
PROMETHEUS_DEFAULT_LABELS = [
    # example: foo=bar => [("foo", "=", "bar")]
    (key, "=", value)
    for key, value in env.dict("PROMETHEUS_DEFAULT_LABELS", default={}).items()
]

# ==============================================================================
# OTEL
# ==============================================================================
# tracing: otel 相关配置
ENABLE_OTEL_TRACE = env.bool("BK_APIGW_ENABLE_OTEL_TRACE", default=False)

OTEL_TYPE = env.str("BK_APIGW_OTEL_TYPE", default="grpc")
OTEL_GRPC_HOST = env.str("BK_APIGW_OTEL_GRPC_HOST", default="")
OTEL_HTTP_URL = env.str("BK_APIGW_OTEL_HTTP_URL", default="")
OTEL_HTTP_TIMEOUT = env.str("BK_APIGW_OTEL_HTTP_TIMEOUT", default=1)
OTEL_DATA_TOKEN = env.str("BK_APIGW_OTEL_DATA_TOKEN", default="")
OTEL_SAMPLER = env.str("DASHBOARD_OTEL_SAMPLER", default="always_on")
OTEL_SERVICE_NAME = env.str("DASHBOARD_OTEL_SERVICE_NAME", default="bk-apigateway-dashboard")
# instrument
OTEL_INSTRUMENT_DB_API = env.bool("DASHBOARD_OTEL_INSTRUMENT_DB_API", default=False)
OTEL_INSTRUMENT_CELERY = env.bool("DASHBOARD_OTEL_INSTRUMENT_CELERY", default=False)
OTEL_INSTRUMENT_REDIS = env.bool("DASHBOARD_OTEL_INSTRUMENT_REDIS", default=False)

# 网关部署集群所属业务 ID，影响从蓝鲸监控拉取 Prometheus 数据等功能；开源环境默认部署在蓝鲸业务 (业务 ID=2)
BCS_CLUSTER_BK_BIZ_ID = env.str("BCS_CLUSTER_BK_BIZ_ID", "2")

# 托管的微网关实例，实例部署所用 chart 由网关生成，
# 此 chart 中，endpoints + base_path 应为微网关实例访问网关数据的网关接口地址前缀
EDGE_CONTROLLER_API_BASE_PATH = env.str("EDGE_CONTROLLER_API_BASE_PATH", "/")

# 默认微网关共享实例
DEFAULT_MICRO_GATEWAY_ID = env.str("DEFAULT_MICRO_GATEWAY_ID", default="faf44a48-59e9-f790-2412-e56c90551fb3")

# ==============================================================================
# apisix
# ==============================================================================
PLUGIN_METADATA_CONFIG = {
    "file-logger": {
        "log_format": {
            # 请求信息
            "proto": "$server_protocol",
            "method": "$request_method",
            "http_host": "$host",
            "http_path": "$uri",
            "headers": "-",
            "params": "$args",
            "body": "$bk_log_request_body",
            "app_code": "$bk_app_code",
            "client_ip": "$remote_addr",
            "request_id": "$bk_request_id",
            "x_request_id": "$x_request_id",
            "request_duration": "$bk_log_request_duration",
            "bk_username": "$bk_username",
            "bk_tenant_id": "$bk_tenant_id",
            # 网关信息
            "api_id": "$bk_gateway_id",
            "api_name": "$bk_gateway_name",
            "resource_id": "$bk_resource_id",
            "resource_name": "$bk_resource_name",
            "stage": "$bk_stage_name",
            # 后端服务
            "backend_scheme": "$upstream_scheme",
            "backend_method": "$method",
            # 后端服务 Host，即后端服务配置中的域名或 IP+Port
            "backend_host": "$bk_backend_host",
            # 后端服务地址，请求后端时，实际请求的 IP+Port，若后端服务配置中为域名，则为域名解析后的地址
            "backend_addr": "$upstream_addr",
            "backend_path": "$bk_log_backend_path",
            "backend_duration": "$bk_log_upstream_duration",
            # 响应
            "response_body": "$bk_log_response_body",
            "response_size": "$body_bytes_sent",
            "status": "$status",
            # 其它
            "msg": "-",
            "level": "info",
            "code_name": "$bk_apigw_error_code_name",
            "error": "$bk_apigw_error_message",
            "proxy_error": "$proxy_error",
            "instance": "$instance_id",
            "timestamp": "$bk_log_request_timestamp",
            # 临时字段，用于记录请求时，认证参数的位置，便于推动认证参数优化
            "auth_location": "$auth_params_location",
        }
    },
    "bk-concurrency-limit": {
        "conn": env.int("GATEWAY_CONCURRENCY_LIMIT_CONN", 2000),
        "burst": env.int("GATEWAY_CONCURRENCY_LIMIT_BURST", 1000),
        "default_conn_delay": env.int("GATEWAY_CONCURRENCY_LIMIT_DEFAULT_CONN_DELAY", 1),  # second
        "key_type": "var",
        "key": "bk_concurrency_limit_key",
        "allow_degradation": True,
    },
    "bk-real-ip": {
        "recursive": env.bool("GATEWAY_REAL_IP_RECURSIVE", False),
        "source": env.str("GATEWAY_REAL_IP_SOURCE", "http_x_forwarded_for"),
        "trusted_addresses": env.list("GATEWAY_REAL_IP_TRUSTED_ADDRESSES", default=["127.0.0.1", "::1"]),
    },
    "bk-opentelemetry": {
        "sampler": {
            # change to always_off/always_on/parent_base if needed!
            "name": env.str("GATEWAY_OTEL_SAMPLER_NAME", "always_off"),
            "options": {
                "root": {
                    "name": "trace_id_ratio",
                    "options": {"fraction": env.float("GATEWAY_OTEL_ROOT_SAMPLER_RATIO", default=0.01)},
                }
            },
        },
        "additional_attributes": [],
    },
}

# 是否启用网关并发限制，默认启用；
# 目前这个插件有缺陷，暂时支持关闭; https://github.com/apache/apisix/issues/11868
GATEWAY_CONCURRENCY_LIMIT_ENABLED = env.bool("GATEWAY_CONCURRENCY_LIMIT_ENABLED", False)

BK_GATEWAY_ETCD_NAMESPACE_PREFIX = env.str("BK_GATEWAY_ETCD_NAMESPACE_PREFIX", default="/bk-gateway-apigw")

# ==============================================================================
# Feature Flag
# ==============================================================================
# 全局功能开关，用于控制站点全局性的一些功能，将与 DEFAULT_USER_FEATURE_FLAG、Model UserFeatureFlag 中数据合并
# 优先级：Model UserFeatureFlag > DEFAULT_USER_FEATURE_FLAG > DEFAULT_FEATURE_FLAG
DEFAULT_FEATURE_FLAG = {
    # 是否展示"监控告警“子菜单
    "ENABLE_MONITOR": env.bool("FEATURE_FLAG_ENABLE_MONITOR", False),
    # 是否展示”运行数据“子菜单
    "ENABLE_RUN_DATA": env.bool("FEATURE_FLAG_ENABLE_RUN_DATA", True),
    # 是否展示 "运行数据" => 统计报表 子菜单
    "ENABLE_RUN_DATA_METRICS": env.bool("FEATURE_FLAG_ENABLE_RUN_DATA_METRICS", True),
    # 是否展示”组件管理“菜单项，企业版展示，上云版不展示
    "MENU_ITEM_ESB_API": env.bool("FEATURE_FLAG_MENU_ITEM_ESB_API", True),
    # 是否展示”组件 API 文档“菜单项
    "MENU_ITEM_ESB_API_DOC": env.bool("FEATURE_FLAG_MENU_ITEM_ESB_API_DOC", True),
    # 是否将 ESB 数据同步到网关。需要考虑这个是否还需要
    "SYNC_ESB_TO_APIGW_ENABLED": env.bool("FEATURE_FLAG_SYNC_ESB_TO_APIGW_ENABLED", True),
    # 网关编辑页，是否支持填写网关“绑定应用”
    "GATEWAY_APP_BINDING_ENABLED": env.bool("FEATURE_FLAG_GATEWAY_APP_BINDING_ENABLED", False),
    # FIXME: 为什么有两个 SDK 特性变量，并且容器化版本有 bkrepo 配置的话，默认应该都是 true?
    # 为 False，表示不启用 SDK 功能，网关 API 文档、组件 API 文档中，不展示 SDK 相关页面，隐藏“网关 APISDK”、“组件 APISDK”菜单项，隐藏网关中 SDK 创建、SDK 列表等功能项
    "ENABLE_SDK": env.bool("FEATURE_FLAG_ENABLE_SDK", False),
    # 隐藏 SDK 列表 相关功能
    "ALLOW_UPLOAD_SDK_TO_REPOSITORY": env.bool("FEATURE_FLAG_ALLOW_UPLOAD_SDK_TO_REPOSITORY", False),
    # 是否允许创建企业微信群，上云版一键拉群功能
    "ALLOW_CREATE_APPCHAT": env.bool("FEATURE_FLAG_ALLOW_CREATE_APPCHAT", False),
    # ----------------------------------------------------------------------------
    # 是否展示蓝鲸通知中心组件
    "ENABLE_BK_NOTICE": ENABLE_BK_NOTICE,
    # 是否开启多租户模式
    "ENABLE_MULTI_TENANT_MODE": ENABLE_MULTI_TENANT_MODE,
    # 是否开启网关AI相关功能
    "ENABLE_AI_COMPLETION": AI_OPEN_API_BASE_URL != "",
}

# 用户功能开关，将与 DEFAULT_FEATURE_FLAG 合并
DEFAULT_USER_FEATURE_FLAG = {
    # 2024-02-20 in 1.13 has no support for FEATURE_FLAG_MICRO_GATEWAY_ENABLED, comment it until it's supported
    # "MICRO_GATEWAY_ENABLED": env.bool("FEATURE_FLAG_MICRO_GATEWAY_ENABLED", False),
}

# 网关功能开关
GLOBAL_GATEWAY_FEATURE_FLAG = {
    # 2024-02-20 in 1.13 has no support for FEATURE_FLAG_MICRO_GATEWAY_ENABLED, comment it until it's supported
    # "MICRO_GATEWAY_ENABLED": env.bool("FEATURE_FLAG_MICRO_GATEWAY_ENABLED", False),
}

# ==============================================================================
# 提供给前端的环境变量值
# ==============================================================================
# 后续前端环境变量尽量走这个接口，而不是通过 src/dashboard-front/index.html + src/constant/config.ts 传入
BK_DOCS_URL_PREFIX = env.str("BK_DOCS_URL_PREFIX", default="https://bk.tencent.com/docs")
BK_APIGATEWAY_VERSION = env.str("BK_APIGATEWAY_VERSION", default="1.17.0")
ENV_VARS_FOR_FRONTEND = {
    "EDITION": EDITION,
    "BK_APP_CODE": BK_APP_CODE,
    "BK_DEFAULT_TEST_APP_CODE": DEFAULT_TEST_APP["bk_app_code"],
    "BK_API_RESOURCE_URL_TMPL": BK_API_URL_TMPL + "/{stage_name}/{resource_path}",
    "BK_COMPONENT_API_URL": BK_COMPONENT_API_URL,
    "BK_PAAS_APP_REPO_URL_TMPL": env.str(
        "BK_PAAS_APP_REPO_URL_TMPL", "https://example.com/groups/blueking-plugins/apigw/{{gateway_name}}.git"
    ),
    "BK_DASHBOARD_FE_URL": DASHBOARD_FE_URL,
    "BK_DASHBOARD_URL": DASHBOARD_URL,
    "BK_DASHBOARD_CSRF_COOKIE_NAME": CSRF_COOKIE_NAME,
    "BK_APIGATEWAY_VERSION": BK_APIGATEWAY_VERSION,
    "BK_DOCS_URL_PREFIX": BK_DOCS_URL_PREFIX,
    "BK_USER_WEB_API_URL": BK_API_URL_TMPL.format(api_name="bk-user-web") + "/prod",
    # 登录地址，带 /login/
    "BK_LOGIN_URL": BK_LOGIN_URL,
    # 访问统计
    "BK_ANALYSIS_SCRIPT_SRC": env.str("BK_ANALYSIS_SCRIPT_SRC", default=""),
    "CREATE_CHAT_API": env.str("CREATE_CHAT_API", default=""),
    "SEND_CHAT_API": env.str("SEND_CHAT_API", default=""),
    "HELPER": {
        "name": env.str("HELPER_NAME", default=""),
        "href": env.str("HELPER_HREF", default=""),
    },
    "BK_SHARED_RES_URL": env.str("BK_SHARED_RES_URL", default=""),
}


# ==============================================================================
# 网关资源数量限制
# ==============================================================================
MAX_STAGE_COUNT_PER_GATEWAY = env.int("MAX_STAGE_COUNT_PER_GATEWAY", 20)
API_GATEWAY_RESOURCE_LIMITS = {
    "max_gateway_count_per_app": env.int("MAX_GATEWAY_COUNT_PER_APP", 10),  # 每个 app 最多创建的网关数量
    "max_resource_count_per_gateway": env.int("MAX_RESOURCE_COUNT_PER_GATEWAY", 1000),  # 每个网关最多创建的 api 数量
    # 配置 app 的特殊规则
    "max_gateway_count_per_app_whitelist": {
        "bk_sops": 1000000,  # 标准运维网关数量无限制
        "data": 1000000,
    },
    # 配置网关的特殊规则
    "max_resource_count_per_gateway_whitelist": {
        "bk-esb": 5000,
        "bk-base": 2000,
    },
}
for k, v in env.dict("MAX_GATEWAY_COUNT_PER_APP_WHITELIST", default={}).items():
    API_GATEWAY_RESOURCE_LIMITS["max_gateway_count_per_app_whitelist"][k] = int(v)
for k, v in env.dict("MAX_RESOURCE_COUNT_PER_GATEWAY_WHITELIST", default={}).items():
    API_GATEWAY_RESOURCE_LIMITS["max_resource_count_per_gateway_whitelist"][k] = int(v)

# 网关下对象的最大数量
MAX_LABEL_COUNT_PER_GATEWAY = env.int("MAX_LABEL_COUNT_PER_GATEWAY", 100)
# 管理端支持的最大超时时间
MAX_BACKEND_TIMEOUT_IN_SECOND = env.int("MAX_BACKEND_TIMEOUT_IN_SECOND", 600)
# 每一个版本能生成的最大 python sdk 数量
MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION = env.int("MAX_PYTHON_SDK_COUNT_PER_RESOURCE_VERSION", 99)

# DB 操作大小配置
RELEASED_RESOURCE_CREATE_BATCH_SIZE = env.int("RELEASED_RESOURCE_CREATE_BATCH_SIZE", 50)
RELEASED_RESOURCE_DOC_CREATE_BATCH_SIZE = env.int("RELEASED_RESOURCE_DOC_CREATE_BATCH_SIZE", 50)

# ==============================================================================
# ESB 配置
# ==============================================================================
ESB_DEFAULT_BOARD = "default"

ESB_MANAGERS = env.list("ESB_MANAGERS", default=APIGW_MANAGERS)

# ESB 组件对应网关的名称
BK_ESB_GATEWAY_NAME = "bk-esb"

# 用户类型配置
USER_AUTH_TYPE_CONFIGS = {
    "default": {
        "boards": [
            "default",
        ],
    },
}

# 将 esb 的 jwt 密钥同步到指定名称的网关
SYNC_ESB_JWT_KEY_GATEWAY_NAMES = {
    BK_ESB_GATEWAY_NAME: {
        "description": "蓝鲸 ESB 编码组件",
        "description_en": "ESB Coding Component",
        "is_public": False,
    },
    "apigw": {
        "description": "蓝鲸 ESB 占位网关",
        "description_en": "ESB placeholder gateway",
        "is_public": False,
    },
}

# django translation, 避免循环引用
gettext = lambda s: s  # noqa

ESB_BOARD_CONFIGS = {
    "default": {
        "name": "default",
        "label": gettext("蓝鲸智云"),
        # envs
        "api_envs": [
            {
                "name": "prod",
                "label": gettext("正式环境"),
                "host": env.str("ESB_DEFAULT_BOARD_PROD_URL", "") or BK_COMPONENT_API_URL,
                "description": gettext("访问后端正式环境"),
            },
            {
                "name": "test",
                "label": gettext("测试环境"),
                "host": env.str("ESB_DEFAULT_BOARD_TEST_URL", ""),
                "description": gettext("访问后端测试环境"),
            },
        ],
        # sdk
        "has_sdk": env.bool("ESB_DEFAULT_BOARD_HAS_SDK", True),
        "sdk_name": "bkapi-component-open",
        "sdk_package_prefix": "bkapi_component.open",
        "sdk_doc_templates": {
            "python_sdk_usage_example": "python_sdk_usage_example_v2.md",
        },
        "sdk_description": gettext("访问蓝鲸智云组件 API"),
    },
}

# ==============================================================================
# 版本差异配置
# ==============================================================================
# 用户验证类型
USER_AUTH_TYPE = {
    "login_ticket": [
        {
            "key": "bk_token",
            "cookie_name": "bk_token",
        }
    ],
}

# ==============================================================================
# 安全相关
# ==============================================================================
FORBIDDEN_HOSTS = env.list("FORBIDDEN_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])
FORBIDDEN_PORTS = env.list("FORBIDDEN_PORTS", default=[])
