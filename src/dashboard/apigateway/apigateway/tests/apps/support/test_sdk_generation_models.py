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
from ddf import G
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

from apigateway.apps.support.constants import SDKDistributorEnum, SDKGenerationStatusEnum
from apigateway.apps.support.models import SDKArtifact, SDKGenerationItem, SDKGenerationTask
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


def test_generation_task_is_unique_per_resource_version(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)

    assert task.status == SDKGenerationStatusEnum.PENDING.value

    with pytest.raises(IntegrityError), transaction.atomic():
        SDKGenerationTask.objects.create(gateway=fake_gateway, resource_version=fake_resource_version)


def test_generation_item_is_unique_per_task_and_language(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    G(SDKGenerationItem, task=task, language="python")

    with pytest.raises(IntegrityError), transaction.atomic():
        SDKGenerationItem.objects.create(task=task, language="python")


def test_generation_item_accepts_only_canonical_languages(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)

    with pytest.raises(IntegrityError), transaction.atomic():
        SDKGenerationItem.objects.create(task=task, language="golang")


def test_generation_item_full_clean_rejects_unknown_language_before_database(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    item = SDKGenerationItem(task=task, language="unknown")

    with pytest.raises(ValidationError) as exc_info:
        item.full_clean()

    assert "language" in exc_info.value.message_dict


def test_generation_task_full_clean_accepts_matching_gateway_and_resource_version(fake_gateway, fake_resource_version):
    task = SDKGenerationTask(gateway=fake_gateway, resource_version=fake_resource_version)

    task.full_clean()


def test_generation_task_full_clean_rejects_mismatched_gateway_and_resource_version(
    fake_gateway, fake_resource_version
):
    other_gateway = G(Gateway)
    task = SDKGenerationTask(gateway=other_gateway, resource_version=fake_resource_version)

    with pytest.raises(ValidationError, match="gateway"):
        task.full_clean()


def test_artifact_filename_is_unique_per_item_and_distributor(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    item = G(SDKGenerationItem, task=task, language="python")
    G(SDKArtifact, item=item, distributor=SDKDistributorEnum.BKREPO_GENERIC.value, filename="sdk.tar.gz")

    with pytest.raises(IntegrityError), transaction.atomic():
        SDKArtifact.objects.create(
            item=item,
            distributor=SDKDistributorEnum.BKREPO_GENERIC.value,
            filename="sdk.tar.gz",
        )

    G(SDKArtifact, item=item, distributor=SDKDistributorEnum.PYPI.value, filename="sdk.tar.gz")


def test_generation_task_deletion_cascades_to_items_and_artifacts(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    item = G(SDKGenerationItem, task=task, language="python")
    artifact = G(SDKArtifact, item=item)

    task.delete()

    assert not SDKGenerationItem.objects.filter(id=item.id).exists()
    assert not SDKArtifact.objects.filter(id=artifact.id).exists()


def test_generation_item_defaults_include_pending_status_and_empty_lease(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)

    item = G(SDKGenerationItem, task=task, language="python")

    assert item.status == SDKGenerationStatusEnum.PENDING.value
    assert item.lease_token == ""
    assert item.lease_expires_at is None
    assert item.attempt_count == 0
    assert item.input_fingerprint == ""
    assert item.config_snapshot == {}
    assert item.started_at is None
    assert item.finished_at is None


def test_generation_artifact_defaults_to_generic_pending_status(fake_gateway, fake_resource_version):
    task = G(SDKGenerationTask, gateway=fake_gateway, resource_version=fake_resource_version)
    item = G(SDKGenerationItem, task=task, language="python")

    artifact = G(SDKArtifact, item=item)

    assert artifact.distributor == SDKDistributorEnum.BKREPO_GENERIC.value
    assert artifact.status == SDKGenerationStatusEnum.PENDING.value


@pytest.mark.django_db(transaction=True)
def test_sdk_generation_migration_converts_legacy_golang_both_directions():
    if not hasattr(settings.MIGRATION_MODULES, "get"):
        pytest.skip("migration round-trip requires migration modules")

    migration_name = "0019_sdk_generation_tasks"
    old_target = ("support", "0018_remove_resourcedocswagger")
    new_target = ("support", migration_name)
    gateway = G(
        Gateway,
        name="sdk-migration-gateway",
        _maintainers="admin",
        tenant_mode="single",
        tenant_id="default",
        status=1,
    )

    executor = MigrationExecutor(connection)
    leaf_nodes = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate([old_target])
        old_apps = executor.loader.project_state([old_target]).apps
        old_apps.get_model("support", "APISDK").objects.create(
            gateway_id=gateway.id,
            language="golang",
            version_number="1.0.0",
            filename="sdk.tar.gz",
        )

        executor = MigrationExecutor(connection)
        executor.migrate([new_target])
        new_apps = executor.loader.project_state([new_target]).apps
        gateway_sdk = new_apps.get_model("support", "APISDK").objects.get(gateway_id=gateway.id)
        assert gateway_sdk.language == "go"

        executor = MigrationExecutor(connection)
        executor.migrate([old_target])
        reverted_apps = executor.loader.project_state([old_target]).apps
        reverted_gateway_sdk = reverted_apps.get_model("support", "APISDK").objects.get(gateway_id=gateway.id)
        assert reverted_gateway_sdk.language == "golang"
    finally:
        MigrationExecutor(connection).migrate(leaf_nodes)
