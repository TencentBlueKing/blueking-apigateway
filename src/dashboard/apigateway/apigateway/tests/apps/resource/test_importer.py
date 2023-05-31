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
import json

import pytest

from apigateway.apps.resource.importer import ResourceImportValidator, ResourcesImporter
from apigateway.common.error_codes import APIError

pytestmark = pytest.mark.django_db


class TestResourceImportValidator:
    @pytest.mark.parametrize(
        "importing_resources, resource_doc_language, expected",
        [
            (
                [
                    {
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "test",
                        "labels": ["pet"],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
                        "proxy_type": "mock",
                        "proxy_configs": {
                            "mock": {
                                "code": 200,
                                "body": "test",
                                "headers": {
                                    "X-Token": "token",
                                },
                            }
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                    },
                ],
                "zh",
                [
                    {
                        "id": None,
                        "method": "GET",
                        "path": "/http/get/mapping/{userId}",
                        "name": "http_get_mapping_userid",
                        "description": "test",
                        "labels": ["pet"],
                        "is_public": True,
                        "allow_apply_permission": True,
                        "match_subpath": False,
                        "proxy_type": "mock",
                        "proxy_configs": {
                            "backend_config_type": "default",
                            "backend_service_id": None,
                            "mock": {
                                "code": 200,
                                "body": "test",
                                "headers": {
                                    "X-Token": "token",
                                },
                            },
                        },
                        "auth_config": {
                            "auth_verified_required": True,
                        },
                        "disabled_stages": [],
                        "resource_doc_id": None,
                        "resource_doc_language": "zh",
                    }
                ],
            )
        ],
    )
    def test_validate(self, mocker, fake_gateway, importing_resources, resource_doc_language, expected):
        validator = ResourceImportValidator(
            fake_gateway, importing_resources, resource_doc_language=resource_doc_language
        )

        mocker.patch("apigateway.apps.resource.importer.Stage.objects.get_names", return_value=["prod"])
        mocker.patch("apigateway.apps.resource.importer.ResourceDoc.objects.get_doc_key_to_id", return_value={})

        result = validator.validate()

        assert result == expected

    @pytest.mark.parametrize(
        "mock_resource_path_method_to_id, importing_resources, expected",
        [
            (
                {
                    "/echo/": {
                        "GET": 1,
                        "POST": 2,
                    },
                },
                [
                    {"method": "GET", "path": "/echo/"},
                ],
                [
                    {"id": 1, "method": "GET", "path": "/echo/"},
                ],
            ),
            (
                {
                    "/echo/": {
                        "GET": 1,
                        "POST": 2,
                    },
                },
                [
                    {"method": "DELETE", "path": "/echo/"},
                ],
                [
                    {"id": None, "method": "DELETE", "path": "/echo/"},
                ],
            ),
        ],
    )
    def test_enrich_resource_id(
        self, mocker, fake_gateway, mock_resource_path_method_to_id, importing_resources, expected
    ):
        validator = ResourceImportValidator(fake_gateway, importing_resources)

        mocker.patch.object(
            validator,
            "_get_resource_path_method_to_id",
            return_value=mock_resource_path_method_to_id,
        )

        validator._enrich_resource_id()
        assert validator._importing_resources == expected

    @pytest.mark.parametrize(
        "existed_resource_id_to_fields, importing_resource, expected",
        [
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"id": 1}, {"id": 2}],
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
            ),
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"id": 1}],
                {1: {"id": 1, "name": "a"}},
            ),
        ],
    )
    def test_remove_unspecified_resources(
        self, fake_gateway, existed_resource_id_to_fields, importing_resource, expected
    ):
        validator = ResourceImportValidator(fake_gateway, importing_resource)
        validator._remove_unspecified_resources(existed_resource_id_to_fields)
        assert existed_resource_id_to_fields == expected

    @pytest.mark.parametrize(
        "importing_resources, mock_resource_id_to_fields",
        [
            (
                [
                    {},
                ],
                {},
            ),
            (
                [
                    {},
                    {"id": 1, "method": "GET", "path": "/echo/", "name": "echo"},
                ],
                {
                    1: {"id": 1, "method": "POST", "path": "/echo/", "name": "echo"},
                    2: {"id": 2, "method": "GET", "path": "/echo/2/", "name": "echo"},
                },
            ),
        ],
    )
    def test_validate_resource_id(self, mocker, fake_gateway, importing_resources, mock_resource_id_to_fields):
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.filter_id_to_fields",
            return_value=mock_resource_id_to_fields,
        )
        validator = ResourceImportValidator(fake_gateway, importing_resources)
        assert validator._validate_resource_id() is None

    @pytest.mark.parametrize(
        "importing_resources, mock_resource_id_to_fields",
        [
            (
                [
                    {"id": 1, "method": "GET", "path": "/echo/", "name": "echo"},
                    {"id": 1, "method": "GET", "path": "/echo/", "name": "echo"},
                ],
                {
                    1: {"id": 1},
                },
            ),
            (
                [
                    {"id": 1, "method": "GET", "path": "/echo/", "name": "echo"},
                ],
                {
                    2: {"id": 2},
                },
            ),
        ],
    )
    def test_validate_resource_id_error(self, mocker, fake_gateway, importing_resources, mock_resource_id_to_fields):
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.filter_id_to_fields",
            return_value=mock_resource_id_to_fields,
        )
        validator = ResourceImportValidator(fake_gateway, importing_resources)
        with pytest.raises(APIError):
            validator._validate_resource_id()

    @pytest.mark.parametrize(
        "mock_resource_id_to_fields, importing_resources, expected_error",
        [
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/a/"},
                    2: {"id": 2, "method": "POST", "path": "/b/"},
                },
                [
                    {"method": "GET", "path": "/c/"},
                    {"method": "DELETE", "path": "/c/"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/a/"},
                    2: {"id": 2, "method": "POST", "path": "/b/"},
                },
                [
                    {"id": 1, "method": "GET", "path": "/a/"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/a/"},
                    2: {"id": 2, "method": "POST", "path": "/b/"},
                },
                [
                    {"id": 1, "method": "GET", "path": "/c/"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/a/"},
                    2: {"id": 2, "method": "POST", "path": "/b/"},
                },
                [
                    {"method": "GET", "path": "/a/"},
                ],
                APIError,
            ),
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/a/"},
                    2: {"id": 2, "method": "POST", "path": "/b/"},
                },
                [
                    {"id": 2, "method": "GET", "path": "/a/"},
                ],
                APIError,
            ),
        ],
    )
    def test_validate_method_path(
        self, mocker, fake_gateway, mock_resource_id_to_fields, importing_resources, expected_error
    ):
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.filter_id_to_fields",
            return_value=mock_resource_id_to_fields,
        )
        validator = ResourceImportValidator(fake_gateway, importing_resources)

        if not expected_error:
            assert validator._validate_method_path() is None
            return

        with pytest.raises(expected_error):
            validator._validate_method_path()

    @pytest.mark.parametrize(
        "mock_resource_id_to_fields, importing_resources, expected_error",
        [
            (
                {
                    1: {"id": 1, "name": "a"},
                    2: {"id": 2, "name": "b"},
                },
                [
                    {"name": "c"},
                    {"name": "d"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "name": "a"},
                    2: {"id": 2, "name": "b"},
                },
                [
                    {"id": 1, "name": "a"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "name": "a"},
                    2: {"id": 2, "name": "b"},
                },
                [
                    {"id": 1, "name": "c"},
                ],
                None,
            ),
            (
                {
                    1: {"id": 1, "name": "a"},
                    2: {"id": 2, "name": "b"},
                },
                [
                    {"name": "a"},
                ],
                APIError,
            ),
            (
                {
                    1: {"id": 1, "name": "a"},
                    2: {"id": 2, "name": "b"},
                },
                [
                    {"id": 2, "name": "a"},
                ],
                APIError,
            ),
        ],
    )
    def test_validate_name(
        self, mocker, fake_gateway, mock_resource_id_to_fields, importing_resources, expected_error
    ):
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.filter_id_to_fields",
            return_value=mock_resource_id_to_fields,
        )
        validator = ResourceImportValidator(fake_gateway, importing_resources)

        if not expected_error:
            assert validator._validate_resource_name() is None
            return

        with pytest.raises(expected_error):
            validator._validate_resource_name()

    @pytest.mark.parametrize(
        "mock_resource_id_to_fields, importing_resources, max_resource_count, expected_error",
        [
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"name": "c"}],
                5,
                None,
            ),
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"id": 1}, {"id": 2}, {"name": "c"}, {"name": "d"}],
                5,
                None,
            ),
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"id": 1}, {"id": 2}, {"name": "c"}, {"name": "d"}, {"name": "e"}, {"name": "f"}],
                5,
                APIError,
            ),
            (
                {1: {"id": 1, "name": "a"}, 2: {"id": 2, "name": "b"}},
                [{"name": "a-1"}, {"name": "a-2"}, {"name": "c"}, {"name": "d"}, {"name": "e"}, {"name": "f"}],
                5,
                APIError,
            ),
        ],
    )
    def test_validate_resource_count(
        self,
        settings,
        mocker,
        fake_gateway,
        mock_resource_id_to_fields,
        importing_resources,
        max_resource_count,
        expected_error,
    ):
        settings.MAX_RESOURCE_COUNT_PER_GATEWAY = max_resource_count
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.filter_id_to_fields",
            return_value=mock_resource_id_to_fields,
        )
        validator = ResourceImportValidator(fake_gateway, importing_resources)

        if not expected_error:
            assert validator._validate_resource_count() is None
            return

        with pytest.raises(expected_error):
            validator._validate_resource_count()

    @pytest.mark.parametrize(
        "resource_id_to_fields, expected",
        [
            (
                {
                    1: {"id": 1, "method": "GET", "path": "/echo/", "name": "get_echo"},
                    2: {"id": 2, "method": "POST", "path": "/echo/", "name": "post_echo"},
                },
                {
                    "/echo/": {
                        "GET": 1,
                        "POST": 2,
                    },
                },
            )
        ],
    )
    def test_get_resource_path_method_to_id(self, fake_gateway, resource_id_to_fields, expected):
        validator = ResourceImportValidator(fake_gateway, [])
        validator._existed_resource_id_to_fields = resource_id_to_fields
        result = validator._get_resource_path_method_to_id()
        assert result == expected


