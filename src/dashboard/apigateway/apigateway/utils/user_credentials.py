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
from dataclasses import dataclass
from typing import Optional

from django.conf import settings


@dataclass
class UserCredentials:
    credentials: str

    def to_dict(self):
        return {
            settings.BK_LOGIN_TICKET_KEY: self.credentials,
        }


# FIXME: maybe we don't need this anymore? can we remove it?
def get_user_credentials_from_request(request) -> Optional[UserCredentials]:
    credentials = request.COOKIES.get(settings.BK_LOGIN_TICKET_KEY, None)
    if not credentials:
        return None
    return UserCredentials(credentials=credentials)
