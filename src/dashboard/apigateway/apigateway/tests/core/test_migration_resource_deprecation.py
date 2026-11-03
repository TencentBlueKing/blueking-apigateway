#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
#
import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

pytestmark = [pytest.mark.migration, pytest.mark.django_db(transaction=True)]


def test_existing_resources_default_to_not_deprecated():
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    before = [("core", "0057_gateway_display_names")]
    after = [("core", "0058_resource_deprecation")]
    try:
        executor.migrate(before)
        apps = executor.loader.project_state(before).apps
        gateway = apps.get_model("core", "Gateway").objects.create(
            name="migration-deprecation", status=1, tenant_mode="single", tenant_id=""
        )
        resource = apps.get_model("core", "Resource").objects.create(
            gateway_id=gateway.id,
            name="get_users",
            method="GET",
            path="/users",
            proxy_id=0,
        )
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        resource_model = executor.loader.project_state(after).apps.get_model("core", "Resource")
        migrated = resource_model.objects.get(pk=resource.pk)
        assert migrated.is_deprecated is False
        assert migrated.deprecated_note == ""
        assert (migrated.name, migrated.path) == ("get_users", "/users")
    finally:
        MigrationExecutor(connection).migrate(latest)
