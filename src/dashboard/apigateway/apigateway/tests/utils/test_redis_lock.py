# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

import pytest

from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import Lock

pytestmark = pytest.mark.no_meta_schema


@pytest.fixture
def redis_client(mocker):
    client = mocker.Mock(spec=["lock", "delete"])
    client.lock.return_value.acquire.return_value = True
    mocker.patch("apigateway.utils.redis_utils.get_default_redis_client", return_value=client)
    return client


def test_lock_passes_timeout_and_releases(redis_client):
    with Lock("test_lock", timeout=30):
        redis_client.delete.assert_not_called()
    redis_client.lock.assert_called_once_with("lock_test_lock", 30)
    redis_client.lock.return_value.acquire.assert_called_once_with(blocking=False)
    redis_client.delete.assert_called_once_with("lock_test_lock")


def test_lock_releases_on_body_error(redis_client):
    with pytest.raises(ValueError, match="body error"), Lock("test_lock"):
        raise ValueError("body error")
    redis_client.delete.assert_called_once_with("lock_test_lock")


def test_lock_retries_until_acquired(redis_client, mocker):
    sleep = mocker.patch("apigateway.utils.redis_utils.time.sleep")
    redis_client.lock.return_value.acquire.side_effect = [False, True]
    with Lock("test_lock", try_get_times=3):
        assert redis_client.lock.return_value.acquire.call_count == 2
    sleep.assert_called_once_with(1)
    redis_client.delete.assert_called_once_with("lock_test_lock")


def test_failed_acquisition_does_not_delete_another_lock(redis_client, mocker):
    sleep = mocker.patch("apigateway.utils.redis_utils.time.sleep")
    redis_client.lock.return_value.acquire.return_value = False
    with pytest.raises(LockTimeout, match="Timeout while waiting for lock"), Lock("test_lock", try_get_times=2):
        pytest.fail("failed acquisition must not enter the body")
    assert redis_client.lock.return_value.acquire.call_count == 2
    sleep.assert_called_once_with(1)
    redis_client.delete.assert_not_called()
