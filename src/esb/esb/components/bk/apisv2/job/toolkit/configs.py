# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from future import standard_library

standard_library.install_aliases()
import os.path  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

from django.conf import settings  # noqa: E402

from esb.utils import SmartHost, get_ssl_root_dir  # noqa: E402

SYSTEM_NAME = "JOB"

HOST_JOB = getattr(settings, "HOST_JOB", "")
if HOST_JOB.startswith("https://"):
    host_job = HOST_JOB
elif HOST_JOB.startswith("http://"):
    host_job = urlparse(HOST_JOB)._replace(scheme="https").geturl()
else:
    host_job = "https://%s" % HOST_JOB

host = SmartHost(host_prod=host_job)

# 证书配置
SSL_ROOT_DIR = get_ssl_root_dir()
CLIENT_CERT = os.path.join(SSL_ROOT_DIR, "job_esb_api_client.crt")
CLIENT_KEY = os.path.join(SSL_ROOT_DIR, "job_esb_api_client.key")
