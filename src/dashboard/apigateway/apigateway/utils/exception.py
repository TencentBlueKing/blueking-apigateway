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
import logging
from typing import Optional, Type

logger = logging.getLogger(__name__)


def check_result_code(name: str, exception_type: Type[Exception], code: Optional[int], message: Optional[str]):
    """Check the code in result which returned by api response, if the code is not equal to 0, raise the exception."""

    logger.debug("checking %s result, code %s, message %s", name, code, message)
    if code == 0:
        return

    raise exception_type(f"{name} error, code {code}, message {message}")


class LockTimeout(Exception):
    """Lock timeout error"""
