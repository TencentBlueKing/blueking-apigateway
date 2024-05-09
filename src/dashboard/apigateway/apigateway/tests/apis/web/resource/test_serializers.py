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
import datetime
import json

import pytest
from dateutil.tz import tzutc
from ddf import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.resource.serializers import (
    BackendPathCheckInputSLZ,
    HttpBackendConfigSLZ,
    ResourceDataImportSLZ,
    ResourceExportOutputSLZ,
    ResourceImportInputSLZ,
    ResourceInputSLZ,
    ResourceListOutputSLZ,
)
from apigateway.core.models import (
    Backend,
    Proxy,
    Resource,
    Stage,
)


class TestResourceListOutputSLZ:
    @pytest.mark.parametrize(
        "context, expected",
        [
            (
                {"latest_version_created_time": None},
                False,
            ),
            (
                {"latest_version_created_time": datetime.datetime(2020, 1, 1, tzinfo=tzutc())},
                True,
            ),
            (
                {"latest_version_created_time": datetime.datetime(2220, 1, 1, tzinfo=tzutc())},
                False,
            ),
        ],
    )
    def test_has_updated(self, fake_resource, context, expected):
        slz = ResourceListOutputSLZ(fake_resource, context=context)
        assert slz.get_has_updated(fake_resource) is expected


class TestHttpBackendConfigSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "method": "GET",
                    "path": "/test",
                },
                {
                    "method": "GET",
                    "path": "/test",
                    "legacy_upstreams": None,
                    "legacy_transform_headers": None,
                },
            ),
            (
                {
                    "method": "GET",
                    "path": "/test",
                    "legacy_upstreams": None,
                    "legacy_transform_headers": None,
                },
                {
                    "method": "GET",
                    "path": "/test",
                    "legacy_upstreams": None,
                    "legacy_transform_headers": None,
                },
            ),
            (
                {
                    "method": "GET",
                    "path": "/test",
                    "legacy_upstreams": {
                        "hosts": [{"host": "http://{env.foo}", "weight": 20}],
                        "loadbalance": "roundrobin",
                    },
                    "legacy_transform_headers": {"set": {"x-token": "test"}, "delete": ["x-token"]},
                },
                {
                    "method": "GET",
                    "path": "/test",
                    "legacy_upstreams": {
                        "hosts": [{"host": "http://{env.foo}", "weight": 20}],
                        "loadbalance": "roundrobin",
                    },
                    "legacy_transform_headers": {"set": {"x-token": "test"}, "delete": ["x-token"]},
                },
            ),
        ],
    )
    def test_validate(self, data, expected):
        slz = HttpBackendConfigSLZ(data=data)
        slz.is_valid(raise_exception=True)
        assert slz.data == expected


