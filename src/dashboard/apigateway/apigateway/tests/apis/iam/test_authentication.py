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
import pytest

from apigateway.apis.iam.authentication import IAMBasicAuthentication
from apigateway.apis.iam.exceptions import AuthenticationFailed


class TestIAMBasicAuthentication:
    def test_authenticate_credentials(self, mocker):
        mocker.patch(
            "apigateway.apis.iam.authentication.IAM.get_token",
            return_value=(True, "", "my-token"),
        )

        result = IAMBasicAuthentication().authenticate_credentials(userid="bk_iam", password="my-token")
        assert result == ({"username": "bk_iam", "password": "my-token"}, None)

    @pytest.mark.parametrize(
        "userid, password, get_token_result",
        [
            ("test", "my-token", (True, "", "my-token")),
            ("bk_iam", "my-token", (False, "", None)),
            ("bk_iam", "my-token", (True, "", "invalid-token")),
        ],
    )
    def test_authenticate_credentials__error(self, mocker, userid, password, get_token_result):
        mocker.patch(
            "apigateway.apis.iam.authentication.IAM.get_token",
            return_value=get_token_result,
        )

        with pytest.raises(AuthenticationFailed):
            IAMBasicAuthentication().authenticate_credentials(userid=userid, password=password)
