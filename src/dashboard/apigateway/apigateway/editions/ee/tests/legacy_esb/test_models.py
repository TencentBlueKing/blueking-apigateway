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
import datetime
import json
import operator
from unittest import mock

import pytest
from ddf import G
from pydantic import BaseModel

from apigateway.apps.esb.bkcore import models
from apigateway.legacy_esb import models as legacy_models

pytestmark = pytest.mark.django_db


class TestLegacyModelMigrator:
    class LegacyModel(BaseModel):
        id: int
        name: str
        description: str

    class NGModel(BaseModel):
        id: int
        name: str
        description: str

    @pytest.mark.parametrize(
        "src, dst, expected",
        [
            (
                {"id": 1, "name": "fake-name", "description": "test"},
                {"id": 1, "name": "fake-name", "description": "test"},
                False,
            ),
            (
                {"id": 1, "name": "name", "description": "test"},
                {"id": 1, "name": "other-name", "description": "test"},
                True,
            ),
        ],
    )
    def test_has_different_field_value(self, src, dst, expected):
        result = legacy_models.LegacyModelMigrator().has_different_field_value(
            TestLegacyModelMigrator.LegacyModel.parse_obj(src),
            TestLegacyModelMigrator.NGModel.parse_obj(dst),
            ["id", "name", "description"],
        )
        assert result is expected


def test_convert_is_official_to_data_type():
    assert 1 == legacy_models._convert_is_official_to_data_type(True)
    assert 3 == legacy_models._convert_is_official_to_data_type(False)


class TestComponentSystem:
    @pytest.fixture
    def fake_legacy_system(self, faker, unique_id):
        return G(
            legacy_models.ComponentSystem,
            name=unique_id,
            description=faker.word(),
            component_admin="admin1",
            interface_admin="admin2",
            comment=faker.text(),
            execute_timeout=30,
            query_timeout=10,
        )

    def test_clone_to_ng_obj(self, fake_legacy_system):
        expected = models.ComponentSystem(
            id=fake_legacy_system.id,
            name=fake_legacy_system.name,
            description=fake_legacy_system.description,
            comment=fake_legacy_system.comment,
            timeout=30,
            data_type=3,
            _maintainers="admin1;admin2",
        )

        assert fake_legacy_system.clone_to_ng_obj() == expected

    def test_update_ng_obj_fields(self, fake_legacy_system):
        ng_obj = G(models.ComponentSystem, id=fake_legacy_system.id, name=fake_legacy_system.name)
        expected = models.ComponentSystem(
            id=fake_legacy_system.id,
            name=fake_legacy_system.name,
            description=fake_legacy_system.description,
            comment=fake_legacy_system.comment,
            timeout=30,
            data_type=3,
            _maintainers="admin1;admin2",
        )

        result = fake_legacy_system.update_ng_obj_fields(ng_obj)
        assert result == expected

    def test_is_changed(self, fake_legacy_system):
        ng_obj = models.ComponentSystem(
            id=fake_legacy_system.id,
            name=fake_legacy_system.name,
            description=fake_legacy_system.description,
            comment=fake_legacy_system.comment,
            timeout=30,
            data_type=3,
            _maintainers="admin1;admin2",
        )
        assert fake_legacy_system.is_changed(ng_obj) is False

        ng_obj = models.ComponentSystem(
            id=fake_legacy_system.id,
            name=fake_legacy_system.name,
            description=fake_legacy_system.description,
            comment=fake_legacy_system.comment,
            timeout=10,
            data_type=3,
            _maintainers="admin1;admin2",
        )
        assert fake_legacy_system.is_changed(ng_obj) is True

    def test_is_official(self, fake_legacy_system):
        assert fake_legacy_system.is_official is False

    def test_data_type(self, fake_legacy_system):
        assert fake_legacy_system.data_type == 3

    @pytest.mark.parametrize(
        "query_timeout, execute_timeout, expected",
        [
            (None, None, None),
            (None, 10, None),
            (10, None, None),
            (10, 30, 30),
            (30, 10, 30),
            (0, 10, None),
        ],
    )
    def test_timeout(self, fake_legacy_system, query_timeout, execute_timeout, expected):
        fake_legacy_system.query_timeout = query_timeout
        fake_legacy_system.execute_timeout = execute_timeout

        assert fake_legacy_system.timeout == expected

    @pytest.mark.parametrize(
        "component_admin, interface_admin, expected",
        [
            ("admin1", "admin2", ["admin1", "admin2"]),
            ("admin1;admin2", "", ["admin1", "admin2"]),
            ("admin1", "admin1", ["admin1"]),
            ("admin2", "admin1", ["admin2", "admin1"]),
        ],
    )
    def test_maintainers(self, fake_legacy_system, component_admin, interface_admin, expected):
        fake_legacy_system.component_admin = component_admin
        fake_legacy_system.interface_admin = interface_admin

        assert fake_legacy_system.maintainers == expected


