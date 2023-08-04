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

LOG_MAX_BYTES = 500 * 1024 * 1024
LOG_BACKUP_COUNT = 3
LOG_CLASS = "concurrent_log_handler.ConcurrentRotatingFileHandler"


def get_logging_config(log_level: str, log_dir: str, log_to_file: bool = False, log_api_log_to_file: bool = True):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(levelname)s [%(asctime)s] %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d \n \t %(message)s \n",  # noqa
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                # 不要添加换行符，Elasticsearch日志采集器认为每行均是一个合法JSON字符串
                "format": "%(message)s"
            },
        },
        "handlers": {
            "null": {
                "level": "DEBUG",
                "class": "logging.NullHandler",
            },
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "console_simple": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "root": _get_logging_handler(log_to_file, os.path.join(log_dir, "esb.log"), "verbose"),
            "api": _get_logging_handler(log_api_log_to_file, os.path.join(log_dir, "esb_api.log"), "simple"),
            "mysql": _get_logging_handler(log_to_file, os.path.join(log_dir, "esb_mysql.log"), "verbose"),
        },
        "loggers": {
            "django": {
                "handlers": ["root"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.request": {
                "handlers": ["root"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.db.backends": {
                "handlers": ["mysql"],
                "level": "ERROR",
                "propagate": True,
            },
            "thrift": {
                "handlers": ["root"],
                "level": "ERROR",
                "propagate": True,
            },
            # the root logger, for all the project
            "root": {
                "handlers": ["root"],
                "level": log_level,
                "propagate": False,
            },
            # Logging config for ESB projects
            "api": {
                "handlers": ["api"],
                "level": "INFO",
                "propagate": False,
            },
            "esb.management": {
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