class TestResourcesImporter:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.importer = ResourcesImporter(fake_gateway, allow_overwrite=True, username="")

    def test_init(self, fake_gateway):
        importer = ResourcesImporter(fake_gateway, allow_overwrite=True, username="admin")

        assert importer.allow_overwrite is True
        assert importer.username == "admin"
        assert importer.imported_resources == []
        assert importer._selected_resources is None

    def test_import_resources(self, mocker):
        mocker.patch.object(self.importer, "_filter_imported_resources", return_value=None)
        mocker.patch.object(self.importer, "_create_not_exist_labels", return_value=None)
        mocker.patch.object(self.importer, "_enrich_imported_resources", return_value=None)
        mocker.patch.object(self.importer, "_create_resource", return_value=mocker.MagicMock(id=1))
        mocker.patch.object(self.importer, "_update_resource", return_value=None)
        mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.get",
            return_value=mocker.MagicMock(),
        )

        self.importer.imported_resources = [
            {"id": None},
            {"id": 2},
        ]

        self.importer.import_resources()
        assert self.importer.imported_resources == [
            {"id": 1, "_is_created": True},
            {"id": 2, "_is_updated": True},
        ]

    @pytest.mark.parametrize(
        "content, expected",
        [
            (
                json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "operationId": "http_get_mapping_userid",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "allowApplyPermission": True,
                                        "matchSubpath": True,
                                        "backend": {
                                            "type": "HTTP",
                                            "path": "/hello/",
                                            "matchSubpath": True,
                                            "method": "get",
                                            "timeout": 30,
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                {
                    "imported_resources": [
                        {
                            "method": "GET",
                            "path": "/http/get/mapping/{userId}",
                            "match_subpath": True,
                            "name": "http_get_mapping_userid",
                            "description": "test",
                            "description_en": None,
                            "labels": ["pet"],
                            "is_public": True,
                            "allow_apply_permission": True,
                            "proxy_type": "http",
                            "proxy_configs": {
                                "http": {
                                    "method": "GET",
                                    "path": "/hello/",
                                    "match_subpath": True,
                                    "timeout": 30,
                                    "upstreams": {},
                                    "transform_headers": {},
                                }
                            },
                            "auth_config": {
                                "auth_verified_required": True,
                            },
                            "disabled_stages": [],
                        }
                    ],
                    "selected_resources": None,
                },
            ),
            (
                json.dumps(
                    {
                        "swagger": "2.0",
                        "basePath": "/",
                        "info": {
                            "version": "0.1",
                            "title": "API Gateway Swagger",
                        },
                        "schemes": ["http"],
                        "paths": {
                            "/http/get/mapping/{userId}": {
                                "get": {
                                    "operationId": "http_get_mapping_userid",
                                    "description": "test",
                                    "tags": ["pet"],
                                    "schemes": ["http"],
                                    "x-bk-apigateway-resource": {
                                        "isPublic": True,
                                        "descriptionEn": "english",
                                        "allowApplyPermission": True,
                                        "backend": {
                                            "type": "MOCK",
                                            "statusCode": 200,
                                            "responseBody": "test",
                                            "headers": {
                                                "X-Token": "token",
                                            },
                                        },
                                    },
                                },
                            }
                        },
                    }
                ),
                {
                    "imported_resources": [
                        {
                            "method": "GET",
                            "path": "/http/get/mapping/{userId}",
                            "name": "http_get_mapping_userid",
                            "description": "test",
                            "description_en": "english",
                            "labels": ["pet"],
                            "is_public": True,
                            "allow_apply_permission": True,
                            "match_subpath": False,
                            "proxy_type": "mock",
                            "proxy_configs": {
                                "mock": {
                                    "code": 200,
                                    "body": "test",
                                    "headers": {
                                        "X-Token": "token",
                                    },
                                }
                            },
                            "auth_config": {
                                "auth_verified_required": True,
                            },
                            "disabled_stages": [],
                        }
                    ],
                    "selected_resources": [{"name": "echo"}],
                },
            ),
        ],
    )
    def test_load_importing_resources_by_swagger(self, mocker, content, expected):
        mock_set_importing_resources = mocker.patch.object(
            self.importer,
            "set_importing_resources",
            return_value=None,
        )

        self.importer.load_importing_resources_by_swagger(content)

        mock_set_importing_resources.assert_called_once_with(expected["imported_resources"])

    @pytest.mark.parametrize(
        "mock_unspecified_resources, unspecified_resource_id, expected",
        [
            (
                [],
                None,
                {
                    "unspecified_resources": [],
                    "existed_resource_id_to_fields": {1: {"id": 1}},
                },
            ),
            (
                [{"id": 1}, {"id": 2}],
                [1, 2],
                {
                    "unspecified_resources": [{"id": 1}, {"id": 2}],
                    "existed_resource_id_to_fields": {3: {"id": 3}},
                },
            ),
        ],
    )
    def test_delete_unspecified_resources(self, mocker, mock_unspecified_resources, unspecified_resource_id, expected):
        mocker.patch.object(self.importer, "get_unspecified_resources", return_value=mock_unspecified_resources)
        mock_delete_resources = mocker.patch(
            "apigateway.apps.resource.importer.ResourceHandler.delete_resources",
            return_value=None,
        )

        result = self.importer._delete_unspecified_resources()

        assert result == expected["unspecified_resources"]

        if unspecified_resource_id is None:
            mock_delete_resources.assert_not_called()
            return

        mock_delete_resources.assert_called_once_with(unspecified_resource_id, self.importer.gateway)

    @pytest.mark.parametrize(
        "imported_resources, expected",
        [
            (
                [],
                [],
            ),
            (
                [{"id": 1}, {"id": None}, {"id": 3}],
                [1, 3],
            ),
        ],
    )
    def test_get_unspecified_resources(self, mocker, imported_resources, expected):
        mocker.patch.object(
            self.importer, "imported_resources", new_callable=mocker.PropertyMock(return_value=imported_resources)
        )
        mock_get_unspecified_resource_fields = mocker.patch(
            "apigateway.apps.resource.importer.Resource.objects.get_unspecified_resource_fields",
            return_value=[{"id": 10}],
        )

        result = self.importer.get_unspecified_resources()
        assert result == [{"id": 10}]
        mock_get_unspecified_resource_fields.assert_called_once_with(self.importer.gateway.id, expected)

    @pytest.mark.parametrize(
        "imported_resources, selected_resources, expected",
        [
            (
                [
                    {"name": "get_user"},
                    {"name": "create_user"},
                ],
                None,
                [
                    {"name": "get_user"},
                    {"name": "create_user"},
                ],
            ),
            (
                [
                    {"name": "get_user"},
                    {"name": "create_user"},
                ],
                [{"name": "get_user"}],
                [
                    {"name": "get_user"},
                ],
            ),
            (
                [
                    {"name": "get_user"},
                    {"name": "create_user"},
                ],
                [],
                [],
            ),
        ],
    )
    def test_filter_imported_resources(self, imported_resources, selected_resources, expected):
        self.importer.imported_resources = imported_resources
        self.importer._selected_resources = selected_resources
        self.importer._filter_imported_resources()

        assert self.importer.imported_resources == expected

    @pytest.mark.parametrize(
        "imported_resources, expected",
        [
            (
                [
                    {"labels": ["l1", "l2"]},
                    {"labels": ["l2", "l3"]},
                ],
                set(["l1", "l2", "l3"]),
            )
        ],
    )
    def test_create_exist_labels(self, mocker, imported_resources, expected):
        mock_save_labels = mocker.patch(
            "apigateway.apps.resource.importer.APILabel.objects.save_labels",
            return_value=None,
        )

        self.importer.imported_resources = imported_resources
        self.importer._create_not_exist_labels()

        mock_save_labels.assert_called_once_with(self.importer.gateway, expected, self.importer.username)

    @pytest.mark.parametrize(
        "mock_label_name_to_id, mock_stage_name_to_id, imported_resources, expected",
        [
            (
                {
                    "l1": 1,
                    "l2": 2,
                },
                {
                    "prod": 3,
                    "test": 4,
                },
                [
                    {"labels": ["l1"], "disabled_stages": ["test"]},
                ],
                [
                    {"labels": ["l1"], "disabled_stages": ["test"], "label_ids": [1], "disabled_stage_ids": [4]},
                ],
            )
        ],
    )
    def test_enrich_imported_resources(
        self, mocker, mock_label_name_to_id, mock_stage_name_to_id, imported_resources, expected
    ):
        mocker.patch(
            "apigateway.apps.resource.importer.APILabel.objects.get_name_id_map",
            return_value=mock_label_name_to_id,
        )
        mocker.patch(
            "apigateway.apps.resource.importer.Stage.objects.get_name_id_map",
            return_value=mock_stage_name_to_id,
        )

        self.importer.imported_resources = imported_resources
        self.importer._enrich_imported_resources()
        assert self.importer.imported_resources == expected