class TestESBChannel:
    @pytest.fixture
    def fake_legacy_system(self):
        return G(legacy_models.ComponentSystem)

    @pytest.fixture
    def fake_ng_system(self, fake_legacy_system):
        return fake_legacy_system.clone_to_ng_obj()

    @pytest.fixture
    def fake_legacy_channel(self, faker, unique_id, fake_legacy_system, fake_ng_system):
        legacy_channel = G(
            legacy_models.ESBChannel,
            description=faker.sentence(),
            path=f"/{unique_id}/",
            method="GET",
            component_system=fake_legacy_system,
            component_codename=faker.sentence(),
            name=faker.word(),
            is_active=True,
            timeout=30,
            comp_conf='{"a": "b"}',
            perm_level=1,
            is_hidden=False,
        )
        legacy_channel.ng_system = fake_ng_system
        return legacy_channel

    def test_clone_to_ng_obj(self, fake_legacy_channel):
        expected = models.ESBChannel(
            id=fake_legacy_channel.id,
            system=fake_legacy_channel.ng_system,
            method=fake_legacy_channel.method,
            path=fake_legacy_channel.path,
            name=fake_legacy_channel.name,
            description=fake_legacy_channel.description,
            component_codename=fake_legacy_channel.component_codename,
            permission_level="normal",
            timeout=30,
            config={"a": "b"},
            is_active=True,
            is_public=True,
            data_type=fake_legacy_channel.ng_system.data_type,
        )
        assert fake_legacy_channel.clone_to_ng_obj() == expected

    def test_update_ng_obj_fields(self, fake_legacy_channel):
        expected = models.ESBChannel(
            id=fake_legacy_channel.id,
            system=fake_legacy_channel.ng_system,
            method=fake_legacy_channel.method,
            path=fake_legacy_channel.path,
            name=fake_legacy_channel.name,
            description=fake_legacy_channel.description,
            component_codename=fake_legacy_channel.component_codename,
            permission_level="normal",
            timeout=30,
            config={"a": "b"},
            is_active=True,
            is_public=True,
            data_type=fake_legacy_channel.ng_system.data_type,
        )

        ng_obj = models.ESBChannel(id=fake_legacy_channel.id)
        result = fake_legacy_channel.update_ng_obj_fields(ng_obj)
        assert result == expected

    def test_is_changed(self, fake_legacy_channel):
        ng_obj = fake_legacy_channel.clone_to_ng_obj()
        assert fake_legacy_channel.is_changed(ng_obj) is False

        ng_obj.__dict__.update(
            {
                "method": "POST",
            }
        )
        assert fake_legacy_channel.is_changed(ng_obj) is True

    @pytest.mark.parametrize(
        "perm_level, expected",
        [
            (0, "unlimited"),
            (1, "normal"),
            (2, "sensitive"),
            (3, "special"),
        ],
    )
    def test_permission_level(self, fake_legacy_channel, perm_level, expected):
        fake_legacy_channel.perm_level = perm_level
        assert fake_legacy_channel.permission_level == expected

    @pytest.mark.parametrize(
        "comp_conf, expected",
        [
            (None, {}),
            ("", {}),
            ('{"a": "b"}', {"a": "b"}),
            ('[["a", "b"]]', {"a": "b"}),
        ],
    )
    def test_config(self, fake_legacy_channel, comp_conf, expected):
        fake_legacy_channel.comp_conf = comp_conf
        assert fake_legacy_channel.config == expected


