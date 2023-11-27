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

from apigateway.apps.release.validators import ReleaseValidationError, ReleaseValidator


class TestReleaseValidator:
    @pytest.mark.parametrize(
        "vars, mock_used_stage_vars, will_error",
        [
            # ok
            (
                {
                    "prefix": "/o",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                False,
            ),
            # var in path not exist
            (
                {
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in path invalid
            (
                {
                    "prefix": "/test/?a=b",
                    "domain": "bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts not exist
            (
                {
                    "prefix": "/test/",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
            # var in hosts invalid
            (
                {
                    "prefix": "/test/",
                    "domain": "http://bking.com",
                },
                {
                    "in_path": ["prefix"],
                    "in_host": ["domain"],
                },
                True,
            ),
        ],
    )
    def test_validate_stage_vars(
        self, mocker, fake_gateway, fake_stage, fake_resource_version, vars, mock_used_stage_vars, will_error
    ):
        mocker.patch(
            "apigateway.core.managers.ResourceVersionManager.get_used_stage_vars",
            return_value=mock_used_stage_vars,
        )

        fake_stage.vars = vars
        fake_stage.save(update_fields=["_vars"])

        validator = ReleaseValidator(fake_gateway, fake_stage, fake_resource_version.id)

        if will_error:
            with pytest.raises(Exception):
                validator._validate_stage_vars()
            return

        assert validator._validate_stage_vars() is None

    @pytest.mark.parametrize(
        "contain_hosts_ret,succeeded",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_validate_stage_upstreams(
        self,
        contain_hosts_ret,
        succeeded,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        mocker,
    ):
        with mocker.patch(
            "apigateway.apps.release.validators.StageProxyHTTPContext.contain_hosts",
            return_value=contain_hosts_ret,
        ):
            validator = ReleaseValidator(fake_gateway, fake_stage, fake_resource_version.id)

            if not succeeded:
                with pytest.raises(ReleaseValidationError):
                    validator._validate_stage_upstreams()
            else:
                assert validator._validate_stage_upstreams() is None
