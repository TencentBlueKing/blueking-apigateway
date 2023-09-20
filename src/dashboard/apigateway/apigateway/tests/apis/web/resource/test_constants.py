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

from apigateway.apis.web.resource.constants import PATH_VAR_PATTERN, STAGE_PATH_VAR_NAME_PATTERN


@pytest.mark.parametrize(
    "value, expected",
    [
        ("/echo/{username}/", ["username"]),
        ("/hello/{env.region}/", ["env.region"]),
        ("/hello/{{uuid}}", ["{uuid"]),
    ],
)
def test_path_var_pattern(value, expected):
    result = PATH_VAR_PATTERN.findall(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("env.username", "username"),
        ("envregion", None),
    ],
)
def test_stage_path_var_name_pattern(value, expected):
    result = STAGE_PATH_VAR_NAME_PATTERN.match(value)
    if result:
        result = result.group(1)

    assert result == expected
