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

import time

from django import forms

from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs


class Detect(Component):
    """心跳探测，测试用"""

    sys_name = configs.SYSTEM_NAME

    class Form(BaseComponentForm):
        timestamp = forms.IntegerField(label="timestamp", required=True)
        sleep_time = forms.IntegerField(label="sleep time", required=False)

    def handle(self):
        if self.form_data.get("sleep_time"):
            time.sleep(self.form_data["sleep_time"])

        self.response.payload = {
            "result": True,
            "data": {
                "timestamp": self.form_data["timestamp"],
                "now": int(time.time()),
            },
        }
