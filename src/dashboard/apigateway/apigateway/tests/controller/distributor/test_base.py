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

from apigateway.controller.distributor.base import BaseDistributor


class TestBaseDistributor:
    """Test BaseDistributor abstract class"""

    def test_base_distributor_is_abstract(self):
        """Test that BaseDistributor cannot be instantiated directly"""
        with pytest.raises(TypeError) as exc_info:
            BaseDistributor()
        assert "abstract" in str(exc_info.value).lower()

    def test_distribute_must_be_implemented(self, mocker):
        """Test that distribute method must be implemented"""

        class IncompleteDistributor(BaseDistributor):
            def revoke(self, release, release_task_id=None, publish_id=None):
                return True, "revoked"

        # Should not be able to instantiate without implementing distribute
        with pytest.raises(TypeError):
            IncompleteDistributor()

    def test_revoke_must_be_implemented(self, mocker):
        """Test that revoke method must be implemented"""

        class IncompleteDistributor(BaseDistributor):
            def distribute(self, release, release_task_id=None, publish_id=None):
                return True, "distributed"

        # Should not be able to instantiate without implementing revoke
        with pytest.raises(TypeError):
            IncompleteDistributor()

    def test_complete_implementation(self, mocker):
        """Test a complete implementation of BaseDistributor"""

        class CompleteDistributor(BaseDistributor):
            def distribute(self, release_task_id: str, publish_id: int):
                return True, "distributed"

            def revoke(self, release_task_id: str, publish_id: int):
                return True, "revoked"

        # Should be able to instantiate with all methods implemented
        distributor = CompleteDistributor()
        assert distributor is not None

        # Test the methods
        mock_release = mocker.Mock()
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)
        assert success is True
        assert message == "distributed"

        success, message = distributor.revoke(release_task_id="test-task-id", publish_id=123)
        assert success is True
        assert message == "revoked"
