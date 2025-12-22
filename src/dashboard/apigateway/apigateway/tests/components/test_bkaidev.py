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

import pytest

from apigateway.components.bkaidev import (
    _convert_prompt,
    _convert_prompts,
    _get_mock_prompts_by_ids,
    _get_mock_prompts_by_keyword,
    _get_mock_prompts_updated_time,
    fetch_prompts_by_ids,
    fetch_prompts_list,
    fetch_prompts_updated_time,
)

pytestmark = pytest.mark.django_db


class TestConvertPrompt:
    def test_convert_prompt(self):
        """测试单个 prompt 数据转换"""
        remote_prompt = {
            "prompt_id": 1,
            "prompt_code": "prompt_001",
            "prompt_name": "代码审查助手",
            "prompt_content": "你是一个专业的代码审查专家",
            "updated_at": "2025-12-15T10:00:00Z",
            "updated_by": "admin",
            "tag_names": ["代码", "审查"],
            "generate_type": "public",
            "is_public": True,
            "space_id": "devops",
            "space_name": "DevOps",
        }

        result = _convert_prompt(remote_prompt)

        assert result["id"] == 1
        assert result["name"] == "代码审查助手"
        assert result["code"] == "prompt_001"
        assert result["content"] == "你是一个专业的代码审查专家"
        assert result["updated_time"] == "2025-12-15T10:00:00Z"
        assert result["updated_by"] == "admin"
        assert result["labels"] == ["代码", "审查"]
        assert result["is_public"] is True
        assert result["space_code"] == "devops"
        assert result["space_name"] == "DevOps"

    def test_convert_prompt_with_missing_fields(self):
        """测试缺少字段时的默认值"""
        remote_prompt = {
            "prompt_id": 1,
            "prompt_name": "测试",
        }

        result = _convert_prompt(remote_prompt)

        assert result["id"] == 1
        assert result["name"] == "测试"
        assert result["code"] == ""
        assert result["content"] == ""
        assert result["updated_time"] == ""
        assert result["updated_by"] == ""
        assert result["labels"] == []
        assert result["is_public"] is False
        assert result["space_code"] == ""
        assert result["space_name"] == ""

    def test_convert_prompts(self):
        """测试批量转换 prompts 数据"""
        remote_prompts = [
            {"prompt_id": 1, "prompt_name": "Prompt 1", "prompt_code": "p1"},
            {"prompt_id": 2, "prompt_name": "Prompt 2", "prompt_code": "p2"},
        ]

        result = _convert_prompts(remote_prompts)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Prompt 1"
        assert result[1]["id"] == 2
        assert result[1]["name"] == "Prompt 2"


class TestMockPrompts:
    def test_get_mock_prompts_by_keyword(self):
        """测试获取 mock prompts 列表"""
        result = _get_mock_prompts_by_keyword()

        assert len(result) >= 1
        # 验证返回的是原始格式
        assert "prompt_id" in result[0]
        assert "prompt_name" in result[0]
        assert "prompt_code" in result[0]

    def test_get_mock_prompts_by_ids(self):
        """测试根据 ID 获取 mock prompts"""
        result = _get_mock_prompts_by_ids([1, 2])

        assert len(result) == 2
        assert result[0]["prompt_id"] == 1
        assert result[1]["prompt_id"] == 2

    def test_get_mock_prompts_by_ids_partial(self):
        """测试部分 ID 存在的情况"""
        result = _get_mock_prompts_by_ids([1, 999])

        assert len(result) == 1
        assert result[0]["prompt_id"] == 1

    def test_get_mock_prompts_by_ids_empty(self):
        """测试空 ID 列表"""
        result = _get_mock_prompts_by_ids([])

        assert result == []

    def test_get_mock_prompts_updated_time(self):
        """测试获取 mock prompts 更新时间"""
        result = _get_mock_prompts_updated_time([1, 2])

        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        assert result[1] == "2025-12-15T10:00:00Z"

    def test_get_mock_prompts_updated_time_empty(self):
        """测试空 ID 列表"""
        result = _get_mock_prompts_updated_time([])

        assert result == {}


class TestFetchPromptsListMock:
    def test_fetch_prompts_list_mock(self, settings, mocker):
        """测试 mock 模式下获取 prompts 列表"""
        settings.BKAIDEV_USE_MOCK = True
        mock_credentials = mocker.MagicMock()

        result = fetch_prompts_list(mock_credentials)

        assert len(result) >= 1
        # 验证返回的是转换后的格式
        assert "id" in result[0]
        assert "name" in result[0]
        assert "code" in result[0]
        assert "content" in result[0]


class TestFetchPromptsByIdsMock:
    def test_fetch_prompts_by_ids_mock(self, settings):
        """测试 mock 模式下根据 ID 获取 prompts"""
        settings.BKAIDEV_USE_MOCK = True

        result = fetch_prompts_by_ids([1, 2], with_content=True)

        assert len(result) == 2
        # 验证返回的是转换后的格式
        assert result[0]["id"] == 1
        assert result[0]["name"] == "代码审查助手"
        assert "content" in result[0]

    def test_fetch_prompts_by_ids_empty(self, settings):
        """测试空 ID 列表"""
        settings.BKAIDEV_USE_MOCK = True

        result = fetch_prompts_by_ids([])

        assert result == []


