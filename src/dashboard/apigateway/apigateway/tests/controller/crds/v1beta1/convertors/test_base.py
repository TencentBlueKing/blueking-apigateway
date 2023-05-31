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
class TestBaseConvertor:
    def test_common_metadata_with_short_name(
        self,
        fake_base_convertor,
        edge_gateway,
        edge_gateway_stage,
    ):
        name = "short-name"
        metadata = fake_base_convertor._common_metadata(name)
        assert 0 < len(metadata.name) <= 64
        assert name in metadata.name
        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

    def test_common_metadata_with_long_name(
        self,
        fake_base_convertor,
        edge_gateway,
        edge_gateway_stage,
    ):
        name = f"{'long-' * 16}name"
        metadata = fake_base_convertor._common_metadata(name)
        assert 0 < len(metadata.name) <= 64
        assert name not in metadata.name
        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name
