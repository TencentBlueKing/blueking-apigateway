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
import pytest
from ddf import G

from apigateway.apps.label.models import APILabel
from apigateway.biz.resource.importer import (
    ResourceDataConvertor,
    ResourceImportValidator,
    ResourcesImporter,
)
from apigateway.core.models import Backend, Resource


class TestResourceDataConvertor:
    def test_convert(self, fake_gateway, faker):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")

        backend_1 = G(Backend, gateway=fake_gateway, name="foo")
        backend_2 = G(Backend, gateway=fake_gateway, name="default")

        resources = [
            {
                "id": resource_1.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "foo",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
            {
                "name": "test2_1",
                "method": "POST",
                "path": "/test2",
                "backend_config": {
                    "method": "POST",
                    "path": "/backend/test2",
                },
            },
        ]
        convertor = ResourceDataConvertor(fake_gateway, resources)
        result = convertor.convert()

        assert result[0].resource == resource_1
        assert result[0].backend == backend_1
        assert result[0].backend_config.path == "/backend/test1"

        assert result[1].resource == resource_2
        assert result[1].backend == backend_2
        assert result[1].backend_config.path == "/backend/test2"

    def test_convert__error(self, fake_resource):
        resources = [
            {
                "id": fake_resource.id,
                "name": "test1",
                "method": "GET",
                "path": "/test1",
                "backend_name": "not_exist",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test1",
                },
            },
        ]

        convertor = ResourceDataConvertor(fake_resource.gateway, resources)
        with pytest.raises(ValueError):
            convertor.convert()

    def test_get_resource_obj(self, fake_resource):
        resource_id_to_obj = {fake_resource.id: fake_resource}
        resource_key_to_resource_obj = {f"{fake_resource.method}:{fake_resource.path}": fake_resource}

        convertor = ResourceDataConvertor(fake_resource.gateway, [])

        resource_obj = convertor._get_resource_obj(
            {"id": fake_resource.id}, resource_id_to_obj, resource_key_to_resource_obj
        )
        assert resource_obj == fake_resource

        resource_obj = convertor._get_resource_obj(
            {"method": fake_resource.method, "path": fake_resource.path},
            resource_id_to_obj,
            resource_key_to_resource_obj,
        )
        assert resource_obj == fake_resource

        with pytest.raises(ValueError):
            convertor._get_resource_obj({"id": 0}, resource_id_to_obj, resource_key_to_resource_obj)


