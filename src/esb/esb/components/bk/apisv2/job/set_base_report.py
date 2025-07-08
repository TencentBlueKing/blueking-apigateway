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

from django import forms

from common.constants import API_TYPE_OP, HTTP_METHOD
from common.forms import BaseComponentForm, TypeCheckField
from components.component import Component
from .toolkit import configs, tools


class SetBaseReport(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"开启/关闭Agent基础数据采集上报功能"
    label_en = "Enable / disable agent basic data collection and reporting function"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP
    host = configs.host

    class Form(BaseComponentForm):
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        sys_id = forms.IntegerField(label="system information reported dataid", required=True)
        cpu_id = forms.IntegerField(label="cpu information reported dataid", required=True)
        mem_id = forms.IntegerField(label="memery information reported dataid", required=True)
        net_id = forms.IntegerField(label="NIC information reported dataid", required=True)
        disk_id = forms.IntegerField(label="disk I/O information reported dataid", required=True)
        proc_id = forms.IntegerField(label="process information reported dataid", required=True)
        crontab_id = forms.IntegerField(label="crontab information reported dataid", required=True)
        iptables_id = forms.IntegerField(label="iptables information reported dataid", required=True)
        ip_list = TypeCheckField(label="ip list", promise_type=list, required=True)

        def clean(self):
            data = self.cleaned_data
            return {
                "bk_biz_id": data["bk_biz_id"],
                "params": {
                    "sys_id": data["sys_id"],
                    "cpu_id": data["cpu_id"],
                    "mem_id": data["mem_id"],
                    "net_id": data["net_id"],
                    "proc_id": data["proc_id"],
                    "disk_id": data["disk_id"],
                    "crontab_id": data["crontab_id"],
                    "iptables_id": data["iptables_id"],
                    "ip_list": data["ip_list"],
                },
            }

    def handle(self):
        params = tools.get_action_params(
            action="set_base_report",
            params=self.form_data,
            operator=self.current_user.username,
            app_code=self.request.app_code,
            request_id=self.request.request_id,
        )

        client = tools.JOBClient(self.outgoing.http_client)
        self.response.payload = client.post(
            self.host, "/api/v2/set_base_report", data=params, bk_language=self.request.bk_language
        )
