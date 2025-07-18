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

import base64
import hashlib
import hmac
import json

from .compat import str


def get_signature(method, path, app_secret, params=None, data=None):
    """generate signature"""
    kwargs = {}
    if params:
        kwargs.update(params)
    if data:
        data = json.dumps(data) if isinstance(data, dict) else data
        kwargs["data"] = data
    kwargs = "&".join(["%s=%s" % (k, v) for k, v in sorted(kwargs.items(), key=lambda x: x[0])])
    orignal = "%s%s?%s" % (method, path, kwargs)
    app_secret = app_secret.encode("utf-8") if isinstance(app_secret, str) else app_secret
    orignal = orignal.encode("utf-8") if isinstance(orignal, str) else orignal
    signature = base64.b64encode(hmac.new(app_secret, orignal, hashlib.sha1).digest())
    return signature if isinstance(signature, str) else signature.decode("utf-8")