class TestESBBuffetComponent:
    @pytest.fixture
    def fake_buffet_component(self):
        return G(
            legacy_models.ESBBuffetComponent,
            description="test",
            dest_url="http://1.1.1.1/echo/",
            dest_http_method="POST",
            favor_post_ctype="json",
            extra_headers=json.dumps({"a": "b"}),
            registed_path="/echo/",
            registed_http_method="POST",
            timeout_time=30,
        )

    def test_to_resource(self, fake_buffet_component):
        assert fake_buffet_component.to_resource() == {
            "name": "post_echo",
            "description": "test",
            "method": "POST",
            "path": "/echo/",
            "is_public": False,
            "allow_apply_permission": False,
            "labels": [],
            "proxy_type": "http",
            "proxy_configs": {
                "http": {
                    "method": "POST",
                    "path": "/echo/",
                    "timeout": 600,
                    "upstreams": {
                        "loadbalance": "roundrobin",
                        "hosts": [
                            {
                                "host": "http://1.1.1.1",
                                "weight": 100,
                            }
                        ],
                    },
                    "transform_headers": {
                        "set": {
                            "a": "b",
                            "Content-Type": "application/json",
                        }
                    },
                },
            },
            "auth_config": {
                "auth_verified_required": False,
                "app_verified_required": False,
                "resource_perm_required": False,
            },
            "disabled_stages": [],
        }

    @pytest.mark.parametrize(
        "method, path, expected",
        [
            ("GET", "/echo/", "get_echo"),
            ("POST", "/echo/", "post_echo"),
            ("get", "/echo/234/test/", "get_echo_234_test"),
            ("get", "/echo/{username}/test", "get_echo_username_test"),
        ],
    )
    def test_name(self, fake_buffet_component, method, path, expected):
        fake_buffet_component.registed_http_method = method
        fake_buffet_component.registed_path = path
        assert fake_buffet_component._name == expected

    @pytest.mark.parametrize(
        "system_timeout, buffet_timeout, expected",
        [
            (None, 10, 600),
            (None, None, 600),
            (10, 20, 20),
            (30, 10, 30),
            (30, None, 600),
        ],
    )
    def test_timeout(self, mocker, fake_buffet_component, system_timeout, buffet_timeout, expected):
        fake_buffet_component.system = G(
            legacy_models.ComponentSystem, query_timeout=system_timeout, execute_timeout=system_timeout
        )
        fake_buffet_component.timeout_time = buffet_timeout

        assert fake_buffet_component._timeout == expected

    @pytest.mark.parametrize(
        "method, expected",
        [
            ("GET", "GET"),
            ("POST", "POST"),
            ("_ORIG", "ANY"),
        ],
    )
    def test_convert_method(self, fake_buffet_component, method, expected):
        assert fake_buffet_component._convert_method(method) == expected

    @pytest.mark.parametrize(
        "dest_url, expected",
        [
            ("http://1.1.1.1/", "http://1.1.1.1"),
            ("https://1.1.1.1/", "https://1.1.1.1"),
            ("http://1.1.1.1/echo/test", "http://1.1.1.1"),
        ],
    )
    def test_backend_host(self, fake_buffet_component, dest_url, expected):
        fake_buffet_component.dest_url = dest_url
        assert fake_buffet_component._backend_host == expected

    @pytest.mark.parametrize(
        "dest_url, expected",
        [
            ("http://1.1.1.1/echo", "/echo"),
            ("https://1.1.1.1/echo/{username}", "/echo/{username}"),
        ],
    )
    def test_backend_path(self, fake_buffet_component, dest_url, expected):
        fake_buffet_component.dest_url = dest_url
        assert fake_buffet_component._backend_path == expected

    @pytest.mark.parametrize(
        "dest_http_method, mock_extra_headers, favor_post_ctype, expected",
        [
            ("GET", {"A": "b"}, "json", {"A": "b"}),
            ("POST", {"A": "b", "Content-Type": "test"}, "json", {"A": "b", "Content-Type": "test"}),
            ("POST", {"A": "b", "content-type": "test"}, "json", {"A": "b", "content-type": "test"}),
            ("POST", {"A": "b"}, "json", {"A": "b", "Content-Type": "application/json"}),
            ("POST", {"A": "b"}, "form", {"A": "b", "Content-Type": "application/x-www-form-urlencoded"}),
        ],
    )
    def test_enrich_extra_headers(
        self, mocker, fake_buffet_component, dest_http_method, mock_extra_headers, favor_post_ctype, expected
    ):
        mocker.patch(
            "apigateway.legacy_esb.models.ESBBuffetComponent._canonical_extra_headers",
            new_callable=mock.PropertyMock(return_value=mock_extra_headers),
        )
        fake_buffet_component.dest_http_method = dest_http_method
        fake_buffet_component.favor_post_ctype = favor_post_ctype

        assert fake_buffet_component._enrich_extra_headers() == expected

    @pytest.mark.parametrize(
        "extra_headers, expected",
        [
            (None, {}),
            ("", {}),
            (json.dumps({"a": "b"}), {"a": "b"}),
            (json.dumps({"a-345": "b"}), {"a-345": "b"}),
            (json.dumps({"content_type": "application/json"}), {"content-type": "application/json"}),
            (json.dumps({"content-type": "application/json"}), {"content-type": "application/json"}),
            (json.dumps({"Content-Type": "application/json"}), {"Content-Type": "application/json"}),
            (json.dumps({"Content_Type": "application/json"}), {"Content-Type": "application/json"}),
        ],
    )
    def test_canonical_extra_headers(self, fake_buffet_component, extra_headers, expected):
        fake_buffet_component.extra_headers = extra_headers
        assert fake_buffet_component._canonical_extra_headers == expected


