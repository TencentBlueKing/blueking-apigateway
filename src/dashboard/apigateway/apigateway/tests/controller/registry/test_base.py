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

from apigateway.controller.registry.base import Registry


class TestRegistry:
    """Test Registry abstract class"""

    @pytest.fixture
    def test_registry_class(self):
        """Fixture for a complete test registry implementation"""

        class TestRegistry(Registry):
            registry_type = "test"

            def apply_resource(self, resource):
                pass

            def sync_resources_by_key_prefix(self, resources):
                pass

            def delete_resources_by_key_prefix(self):
                pass

            def iter_by_type(self, resource_type):
                pass

        return TestRegistry

    def test_registry_is_abstract(self):
        """Test that Registry cannot be instantiated directly"""
        with pytest.raises(TypeError) as exc_info:
            Registry("/test")
        assert "abstract" in str(exc_info.value).lower()

    def test_registry_key_prefix_with_trailing_slash(self, test_registry_class):
        """Test registry initialization with trailing slash"""
        registry = test_registry_class("/test/")
        assert registry.key_prefix == "/test/"

    def test_registry_key_prefix_without_trailing_slash(self, test_registry_class):
        """Test registry initialization without trailing slash adds one"""
        registry = test_registry_class("/test")
        assert registry.key_prefix == "/test/"

    def test_get_kind_key_prefix(self, test_registry_class):
        """Test _get_kind_key_prefix method"""
        registry = test_registry_class("/gateway/test-gateway/prod/")
        kind_prefix = registry._get_kind_key_prefix("service")
        assert kind_prefix == "/gateway/test-gateway/prod/service/"

    def test_get_key(self, test_registry_class):
        """Test _get_key method"""
        registry = test_registry_class("/gateway/test-gateway/prod/")
        key = registry._get_key("service", "service-1")
        assert key == "/gateway/test-gateway/prod/service/service-1"

    def test_abstract_methods_must_be_implemented(self):
        """Test that all abstract methods must be implemented"""

        # Missing apply_resource
        with pytest.raises(TypeError):

            class IncompleteRegistry1(Registry):
                registry_type = "test"

                def sync_resources_by_key_prefix(self, resources):
                    pass

                def delete_resources_by_key_prefix(self):
                    pass

                def iter_by_type(self, resource_type):
                    pass

            IncompleteRegistry1("/test")

        # Missing sync_resources_by_key_prefix
        with pytest.raises(TypeError):

            class IncompleteRegistry2(Registry):
                registry_type = "test"

                def apply_resource(self, resource):
                    pass

                def delete_resources_by_key_prefix(self):
                    pass

                def iter_by_type(self, resource_type):
                    pass

            IncompleteRegistry2("/test")

    def test_complete_implementation(self):
        """Test a complete implementation of Registry"""

        class CompleteRegistry(Registry):
            registry_type = "complete"

            def apply_resource(self, resource):
                return True

            def sync_resources_by_key_prefix(self, resources):
                return []

            def delete_resources_by_key_prefix(self):
                pass

            def iter_by_type(self, resource_type):
                return []

        registry = CompleteRegistry("/test/")
        assert registry.registry_type == "complete"
        assert registry.key_prefix == "/test/"

    @pytest.mark.parametrize(
        "kind,id,expected",
        [
            ("service", "svc-1", "/prefix/service/svc-1"),
            ("route", "route-1", "/prefix/route/route-1"),
            ("ssl", "ssl-1", "/prefix/ssl/ssl-1"),
        ],
    )
    def test_get_key_with_different_kinds(self, test_registry_class, kind, id, expected):
        """Test _get_key with different resource kinds"""
        registry = test_registry_class("/prefix/")
        key = registry._get_key(kind, id)
        assert key == expected
