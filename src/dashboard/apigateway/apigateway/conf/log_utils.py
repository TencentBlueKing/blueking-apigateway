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
from pathlib import Path
from typing import Any, Dict, List, Optional


def build_logging_config(log_level: str, to_console: bool, file_directory: Optional[Path], file_format: str) -> Dict:
    """Build the global logging config dict.
    :param log_level: The log level.
    :param to_console: If True, output the logs to the console.
    :param file_directory: If the value is not None, output the logs to the given directory.
    :param file_format: The format of the logging file, "json" or "text".
    :return: The logging config dict.
    """

    def _build_file_handler(log_path: Path, filename: str, format: str) -> Dict:
        if format not in ("json", "text"):
            raise ValueError(f"Invalid file_format: {file_format}")
        formatter = "verbose_json" if format == "json" else "verbose"
        return {
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "level": log_level,
            "formatter": formatter,
            "filename": str(log_path / filename),
            # Set max file size to 100MB
            "maxBytes": 100 * 1024 * 1024,
            "backupCount": 5,
        }

    handlers_config: Dict[str, Any] = {
        "null": {"level": log_level, "class": "logging.NullHandler"},
        "console": {"level": log_level, "class": "logging.StreamHandler", "formatter": "verbose"},
        "console_simple": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "sentry": {
            "level": "ERROR",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
            "formatter": "verbose",
        },
    }
    # 生成指定 Logger 对应的 Handlers
    logger_handlers_map: Dict[str, List[str]] = {}
    for logger_name in ["root", "component", "iam", "mysql", "celery"]:
        handlers = []

        if to_console:
            handlers.append("console")

        if file_directory:
            # 生成 logger 对应日志文件的 Handler
            handlers_config[logger_name] = _build_file_handler(
                file_directory, f"{logger_name}-{file_format}.log", file_format
            )
            handlers.append(logger_name)

        logger_handlers_map[logger_name] = handlers

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": (
                    "%(name)s %(levelname)s [%(asctime)s] %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d "
                    "\n \t%(message)s \n"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "verbose_json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": (
                    "%(name)s %(levelname)s %(asctime)s %(pathname)s %(lineno)d "
                    "%(funcName)s %(process)d %(thread)d %(message)s"
                ),
            },
            "simple": {"format": "%(name)s %(levelname)s %(message)s"},
        },
        "handlers": handlers_config,
        # the root logger, 用于整个项目的默认 logger
        "root": {"handlers": logger_handlers_map["root"], "level": log_level, "propagate": False},
        "loggers": {
            "django": {
                "handlers": [*logger_handlers_map["root"], "sentry"],
                "level": "ERROR",
                "propagate": True,
            },
            "django.db.backends": {
                "handlers": logger_handlers_map["mysql"],
                "level": log_level,
                "propagate": True,
            },
            # 组件调用日志
            "component": {
                "handlers": [*logger_handlers_map["component"], "sentry"],
                "level": log_level,
                "propagate": False,
            },
            "bkapi_client_core": {
                "handlers": [*logger_handlers_map["component"], "sentry"],
                "level": log_level,
                "propagate": False,
            },
            "iam": {
                "handlers": [*logger_handlers_map["iam"], "sentry"],
                "level": log_level,
                "propagate": False,
            },
            "celery": {
                "handlers": [*logger_handlers_map["celery"], "sentry"],
                "level": "INFO",
                "propagate": False,
            },
            "opentelemetry.util._time": {
                # TODO: 升级 python >= 3.7 后，可删除此 logger
                "handlers": [*logger_handlers_map["celery"], "sentry"],
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
        },
    }
