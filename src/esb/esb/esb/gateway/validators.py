# -*- coding: utf-8 -*
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
from common.base_validators import BaseValidator


class APIGatewayAdapter(BaseValidator):
    """A special validator, for ESB running under API Gateway"""

    def validate(self, request):
        if not request.apigw.enabled:
            return

        user = request.apigw.user
        if user:
            request.g.current_user_username = user["username"]
            request.g.current_user_verified = user["verified"]
            request.g.user_valid_error_message = user.get("valid_error_message")

        app = request.apigw.app
        if app:
            request.g.app_code = app["app_code"]
            request.g.is_app_verified = app["verified"]
            request.g.app_valid_error_message = app.get("valid_error_message")
