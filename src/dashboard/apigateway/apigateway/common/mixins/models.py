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
import json
import logging

from django.db import models
from jsonschema import ValidationError, validate

from apigateway.common.exceptions import SchemaNotExist, SchemaValidationError

logger = logging.getLogger(__name__)


class TimestampedModelMixin(models.Model):
    """model with created_time and updated_time"""

    created_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_time = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class OperatorModelMixin(models.Model):
    created_by = models.CharField(max_length=32, blank=True, null=True)
    updated_by = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        abstract = True


class ConfigFieldModelMixin(models.Model):
    _config = models.TextField(db_column="config")

    @property
    def config(self):
        if not self._config:
            return {}

        # print(f"in getter {self._config}")
        # print(self._config)
        return json.loads(self._config)

    @config.setter
    def config(self, data):
        # should be valid JSON string
        if isinstance(data, str):
            data = json.loads(data)

        # 允许模型定义中 schema 为 None，此时，直接保存 config 的配置
        # 如果模型定义中不允许 schema 为 None，通过模型 save 时 schema 不能为空的校验，保证非法 config 不会被保存
        if not self.schema:
            self._config = json.dumps(data)
            return

        if not self.schema.schema:
            raise SchemaNotExist("schema is empty!")

        schema = self.schema.schema

        try:
            validate(instance=data, schema=schema)
        except ValidationError as ve:
            logger.exception("validate config fail!")
            raise SchemaValidationError(str(ve))
        except Exception as e:
            logger.exception("validate fail, unknown fail!")
            raise SchemaValidationError(str(e))

        self._config = json.dumps(data)

    class Meta:
        abstract = True


class ConfigModelMixin(TimestampedModelMixin, OperatorModelMixin, ConfigFieldModelMixin):
    class Meta:
        abstract = True