class TestResourceInputSLZ:
    @pytest.mark.parametrize(
        "description_en, expected",
        [
            ("test", "test"),
            ("", None),
            (None, None),
        ],
    )
    def test_validate_description_en(self, description_en, expected):
        slz = ResourceInputSLZ()
        result = slz.validate_description_en(description_en)
        assert result == expected

    def test_validate(self, fake_resource, faker):
        fake_gateway = fake_resource.gateway
        backend = G(Backend, gateway=fake_gateway)
        data = {
            "name": "test",
            "description": faker.pystr(),
            "method": "GET",
            "path": "/test/",
            "match_subpath": False,
            "is_public": True,
            "allow_apply_permission": True,
            "auth_config": {
                "auth_verified_required": True,
                "app_verified_required": True,
                "resource_perm_required": True,
            },
            "backend": {
                "id": backend.id,
                "config": {
                    "method": "GET",
                    "path": "/test",
                    "match_subpath": False,
                    "timeout": 0,
                },
            },
            "label_ids": [],
        }

        slz = ResourceInputSLZ(
            data=data,
            context={
                "gateway": fake_gateway,
                "stages": Stage.objects.filter(gateway=fake_gateway),
            },
        )
        slz.is_valid(raise_exception=True)

        assert slz.validated_data["backend"] == backend
        assert slz.validated_data["resource"] is None

        slz = ResourceInputSLZ(
            fake_resource,
            data=data,
            context={
                "gateway": fake_gateway,
                "stages": Stage.objects.filter(gateway=fake_gateway),
            },
        )
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["resource"] == fake_resource

        invalid_name_data = data.copy()
        invalid_name_data["name"] = "test-"
        slz = ResourceInputSLZ(
            fake_resource,
            data=invalid_name_data,
            context={
                "gateway": fake_gateway,
                "stages": Stage.objects.filter(gateway=fake_gateway),
            },
        )
        assert not slz.is_valid(raise_exception=False)

    def test_validate_method(self, fake_gateway):
        r1 = G(Resource, gateway=fake_gateway, method="POST", path="/foo")
        r2 = G(Resource, gateway=fake_gateway, method="ANY", path="/bar")

        with pytest.raises(ValidationError):
            slz = ResourceInputSLZ()
            slz._validate_method(fake_gateway, "/foo", "ANY")

        with pytest.raises(ValidationError):
            slz = ResourceInputSLZ()
            slz._validate_method(fake_gateway, "/bar", "GET")

        slz = ResourceInputSLZ(r1)
        slz._validate_method(fake_gateway, "/foo", "ANY")

        slz = ResourceInputSLZ(r2)
        slz._validate_method(fake_gateway, "/bar", "GET")

    @pytest.mark.parametrize(
        "data",
        [
            {"match_subpath": True, "backend": {"config": {"match_subpath": False}}},
            {"match_subpath": False, "backend": {"config": {"match_subpath": True}}},
        ],
    )
    def test_validate_match_subpath__error(self, data):
        slz = ResourceInputSLZ()
        with pytest.raises(ValidationError):
            slz._validate_match_subpath(data)

    def test_validate_backend_id(self, fake_gateway):
        backend = G(Backend, gateway=fake_gateway)

        slz = ResourceInputSLZ()
        with pytest.raises(ValidationError):
            slz._validate_backend_id(fake_gateway, 0)

        result = slz._validate_backend_id(fake_gateway, backend.id)
        assert result == backend


class TestResourceDataImportSLZ:
    @pytest.mark.parametrize(
        "description_en, expected",
        [
            ("test", "test"),
            ("", None),
            (None, None),
        ],
    )
    def validate_description_en(self, description_en, expected):
        slz = ResourceDataImportSLZ()
        result = slz.validate_description_en(description_en)
        assert result == expected


class TestResourceImportInputSLZ:
    def test_validate(self, fake_stage, fake_resource_swagger):
        data = {
            "content": fake_resource_swagger,
            "selected_resources": [{"name": "foo"}],
            "delete": True,
        }
        slz = ResourceImportInputSLZ(
            data=data,
            context={
                "stages": [fake_stage],
                "exist_label_names": [],
            },
        )
        slz.is_valid(raise_exception=True)
        assert len(slz.validated_data["resources"]) == 1

    @pytest.mark.parametrize(
        "content",
        [
            "foo",
            json.dumps({"foo": "bar"}),
        ],
    )
    def test_validate_content__error(self, content):
        slz = ResourceImportInputSLZ()
        with pytest.raises(ValidationError):
            slz._validate_content(content)


class TestResourceExportOutputSLZ:
    def test_to_representation(self, fake_resource, echo_plugin_resource_binding):
        proxies = {proxy.resource_id: proxy for proxy in Proxy.objects.filter(resource__in=[fake_resource])}
        backends = {backend.id: backend for backend in Backend.objects.filter(gateway=fake_resource.gateway)}

        slz = ResourceExportOutputSLZ(
            [fake_resource],
            many=True,
            context={
                "labels": {fake_resource.id: [{"id": 1, "name": "foo"}]},
                "proxies": proxies,
                "backends": backends,
                "auth_configs": {fake_resource.id: {"foo": True}},
                "resource_id_to_plugin_bindings": {fake_resource.id: [echo_plugin_resource_binding]},
            },
        )
        assert len(slz.data) == 1


class TestBackendPathCheckInputSLZ:
    def test_validate(self):
        data = {
            "path": "/foo/{color}",
            "backend_id": 1,
            "backend_path": "/bar/{color}",
        }

        slz = BackendPathCheckInputSLZ(data=data, context={"stages": []})
        slz.is_valid(raise_exception=True)

        assert slz.validated_data["path"] == data["path"]
        assert slz.validated_data["backend_config"]["path"] == data["backend_path"]
