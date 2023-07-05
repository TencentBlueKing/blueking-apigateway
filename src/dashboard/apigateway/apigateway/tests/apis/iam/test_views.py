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


class TestIAMResourceAPIView:
    def test_post(self, mocker, request_view, fake_stage):
        mocker.patch(
            "apigateway.apis.iam.views.IAMResourceAPIView.authentication_classes",
            new_callable=mocker.PropertyMock(return_value=[]),
        )
        response = request_view(
            "POST",
            "apis.iam.iam_provider.resource_type",
            {
                "resource_type": "stage",
            },
            fake_stage.api,
            data={
                "method": "list_instance",
                "type": "stage",
                "filter": {
                    "parent": {
                        "id": str(fake_stage.api.id),
                        "type": "gateway",
                    },
                },
                "page": {"limit": 10, "offset": 0},
            },
        )

        result = response.json()

        assert response.status_code == 200
        assert result["code"] == 0
        assert result["data"] == {"results": [{"id": str(fake_stage.id), "display_name": fake_stage.name}], "count": 1}
