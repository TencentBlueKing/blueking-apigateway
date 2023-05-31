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
import logging
import subprocess

from django.utils.encoding import force_str

logger = logging.getLogger(__name__)


def run_command(cmd, check=False, timeout=10):
    if isinstance(cmd, list):
        shell = False
    else:
        shell = True

    try:
        completed_process = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        logger.error(f"run shell {cmd} error.")
        raise e

    if completed_process.returncode != 0:
        logger.error(
            f"run shell {cmd} fail. "
            f"returncode={completed_process.returncode}, "
            f"stdout={completed_process.stdout}, stderr={completed_process.stderr}"
        )

    return (completed_process.returncode, force_str(completed_process.stdout), force_str(completed_process.stderr))
