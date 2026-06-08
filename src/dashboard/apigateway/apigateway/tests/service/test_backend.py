#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from django_dynamic_fixture import G

from apigateway.core.models import Backend
from apigateway.service.backend import get_backend_id_to_instance


def test_get_backend_id_to_instance_filters_by_gateway(fake_gateway):
    backend = G(Backend, gateway=fake_gateway, name="backend")
    G(Backend, name="other")

    assert get_backend_id_to_instance(fake_gateway.id) == {backend.id: backend}
