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

from common.base_utils import get_not_empty_value
from common.constants import API_TYPE_Q, HTTP_METHOD
from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs, tools


class GetCronList(Component):
    suggest_method = HTTP_METHOD.GET
    label = u"查询业务下定时作业信息"
    label_en = "Get cron list"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    host = configs.host

    class Form(BaseComponentForm):
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        cron_name = forms.CharField(label="cron job name", required=False)
        cron_id = forms.IntegerField(label="cron job id", required=False)
        cron_status = forms.CharField(label="cron job status", required=False)
        creator = forms.CharField(label="creator", required=False)
        create_time_start = forms.DateField(label="creation start time", required=False, input_formats=["%Y-%m-%d"])
        create_time_end = forms.DateField(label="creation end time", required=False, input_formats=["%Y-%m-%d"])
        last_modify_user = forms.CharField(label="last modifier", required=False)
        last_modify_time_start = forms.DateField(
            label="last modification start time", required=False, input_formats=["%Y-%m-%d"]
        )  # noqa
        last_modify_time_end = forms.DateField(
            label="last modification end time", required=False, input_formats=["%Y-%m-%d"]
        )  # noqa
        start = forms.IntegerField(label="start", required=False)
        length = forms.IntegerField(label="length", required=False)

        def clean(self):
            data = self.cleaned_data

            params = {
                "cron_name": data["cron_name"],
                "cron_id": data["cron_id"],
                "cron_status": data["cron_status"],
                "creator": data["creator"],
                "last_modify_user": data["last_modify_user"],
                "start": data["start"],
                "length": data["length"],
            }
            date_param_keys = [
                "create_time_start",
                "create_time_end",
                "last_modify_time_start",
                "last_modify_time_end",
            ]
            for key in date_param_keys:
                if data[key]:
                    params[key] = data[key].strftime("%Y-%m-%d")

            return {"bk_biz_id": data["bk_biz_id"], "params": get_not_empty_value(params)}

    def handle(self):
        params = tools.get_action_params(
            action="get_cron_list",
            params=self.form_data,
            operator=self.current_user.username,
            app_code=self.request.app_code,
            request_id=self.request.request_id,
        )

        client = tools.JOBClient(self.outgoing.http_client)
        self.response.payload = client.post(
            self.host, "/api/v2/get_cron_list", data=params, bk_language=self.request.bk_language
        )
