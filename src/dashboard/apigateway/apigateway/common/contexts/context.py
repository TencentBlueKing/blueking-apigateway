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
from abc import ABCMeta
from typing import Text

from django.utils.functional import cached_property

from apigateway.core.models import Context

_undefined = object()


class BaseContext(metaclass=ABCMeta):
    scope_type: Text = ""
    type: Text = ""

    @cached_property
    def schema(self):
        raise NotImplementedError()

    def save(self, scope_id, config):
        return Context.objects.update_or_create(
            scope_type=self.scope_type,
            scope_id=scope_id,
            type=self.type,
            defaults={
                "config": config,
                "schema": self.schema,
            },
        )

    def get_config(self, scope_id, default=_undefined):
        try:
            return Context.objects.get(
                scope_type=self.scope_type,
                scope_id=scope_id,
                type=self.type,
            ).config
        except Context.DoesNotExist:
            if default is _undefined:
                raise

            return default

    def filter_contexts(self, scope_ids=None):
        queryset = Context.objects.filter(
            scope_type=self.scope_type,
            type=self.type,
        )
        if scope_ids is not None:
            queryset = queryset.filter(scope_id__in=scope_ids)
        return queryset

    def delete(self, scope_ids):
        return Context.objects.filter(
            scope_type=self.scope_type,
            scope_id__in=scope_ids,
            type=self.type,
        ).delete()
