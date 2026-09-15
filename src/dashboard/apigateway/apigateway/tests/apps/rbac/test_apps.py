#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
from apigateway.apps.rbac.apps import sync_gateway_iam


def test_sync_gateway_iam_runs_model_then_auth_commands(mocker):
    call = mocker.patch("apigateway.apps.rbac.apps.call_command")

    sync_gateway_iam(sender=None, using="default")

    assert call.call_args_list == [
        mocker.call("sync_gateway_rbac_model_to_iam"),
        mocker.call(
            "sync_gateway_rbac_auth_to_iam",
            initial=True,
            all=True,
            apply=True,
            force=True,
        ),
    ]


def test_sync_gateway_iam_skips_non_default_database(mocker):
    call = mocker.patch("apigateway.apps.rbac.apps.call_command")

    sync_gateway_iam(sender=None, using="bkcore")

    call.assert_not_called()
