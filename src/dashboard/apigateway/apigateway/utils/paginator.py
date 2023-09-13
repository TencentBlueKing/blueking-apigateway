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


class LimitOffsetPaginator:
    """
    根据给定的 count、offset、limit，计算分页信息，并获取分页数据
    """

    def __init__(self, count: int, offset: int, limit: int):
        self.count = count
        self.offset = offset
        self.limit = limit

    def has_next(self) -> bool:
        return self.offset + self.limit < self.count

    def has_previous(self) -> bool:
        return self.offset > 0

    def get_paginated_data(self, data: list) -> dict:
        return {
            "count": self.count,
            "has_next": self.has_next(),
            "has_previous": self.has_previous(),
            "results": data,
        }
