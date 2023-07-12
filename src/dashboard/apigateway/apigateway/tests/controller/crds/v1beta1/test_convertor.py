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
from apigateway.controller.crds.v1beta1.convertor import CustomResourceConvertor


class TestCustomResourceConvertor:
    def test_fixture(self, edge_custom_release_convertor):
        assert isinstance(edge_custom_release_convertor, CustomResourceConvertor)

    def test_convert(self, mocker, edge_custom_release_convertor):
        mocker.patch(
            "apigateway.controller.crds.v1beta1.convertors.resource.HttpResourceConvertor._save_resource_header_rewrite_plugin",
            return_value=None,
        )

        edge_custom_release_convertor.convert()

        resources = list(edge_custom_release_convertor.get_kubernetes_resources())
        assert len(resources) > 0
