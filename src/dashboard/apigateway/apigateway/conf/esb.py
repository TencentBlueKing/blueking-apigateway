# -*- coding: utf-8 -*-
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
from apigateway.common.env import Env


def is_esb_enabled(env: Env) -> bool:
    """TE keeps its external ESB dependency; only EE honors ENABLE_ESB.

    Preserve the existing multi-tenant behavior and default to enabled for
    deployments that do not yet provide ENABLE_ESB.
    """
    return not env.bool("ENABLE_MULTI_TENANT_MODE", False) and not (
        env.str("EDITION", "ee") == "ee" and not env.bool("ENABLE_ESB", True)
    )


if __name__ == "__main__":
    # Migration scripts use the same policy without loading Django or its databases.
    print(str(is_esb_enabled(Env())).lower())
