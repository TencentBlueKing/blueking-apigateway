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

from django.db import models

from apigateway.common.mixins.models import TimestampedModelMixin
from apigateway.schema.constants import SchemaTypeEnum
from apigateway.schema.managers import SchemaManager

"""
NOTE:
    - all foreign key reference to core/schema here should be on_delete=models.PROTECT
"""


class Schema(TimestampedModelMixin):
    """
    Schema, with all schemas for all the configs
    based on json schema. will validate the config before save

    http proxy 1.0
    http proxy 2.0  add one more field, but the old is still exists
    """

    name = models.CharField(max_length=64)
    type = models.CharField(max_length=32, choices=SchemaTypeEnum.get_choices(), blank=False, null=False)
    version = models.CharField(max_length=10, blank=False, null=False)

    _schema = models.TextField(db_column="schema", blank=False, null=False)

    description = models.CharField(max_length=512, blank=False, null=False)
    example = models.TextField()

    objects = SchemaManager()

    class Meta:
        verbose_name = "Schema"
        verbose_name_plural = "Schemas"
        unique_together = ("name", "type", "version")
        db_table = "schema"

    def __str__(self):
        return f"<Schema: {self.name}/{self.type}/{self.version}>"

    def natural_key(self):
        return (self.name, self.type, self.version)

    def snapshot(self, as_dict=False):
        """
        - can add field
        - should not delete field!!!!!!!!!
        """
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "version": self.version,
            # "created_time": time.format(self.created_time),
            # "updated_time": time.format(self.updated_time),
        }
        if as_dict:
            return data
        return json.dumps(data)

    def save(self, *args, **kwargs):
        if self.type not in dict(SchemaTypeEnum.get_choices()):
            raise ValueError("type should be one of SchemaTypeEnum")
        super().save(*args, **kwargs)

    @property
    def schema(self):
        return json.loads(self._schema)

    @schema.setter
    def schema(self, data):
        if isinstance(data, dict):
            self._schema = json.dumps(data)
        elif isinstance(data, str):
            # should be valid json string
            json.loads(data)
            self._schema = data
        else:
            raise TypeError("data should be dict or str")