class TestResourceImportValidator:
    def test_validate(self, fake_gateway, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, True)
        validator.validate()

    def test_get_unchanged_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway)
        resource_2 = G(Resource, gateway=fake_gateway)

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(deep=True),
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, True)
        result = validator._get_unchanged_resources()
        assert result == []

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        result = validator._get_unchanged_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2.id

    def test_get_unspecified_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway)
        resource_2 = G(Resource, gateway=fake_gateway)

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
            fake_resource_data.copy(deep=True),
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        result = validator.get_unspecified_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2.id

    def test_validate_resources__error(self, fake_resource, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
            fake_resource_data.copy(update={"resource": fake_resource}, deep=True),
        ]

        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, True)
        with pytest.raises(ValueError):
            validator._validate_resources()

    def test_validate_method_path__error(self, fake_resource, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(update={"method": fake_resource.method, "path": fake_resource.path}, deep=True),
        ]
        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, False)
        with pytest.raises(ValueError):
            validator._validate_method_path()

        resource_data_list = [
            fake_resource_data.copy(update={"method": "GET", "path": "/foo"}, deep=True),
            fake_resource_data.copy(update={"method": "GET", "path": "/foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_resource.gateway, resource_data_list, True)
        with pytest.raises(ValueError):
            validator._validate_method_path()

    def test_validate_method__error(self, fake_gateway, fake_resource_data):
        G(Resource, gateway=fake_gateway, method="GET", path="/foo")

        resource_data_list = [
            fake_resource_data.copy(update={"method": "ANY", "path": "/foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        with pytest.raises(ValueError):
            validator._validate_method()

    def test_validate_name__error(self, fake_gateway, fake_resource_data):
        G(Resource, gateway=fake_gateway, name="foo")
        resource_data_list = [
            fake_resource_data.copy(update={"name": "foo"}, deep=True),
        ]
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        with pytest.raises(ValueError):
            validator._validate_name()

    def test_validate_match_subpath(self, fake_gateway, fake_resource_data):
        resource_data = fake_resource_data.copy(deep=True)
        resource_data.match_subpath = True
        resource_data.backend_config.match_subpath = False

        resource_data_list = [
            resource_data,
        ]

        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        with pytest.raises(ValueError):
            validator._validate_match_subpath()

    def test_validate_resource_count__error(self, settings, fake_resource, fake_resource_data):
        settings.API_GATEWAY_RESOURCE_LIMITS = {
            "max_resource_count_per_gateway_whitelist": {"foo": 2},
            "max_resource_count_per_gateway": 1000,
        }
        resource_data_list = [
            fake_resource_data.copy(deep=True),
            fake_resource_data.copy(deep=True),
        ]
        fake_gateway = fake_resource.gateway
        fake_gateway.name = "foo"
        validator = ResourceImportValidator(fake_gateway, resource_data_list, False)
        with pytest.raises(ValueError):
            validator._validate_resource_count()


class TestResourcesImporter:
    def test_init__error(self, fake_gateway, fake_resource_data):
        resource_data_list = [
            fake_resource_data.copy(deep=True),
            fake_resource_data.copy(deep=True),
        ]

        with pytest.raises(ValueError):
            ResourcesImporter(fake_gateway, resource_data_list)

    def test_from_resources(self, fake_gateway):
        G(Backend, gateway=fake_gateway, name="foo")
        resources = [
            {
                "name": "test",
                "method": "GET",
                "path": "/test",
                "backend_name": "foo",
                "backend_config": {
                    "method": "GET",
                    "path": "/backend/test",
                },
            }
        ]

        importer = ResourcesImporter.from_resources(fake_gateway, resources)
        assert len(importer.resource_data_list) == 1

    def test_import_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")
        resource_2_id = resource_2.id

        G(Backend, gateway=fake_gateway, name="default")

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1, "name": "foo1", "path": "/foo1"}, deep=True),
            fake_resource_data.copy(update={"name": "foo2", "path": "/foo2"}, deep=True),
        ]
        importer = ResourcesImporter(
            fake_gateway,
            resource_data_list,
            need_delete_unspecified_resources=True,
        )
        importer.import_resources()

        resource_ids = list(Resource.objects.filter(gateway=fake_gateway).values_list("id", flat=True))
        assert len(resource_ids) == 2
        assert resource_2_id not in resource_ids
        assert resource_1.id in resource_ids

    @pytest.mark.parametrize(
        "selected_resources, expected",
        [
            (
                None,
                2,
            ),
            (
                [{"name": "test1"}],
                1,
            ),
            (
                [{"name": "test1"}, {"name": "test2"}],
                2,
            ),
            (
                [{"name": "test3"}, {"name": "test4"}],
                0,
            ),
        ],
    )
    def test_filter_selected_resource_data_list(self, fake_gateway, fake_resource_data, selected_resources, expected):
        resource_data_list = [
            fake_resource_data.copy(update={"name": "test1", "method": "GET"}, deep=True),
            fake_resource_data.copy(update={"name": "test2", "method": "POST"}, deep=True),
        ]
        importer = ResourcesImporter(fake_gateway, [], selected_resources=None)
        result = importer._filter_selected_resource_data_list(selected_resources, resource_data_list)
        assert len(result) == expected

    def test_delete_unspecified_resources(self, fake_gateway, fake_resource_data):
        resource_1 = G(Resource, gateway=fake_gateway, name="test1", method="GET", path="/test1")
        resource_2 = G(Resource, gateway=fake_gateway, name="test2", method="POST", path="/test2")
        resource_2_id = resource_2.id

        resource_data_list = [
            fake_resource_data.copy(update={"resource": resource_1}, deep=True),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list, need_delete_unspecified_resources=True)
        result = importer._delete_unspecified_resources()
        assert len(result) == 1
        assert result[0]["id"] == resource_2_id
        assert not Resource.objects.filter(id=resource_2_id).exists()

    def test_create_not_exist_labels(self, fake_gateway, fake_resource_data):
        G(APILabel, gateway=fake_gateway, name="label1")

        resource_data_list = [
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1", "label2"]}, "name": "foo1", "method": "GET"}, deep=True
            ),
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1", "label3"]}, "name": "foo2", "method": "POST"}, deep=True
            ),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list)
        importer._create_not_exist_labels()

        assert APILabel.objects.filter(gateway=fake_gateway).count() == 3

    def test_complete_label_ids(self, fake_gateway, fake_resource_data):
        label_1 = G(APILabel, gateway=fake_gateway, name="label1")
        label_2 = G(APILabel, gateway=fake_gateway, name="label2")

        resource_data_list = [
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label1"]}, "name": "foo1", "method": "GET"}, deep=True
            ),
            fake_resource_data.copy(
                update={"metadata": {"labels": ["label2"]}, "name": "foo2", "method": "POST"}, deep=True
            ),
        ]

        importer = ResourcesImporter(fake_gateway, resource_data_list)
        importer._complete_label_ids()

        assert resource_data_list[0].label_ids == [label_1.id]
        assert resource_data_list[1].label_ids == [label_2.id]
