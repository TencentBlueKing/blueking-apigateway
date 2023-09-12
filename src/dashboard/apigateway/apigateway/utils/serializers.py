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

from rest_framework import serializers as drf_serializers


class CustomFieldsSerializer(drf_serializers.Serializer):
    """
    支持添加`自定义字段`的serializer
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'add_fields' arg up to the superclass
        add_fields = kwargs.pop("add_fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if add_fields is not None:
            # Add 'add_fields' to fields
            self.fields.update(add_fields)