class TestComponentAPIDoc:
    @pytest.fixture
    def fake_legacy_doc(self, faker, unique_id):
        channel = G(legacy_models.ESBChannel, path=f"/{unique_id}/")
        return G(
            legacy_models.ComponentAPIDoc,
            component_id=channel.id,
            doc_md=json.dumps(
                {
                    "zh-hans": "中文文档",
                    "en": "english document",
                }
            ),
        )

    def test_split_doc_by_language(self, fake_legacy_doc):
        result = fake_legacy_doc.split_doc_by_language()
        assert sorted(result, key=operator.itemgetter("language")) == [
            {
                "component_id": fake_legacy_doc.component_id,
                "language": "en",
                "content": "english document",
                "content_md5": "378807031f9afc4a23b176d617af2a81",
            },
            {
                "component_id": fake_legacy_doc.component_id,
                "language": "zh-hans",
                "content": "中文文档",
                "content_md5": "f6d3aaa4e3aa9cf7674f8a2331190d64",
            },
        ]


class TestAppComponentPerm:
    @pytest.fixture
    def fake_legacy_permission(self, faker, unique_id):
        return G(
            legacy_models.AppComponentPerm,
            bk_app_code=unique_id,
            component_id=faker.pyint(),
        )

    def test_clone_to_ng_obj(self, fake_legacy_permission):
        assert fake_legacy_permission.clone_to_ng_obj() == models.AppComponentPermission(
            id=fake_legacy_permission.id,
            bk_app_code=fake_legacy_permission.bk_app_code,
            component_id=fake_legacy_permission.component_id,
            expires=fake_legacy_permission.expires,
        )

    def test_update_ng_obj_fields(self, fake_legacy_permission):
        ng_permission = models.AppComponentPermission(id=fake_legacy_permission.id)
        result = fake_legacy_permission.update_ng_obj_fields(ng_permission)
        assert result == models.AppComponentPermission(
            id=fake_legacy_permission.id,
            bk_app_code=fake_legacy_permission.bk_app_code,
            component_id=fake_legacy_permission.component_id,
            expires=fake_legacy_permission.expires,
        )

    def test_is_changed(self, fake_legacy_permission):
        ng_obj = fake_legacy_permission.clone_to_ng_obj()
        assert fake_legacy_permission.is_changed(ng_obj) is False

        ng_obj.__dict__.update(
            {
                "expires": datetime.datetime.now(),
            }
        )
        assert fake_legacy_permission.is_changed(ng_obj) is True


class TestDocCategory:
    @pytest.fixture
    def fake_category(self, faker, unique_id):
        return G(legacy_models.SystemDocCategory, name=unique_id)

    def test_is_official(self, fake_category):
        assert fake_category.is_official is False

        fake_category.name = "默认分类"
        assert fake_category.is_official is True

    def test_clone_to_ng_obj(self, fake_category):
        assert fake_category.clone_to_ng_obj() == models.DocCategory(
            id=fake_category.id,
            name=fake_category.name,
            priority=fake_category._ng_priority,
            data_type=3,
        )

    def test_update_ng_obj_fields(self, fake_category):
        ng_category = models.DocCategory(id=fake_category.id)
        result = fake_category.update_ng_obj_fields(ng_category)
        assert result == models.DocCategory(
            id=fake_category.id,
            name=fake_category.name,
            priority=fake_category._ng_priority,
            data_type=3,
        )

    def test_is_changed(self, fake_category):
        ng_category = fake_category.clone_to_ng_obj()
        assert fake_category.is_changed(ng_category) is False

        ng_category.name = "test"
        assert fake_category.is_changed(ng_category) is True

    def test_data_type(self, fake_category):
        assert fake_category.data_type == 3
