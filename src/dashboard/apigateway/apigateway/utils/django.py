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
import json

from django.http import Http404
from django.shortcuts import get_object_or_404
from jsonfield import JSONField as BaseJSONField


def get_object_or_None(klass, *args, **kwargs):  # ruff: noqa: N802
    try:
        return get_object_or_404(klass, *args, **kwargs)
    except Http404:
        return None


class JSONField(BaseJSONField):
    # patched this change to support django loaddata command
    # https://github.com/rpkilby/jsonfield/commit/149cac46a12675f6f300add7336a9df49f39b990

    def to_python(self, value):
        if isinstance(value, (str, bytes)):
            return json.loads(value, **self.load_kwargs)

        return value