class TestFetchPromptsUpdatedTimeMock:
    def test_fetch_prompts_updated_time_mock(self, settings):
        """测试 mock 模式下获取 prompts 更新时间"""
        settings.BKAIDEV_USE_MOCK = True

        result = fetch_prompts_updated_time([1, 2])

        assert len(result) == 2
        assert 1 in result
        assert 2 in result

    def test_fetch_prompts_updated_time_empty(self, settings):
        """测试空 ID 列表"""
        settings.BKAIDEV_USE_MOCK = True

        result = fetch_prompts_updated_time([])

        assert result == {}


class TestFetchPromptsListApi:
    def test_fetch_prompts_list_api(self, settings, mocker):
        """测试调用真实 API 获取 prompts 列表"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = "http://bkaidev.example.com"
        settings.BKAIDEV_API_TIMEOUT = 30

        mock_credentials = mocker.MagicMock()
        mock_call_api = mocker.patch(
            "apigateway.components.bkaidev._call_bkaidev_api",
            return_value={
                "data": {
                    "results": [
                        {
                            "prompt_id": 100,
                            "prompt_code": "api_prompt",
                            "prompt_name": "API Prompt",
                            "prompt_content": "API Content",
                            "updated_at": "2025-12-18T10:00:00Z",
                            "updated_by": "api_user",
                            "tag_names": ["api"],
                            "is_public": True,
                            "space_id": "api_space",
                            "space_name": "API Space",
                        }
                    ]
                }
            },
        )

        result = fetch_prompts_list(mock_credentials)

        assert len(result) == 1
        assert result[0]["id"] == 100
        assert result[0]["name"] == "API Prompt"
        assert result[0]["code"] == "api_prompt"
        mock_call_api.assert_called_once()

    def test_fetch_prompts_list_api_no_prefix(self, settings, mocker):
        """测试未配置 BKAIDEV_URL_PREFIX 时抛出异常"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = ""

        mock_credentials = mocker.MagicMock()

        with pytest.raises(Exception):
            fetch_prompts_list(mock_credentials)


class TestFetchPromptsByIdsApi:
    def test_fetch_prompts_by_ids_api(self, settings, mocker):
        """测试调用真实 API 根据 ID 获取 prompts"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = "http://bkaidev.example.com"
        settings.BKAIDEV_API_TIMEOUT = 30

        mock_call_api = mocker.patch(
            "apigateway.components.bkaidev._call_bkaidev_api",
            return_value={
                "data": {
                    "results": [
                        {
                            "prompt_id": 100,
                            "prompt_code": "api_prompt",
                            "prompt_name": "API Prompt",
                            "prompt_content": "API Content",
                            "is_public": True,
                        }
                    ]
                }
            },
        )

        result = fetch_prompts_by_ids([100], with_content=True)

        assert len(result) == 1
        assert result[0]["id"] == 100
        # 验证调用参数包含 type 和 with_content
        call_args = mock_call_api.call_args
        assert call_args[0][1] == "/openapi/aidev/platform/resource/v1/prompts/batch/"
        assert call_args[0][2]["ids"] == [100]
        assert call_args[0][2]["type"] == "prompt"
        assert call_args[0][2]["with_content"] is True

    def test_fetch_prompts_by_ids_api_without_content(self, settings, mocker):
        """测试调用 API 时 with_content=False"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = "http://bkaidev.example.com"
        settings.BKAIDEV_API_TIMEOUT = 30

        mock_call_api = mocker.patch(
            "apigateway.components.bkaidev._call_bkaidev_api",
            return_value={"data": {"results": []}},
        )

        fetch_prompts_by_ids([100], with_content=False)

        call_args = mock_call_api.call_args
        assert call_args[0][2]["with_content"] is False

    def test_fetch_prompts_by_ids_api_no_prefix(self, settings, mocker):
        """测试未配置 BKAIDEV_URL_PREFIX 时抛出异常"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = ""

        with pytest.raises(Exception):
            fetch_prompts_by_ids([1, 2])


class TestFetchPromptsUpdatedTimeApi:
    def test_fetch_prompts_updated_time_api(self, settings, mocker):
        """测试调用真实 API 获取 prompts 更新时间"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = "http://bkaidev.example.com"
        settings.BKAIDEV_API_TIMEOUT = 30

        mock_call_api = mocker.patch(
            "apigateway.components.bkaidev._call_bkaidev_api",
            return_value={
                "data": {
                    "results": [
                        {"prompt_id": 100, "updated_at": "2025-12-18T10:00:00Z"},
                        {"prompt_id": 101, "updated_at": "2025-12-17T15:30:00Z"},
                    ]
                }
            },
        )

        result = fetch_prompts_updated_time([100, 101])

        assert result == {100: "2025-12-18T10:00:00Z", 101: "2025-12-17T15:30:00Z"}
        # 验证调用参数 with_content=False
        call_args = mock_call_api.call_args
        assert call_args[0][2]["with_content"] is False

    def test_fetch_prompts_updated_time_api_no_prefix(self, settings, mocker):
        """测试未配置 BKAIDEV_URL_PREFIX 时抛出异常"""
        settings.BKAIDEV_USE_MOCK = False
        settings.BKAIDEV_URL_PREFIX = ""

        with pytest.raises(Exception):
            fetch_prompts_updated_time([1, 2])
