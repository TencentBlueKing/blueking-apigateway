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
import copy


class ExtensibleFieldMixin:
    """
    如果 Serializer 包含无法写入到自身模型的字段，保存时，去除这些字段
    """

    class Meta:
        non_model_fields = None

    def create(self, validated_data):
        if not self.Meta.non_model_fields:
            return super().create(validated_data)

        data = copy.copy(validated_data)
        for field in self.Meta.non_model_fields:
            data.pop(field, None)
        return super().create(data)

    def update(self, instance, validated_data):
        if not self.Meta.non_model_fields:
            return super().update(instance, validated_data)

        data = copy.copy(validated_data)
        for field in self.Meta.non_model_fields:
            data.pop(field, None)
        return super().update(instance, data)
