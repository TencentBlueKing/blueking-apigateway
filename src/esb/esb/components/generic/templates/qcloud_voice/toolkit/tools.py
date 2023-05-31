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

import hashlib
import json
import random
import time
from builtins import object

from django.utils.encoding import force_bytes

from . import configs


class QCloudVoiceClient(object):
    def __init__(self, http_client):
        self.http_client = http_client

    def get_random(self):
        return random.randint(10000, 99999)

    def get_cur_time(self):
        return int(time.time())

    def generate_sig(self, qcloud_app_key, mobile, random_int, now):
        text = "appkey={}&random={}&time={}&mobile={}".format(qcloud_app_key, random_int, now, mobile)
        return hashlib.sha256(force_bytes(text)).hexdigest()

    def post(self, path, data):
        return self.http_client.post(configs.host, path, data=json.dumps(data))
