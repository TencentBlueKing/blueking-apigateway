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
""""
管理访问 ESB 非公开组件

ESB 非公开组件未包含在 bkapi_component.open 中，
为方便调用这些组件，此处基于 bkapi_client_core 中的 ESBClient，并参照 bkapi_componet.open 实现，对这些组件进行封装
"""
from bkapi_client_core.esb import ESBClient, Operation, OperationGroup, bind_property
from bkapi_client_core.esb import generic_type_partial as _partial
from bkapi_client_core.esb.django_helper import get_client_by_username as _get_client_by_username


class BkLogGroup(OperationGroup):
    esquery_dsl = bind_property(
        Operation,
        name="esquery_dsl",
        method="POST",
        path="/api/c/compapi/v2/bk_log/esquery_dsl/",
    )


class EsbGroup(OperationGroup):
    get_synchronized_components = bind_property(
        Operation,
        name="get_synchronized_components",
        method="GET",
        path="/api/c/compapi/esb/get_synchronized_components/",
    )


class Client(ESBClient):
    """ESB Components"""

    bk_log = bind_property(BkLogGroup, name="bk_log")
    esb = bind_property(EsbGroup, name="esb")


get_client_by_username = _partial(Client, _get_client_by_username)
