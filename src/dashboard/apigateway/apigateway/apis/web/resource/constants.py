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
import re

from apigateway.core.constants import STAGE_VAR_REFERENCE_PATTERN

# 每个资源允许关联的最大标签个数
MAX_LABEL_COUNT_PER_RESOURCE = 10

# 路径变量正则
PATH_PATTERN = re.compile(r"^/[\w{}/.-]*$")
PATH_VAR_PATTERN = re.compile(r"\{(.*?)\}")

# 通常的路径变量，如 {project_id}
NORMAL_PATH_VAR_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,29}$")
# 环境中包含环境变量，如 {env.prefix}
STAGE_PATH_VAR_NAME_PATTERN = re.compile(r"^%s$" % STAGE_VAR_REFERENCE_PATTERN.pattern)

# 资源正则
RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,255}$")
