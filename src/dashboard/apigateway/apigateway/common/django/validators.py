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
from django.utils.translation import gettext as _
from rest_framework import serializers


class NameValidator:
    """currently:
    - gateway_name can be endswith '-'
    - stage name can be endswith '-' and '_'
    - resource name can be endswith '-'
    while build the key/name of etcd/helm/sdk, the '-'/'_' will be striped,
    it would cause some problem if a-/a convert to the same key/name,
    so, we check the name while creating gateway/stage/resource
    since: 2024-01-16, make standardization
    """

    def __call__(self, value: str):
        if value.endswith("-"):
            raise serializers.ValidationError(_("名称不能以【-】结尾。"))

        if value.endswith("_"):
            raise serializers.ValidationError(_("名称不能以【_】结尾。"))
