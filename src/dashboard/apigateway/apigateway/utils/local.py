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
from werkzeug.local import Local as WerkzeugLocal
from werkzeug.local import release_local

from apigateway.utils.singleton import Singleton
from apigateway.utils.string import generate_unique_id

_local = WerkzeugLocal()


class Local(metaclass=Singleton):
    """
    配合中间件 RequestIDMiddleware 使用
    """

    @property
    def request(self):
        """
        获取全局 request 对象
        """
        return getattr(_local, "request", None)

    @request.setter
    def request(self, value):
        _local.request = value

    @property
    def request_id(self):
        if self.request:
            return self.request.request_id
        return generate_unique_id()

    def release(self):
        release_local(_local)


local = Local()
