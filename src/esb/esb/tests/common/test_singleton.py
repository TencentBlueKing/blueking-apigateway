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
import time
from threading import Thread

from common.singleton import SingletonMeta


class TestSingletonMeta:
    class RedColor(metaclass=SingletonMeta):
        pass

    class GreenColor(metaclass=SingletonMeta):
        pass

    class Benchmark(metaclass=SingletonMeta):
        def __init__(self):
            time.sleep(0.2)

    def test(self):
        r1 = TestSingletonMeta.RedColor()
        r2 = TestSingletonMeta.RedColor()

        g1 = TestSingletonMeta.GreenColor()

        assert r1 is r2
        assert id(r1) == id(r2)
        assert r1 is not g1

    def test_benchmark(self):
        ids = []

        def create():
            ids.append(id(TestSingletonMeta.Benchmark()))

        threads = [Thread(target=create) for i in range(20)]

        [thread.start() for thread in threads]
        [thread.join() for thread in threads]

        assert len(ids) == 20
        assert len(set(ids)) == 1
