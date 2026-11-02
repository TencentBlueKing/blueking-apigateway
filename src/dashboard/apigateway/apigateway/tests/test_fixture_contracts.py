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
import json

import pytest

from apigateway.core.models import Schema
from apigateway.schema.data.meta_schema import init_meta_schemas
from apigateway.schema.instances import SCHEMA_NAME_CONTEXT_GATEWAY_FEATURE_FLAG
from apigateway.tests.conftest import _ensure_meta_schemas


@pytest.mark.no_meta_schema
def test_pure_tests_do_not_implicitly_enable_database_access():
    with pytest.raises(RuntimeError, match="Database access not allowed"):
        Schema.objects.count()


@pytest.mark.no_meta_schema
@pytest.mark.django_db
def test_schema_opt_out_still_allows_explicit_database_access():
    schema = Schema.objects.create(name="explicit-schema", type="context", version="1", schema={"type": "object"})
    assert Schema.objects.get(id=schema.id).schema == {"type": "object"}


@pytest.mark.no_meta_schema
@pytest.mark.django_db
class TestMetaSchemaInitialization:
    @pytest.fixture
    def existing_schema(self):
        _ensure_meta_schemas()
        expected = init_meta_schemas()[0]
        return Schema.objects.get(name=expected.name, type=expected.type, version=expected.version), expected

    def test_unchanged_schemas_are_not_rewritten(self, existing_schema, mocker):
        schema, _ = existing_schema
        updated_time = schema.updated_time
        save = mocker.spy(Schema, "save")

        _ensure_meta_schemas()

        save.assert_not_called()
        schema.refresh_from_db()
        assert schema.updated_time == updated_time

    def test_json_formatting_does_not_trigger_a_rewrite(self, existing_schema, mocker):
        schema, _ = existing_schema
        schema._schema = json.dumps(schema.schema, indent=2)
        schema.save()
        save = mocker.spy(Schema, "save")

        _ensure_meta_schemas()

        save.assert_not_called()

    def test_boolean_schema_value_is_not_equivalent_to_zero(self):
        _ensure_meta_schemas()
        schema = Schema.objects.get(name=SCHEMA_NAME_CONTEXT_GATEWAY_FEATURE_FLAG)
        changed = schema.schema
        changed["additionalProperties"] = 0
        schema.schema = changed
        schema.save()

        _ensure_meta_schemas()

        schema.refresh_from_db()
        assert schema.schema["additionalProperties"] is False

    @pytest.mark.parametrize(
        "field, value",
        [
            ("schema", {"type": "null"}),
            ("_schema", "invalid JSON"),
            ("description", "changed"),
            ("example", "changed"),
        ],
    )
    def test_changed_schema_content_is_restored(self, existing_schema, field, value):
        schema, expected = existing_schema
        original_id = schema.id
        setattr(schema, field, value)
        schema.save()

        _ensure_meta_schemas()

        schema.refresh_from_db()
        assert schema.id == original_id
        assert schema.schema == expected.schema
        assert schema.description == expected.description
        assert schema.example == expected.example

    def test_missing_schema_is_recreated_without_changing_other_versions(self, existing_schema):
        schema, expected = existing_schema
        other = Schema.objects.create(name=schema.name, type=schema.type, version="extra", schema={"type": "null"})
        schema.delete()

        _ensure_meta_schemas()

        restored = Schema.objects.get(name=expected.name, type=expected.type, version=expected.version)
        assert restored.schema == expected.schema
        other.refresh_from_db()
        assert other.schema == {"type": "null"}
