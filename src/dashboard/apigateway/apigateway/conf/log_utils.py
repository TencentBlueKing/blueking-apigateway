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

LOG_CLASS = "logging.handlers.RotatingFileHandler"
LOG_MAX_BYTES = 1024 * 1024 * 100
LOG_BACKUP_COUNT = 5


def get_logging_config(log_level: str, is_local: bool, log_dir: str, log_to_file: bool):
    if is_local:
        logging_format = {
            "format": (
                "%(levelname)s [%(asctime)s] %(pathname)s "
                "%(lineno)d %(funcName)s %(process)d %(thread)d "
                "\n \t %(message)s \n"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    else:
        logging_format = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": (
                "%(levelname)s %(asctime)s %(pathname)s %(lineno)d " "%(funcName)s %(process)d %(thread)d %(message)s"
            ),
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": logging_format,
            "simple": {"format": "%(levelname)s %(message)s \n"},
        },
        "handlers": {
            "null": {
                "level": "DEBUG",
                "class": "logging.NullHandler",
            },
            "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
            "console_simple": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "root": _get_logging_handler(log_to_file, os.path.join(log_dir, "dashboard-django.log"), "verbose"),
            "component": _get_logging_handler(
                log_to_file, os.path.join(log_dir, "dashboard-component.log"), "verbose"
            ),
            "mysql": _get_logging_handler(log_to_file, os.path.join(log_dir, "dashboard-mysql.log"), "verbose"),
            "celery": _get_logging_handler(log_to_file, os.path.join(log_dir, "dashboard-celery.log"), "verbose"),
            "sentry": {
                "level": "ERROR",
                "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "": {
                "handlers": ["root", "sentry"],
                "level": log_level,
                "propagate": True,
            },
            "django": {
                "handlers": ["root", "sentry"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.db.backends": {
                "handlers": ["mysql"],
                "level": log_level,
                "propagate": True,
            },
            # 组件调用日志
            "component": {
                "handlers": ["component", "sentry"],
                "level": log_level,
                "propagate": False,
            },
            "bkapi_client_core": {
                "handlers": ["component", "sentry"],
                "level": log_level,
                "propagate": False,
            },
            "celery": {
                "handlers": ["celery", "sentry"],
                "level": "INFO",
                "propagate": False,
            },
            "opentelemetry.util._time": {
                # TODO: 升级 python >= 3.7 后，可删除此 logger
                "handlers": ["celery", "sentry"],
                "level": "ERROR",
                "propagate": False,
            },
            "apigateway.core.management": {
                "handlers": ["console_simple"],
                "level": "INFO",
                "propagate": True,
            },
            "apigateway.apps.esb.management": {
                "handlers": ["console_simple"],
                "level": "INFO",
                "propagate": True,
            },
            "apigateway.legacy_esb.management": {
                "handlers": ["console_simple"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }


def makedirs_when_not_exists(path: str):
    if not path or os.path.exists(path):
        return

    os.makedirs(path, exist_ok=True)


def _get_logging_handler(log_to_file: bool, filename: str, formatter: str):
    if log_to_file:
        return {
            "class": LOG_CLASS,
            "formatter": formatter,
            "filename": filename,
            "maxBytes": LOG_MAX_BYTES,
            "backupCount": LOG_BACKUP_COUNT,
        }

    return {
        "class": "logging.StreamHandler",
        "formatter": formatter,
    }
