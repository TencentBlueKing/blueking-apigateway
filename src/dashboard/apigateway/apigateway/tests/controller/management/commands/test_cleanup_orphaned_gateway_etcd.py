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
import traceback
from io import StringIO
from pathlib import Path
from typing import NoReturn
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from etcd3.utils import prefix_range_end

from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.convertor.constants import (
    LABEL_KEY_APISIX_VERSION,
    LABEL_KEY_GATEWAY,
    LABEL_KEY_PUBLISH_ID,
    LABEL_KEY_STAGE,
)
from apigateway.controller.distributor.key_prefix import GatewayKeyPrefixHandler
from apigateway.controller.management.commands import cleanup_orphaned_gateway_etcd as cleanup_command
from apigateway.controller.management.commands.cleanup_orphaned_gateway_etcd import (
    OrphanGatewayEtcdScanner,
    ScanResult,
    StageKeys,
)
from apigateway.controller.models import BkRelease, Labels
from apigateway.tests.controller.fake_etcd import (
    FakeEtcdClient,
    get_delete_ranges,
    get_put_keys,
    in_range,
    ranges_overlap,
)

pytestmark = pytest.mark.django_db

COMMAND_NAME = "cleanup_orphaned_gateway_etcd"
COMMAND_MODULE = "apigateway.controller.management.commands.cleanup_orphaned_gateway_etcd"


@pytest.fixture
def data_plane(default_data_plane):
    default_data_plane.etcd_namespace_prefix = "/bk-gateway-apigw/default"
    default_data_plane.apisix_version = "3.13"
    default_data_plane.etcd_configs = {"host": "127.0.0.1", "port": 2379}
    default_data_plane.save(update_fields=["etcd_namespace_prefix", "apisix_version", "_encrypted_etcd_configs"])
    return default_data_plane


@pytest.fixture
def mock_etcd_client(mocker):
    return mocker.Mock()


def gateway_root(data_plane):
    return f"{data_plane.etcd_namespace_prefix.rstrip('/')}/v2/gateway"


def production_gateway_root(data_plane):
    return (
        GatewayKeyPrefixHandler(prefix=data_plane.etcd_namespace_prefix)
        .get_release_key_prefix(
            "__gateway__",
            "__stage__",
        )
        .removesuffix("__gateway__/__stage__/")
    )


def make_etcd_item(key, value=None):
    metadata = Mock(key=key.encode())
    return value, metadata


def make_stage_keys(gateway_name, stage_name, keys=None):
    keys = keys or (f"/bk-gateway-apigw/default/v2/gateway/{gateway_name}/{stage_name}/route/route-1",)
    return StageKeys(
        gateway_name=gateway_name,
        stage_name=stage_name,
        key_prefix=f"/bk-gateway-apigw/default/v2/gateway/{gateway_name}/{stage_name}/",
        keys=tuple(keys),
        kinds=tuple(key.split("/")[-2] for key in keys),
    )


def make_delete_release_payload(
    gateway_name,
    stage_name,
    apisix_version,
    resource_version="orphan-cleanup",
    release_id=None,
    publish_id=DELETE_PUBLISH_ID,
    label_publish_id=None,
    label_apisix_version=None,
):
    release = BkRelease(
        id=release_id or f"bk.release.{gateway_name}.{stage_name}",
        publish_id=publish_id,
        publish_time="2026-08-06 00:00:00",
        apisix_version=apisix_version,
        resource_version=resource_version,
        labels=Labels(
            **{
                LABEL_KEY_GATEWAY: gateway_name,
                LABEL_KEY_STAGE: stage_name,
                LABEL_KEY_PUBLISH_ID: label_publish_id if label_publish_id is not None else publish_id,
                LABEL_KEY_APISIX_VERSION: label_apisix_version or apisix_version,
            }
        ),
    )
    return release.model_dump_json().encode()


def test_scan_classifies_actionable_existing_and_tombstoned_gateways(
    fake_gateway,
    data_plane,
    mock_etcd_client,
):
    orphan_route = make_etcd_item(
        f"{gateway_root(data_plane)}/orphan/prod/route/route-1",
        value=None,
    )
    existing_route = make_etcd_item(
        f"{gateway_root(data_plane)}/{fake_gateway.name}/prod/route/route-2",
        value=None,
    )
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    mock_etcd_client.get_prefix.return_value = [orphan_route, existing_route, make_etcd_item(tombstone_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("cleaned", "prod", data_plane.apisix_version),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name, item.key_count) for item in result.actionable] == [
        ("orphan", "prod", 1)
    ]
    assert [(item.gateway_name, item.stage_name) for item in result.tombstoned] == [("cleaned", "prod")]
    assert result.malformed_keys == ()


def test_scan_reports_malformed_keys(data_plane, mock_etcd_client):
    malformed = f"{gateway_root(data_plane)}/missing-segments"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(malformed)]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert result.actionable == ()
    assert result.malformed_keys == (malformed,)


def test_scan_treats_invalid_delete_release_as_actionable(data_plane, mock_etcd_client):
    release_key = f"{gateway_root(data_plane)}/orphan/prod/_bk_release/bk.release.orphan.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(release_key)]
    mock_etcd_client.get.return_value = (b'{"publish_id": 10}', object())

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [("orphan", "prod")]


def test_scan_accepts_tombstone_left_by_normal_delete_publish(data_plane, mock_etcd_client):
    """正常删除发布留下的墓碑带原始 resource_version 和当时的 APISIX 版本，必须幂等跳过"""
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(tombstone_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("cleaned", "prod", "3.2", resource_version="20260101120000"),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert data_plane.apisix_version != "3.2"
    assert [(item.gateway_name, item.stage_name) for item in result.tombstoned] == [("cleaned", "prod")]
    assert result.actionable == ()


def test_scan_treats_release_with_inconsistent_apisix_label_as_actionable(data_plane, mock_etcd_client):
    release_key = f"{gateway_root(data_plane)}/orphan/prod/_bk_release/bk.release.orphan.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(release_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload(
            "orphan",
            "prod",
            data_plane.apisix_version,
            label_apisix_version="0.0",
        ),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [("orphan", "prod")]


def test_scan_treats_release_with_non_delete_publish_id_as_actionable(data_plane, mock_etcd_client):
    release_key = f"{gateway_root(data_plane)}/orphan/prod/_bk_release/bk.release.orphan.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(release_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("orphan", "prod", data_plane.apisix_version, publish_id=7),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [("orphan", "prod")]


def test_scan_treats_release_with_non_delete_publish_id_label_as_actionable(data_plane, mock_etcd_client):
    release_key = f"{gateway_root(data_plane)}/orphan/prod/_bk_release/bk.release.orphan.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(release_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("orphan", "prod", data_plane.apisix_version, label_publish_id=-1),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [("orphan", "prod")]


def test_scan_treats_release_key_with_unexpected_id_as_actionable(data_plane, mock_etcd_client):
    release_key = f"{gateway_root(data_plane)}/orphan/prod/_bk_release/unexpected-release-key"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(release_key)]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("orphan", "prod", data_plane.apisix_version),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [("orphan", "prod")]


def test_scan_aborts_when_tombstone_value_read_fails(data_plane, mock_etcd_client):
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(tombstone_key)]
    mock_etcd_client.get.side_effect = TimeoutError("etcd timeout")

    with pytest.raises(cleanup_command.TombstoneReadError) as exc_info:
        OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert "etcd timeout" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_is_valid_tombstone_is_a_public_scanner_method(data_plane, mock_etcd_client):
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    stage = make_stage_keys("cleaned", "prod", keys=(tombstone_key,))
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("cleaned", "prod", data_plane.apisix_version),
        object(),
    )
    scanner = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client)

    assert scanner.is_valid_tombstone(stage) is True
    assert not hasattr(scanner, "_is_valid_tombstone")


def test_scan_stage_lists_only_the_target_stage_prefix(data_plane, mock_etcd_client):
    stage_prefix = f"{gateway_root(data_plane)}/orphan/prod/"
    route_key = f"{stage_prefix}route/route-1"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(route_key)]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan_stage("orphan", "prod")

    mock_etcd_client.get_prefix.assert_called_once_with(stage_prefix, keys_only=True)
    assert [(item.gateway_name, item.stage_name, item.keys) for item in result.actionable] == [
        ("orphan", "prod", (route_key,))
    ]


def test_scan_stage_reports_malformed_keys_under_target_stage(data_plane, mock_etcd_client):
    stage_prefix = f"{gateway_root(data_plane)}/orphan/prod/"
    malformed_key = f"{stage_prefix}route/route-1/extra"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(malformed_key)]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan_stage("orphan", "prod")

    assert result.actionable == ()
    assert result.malformed_keys == (malformed_key,)


def test_scan_reads_values_only_for_unique_delete_release_candidates(data_plane, mock_etcd_client):
    route_key = f"{gateway_root(data_plane)}/orphan/prod/route/route-1"
    mixed_release_key = f"{gateway_root(data_plane)}/mixed/prod/_bk_release/bk.release.mixed.prod"
    mixed_route_key = f"{gateway_root(data_plane)}/mixed/prod/route/route-1"
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    mock_etcd_client.get_prefix.return_value = [
        make_etcd_item(route_key, value=b"password payload should not be read"),
        make_etcd_item(mixed_release_key, value=b"plugins should not be read"),
        make_etcd_item(mixed_route_key, value=b"cert should not be read"),
        make_etcd_item(tombstone_key),
    ]
    mock_etcd_client.get.return_value = (
        make_delete_release_payload("cleaned", "prod", data_plane.apisix_version),
        object(),
    )

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert [(item.gateway_name, item.stage_name) for item in result.actionable] == [
        ("mixed", "prod"),
        ("orphan", "prod"),
    ]
    assert [(item.gateway_name, item.stage_name) for item in result.tombstoned] == [("cleaned", "prod")]
    mock_etcd_client.get.assert_called_once_with(tombstone_key)


def test_scan_applies_gateway_allowlist_and_sorts_stages(data_plane, mock_etcd_client):
    beta_key = f"{gateway_root(data_plane)}/beta/prod/route/route-2"
    ignored_key = f"{gateway_root(data_plane)}/ignored/prod/route/route-1"
    alpha_key = f"{gateway_root(data_plane)}/alpha/test/service/service-1"
    mock_etcd_client.get_prefix.return_value = [
        make_etcd_item(beta_key),
        make_etcd_item(ignored_key),
        make_etcd_item(alpha_key),
    ]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan(gateway_names={"alpha", "beta"})

    assert [(item.gateway_name, item.stage_name, item.keys) for item in result.actionable] == [
        ("alpha", "test", (alpha_key,)),
        ("beta", "prod", (beta_key,)),
    ]


def test_scan_reports_malformed_key_variants_sorted(data_plane, mock_etcd_client):
    root = gateway_root(data_plane)
    malformed_keys = [
        f"{root}/orphan/prod/route/route-1/extra",
        f"{root}/orphan//route/route-1",
        f"{root}/orphan/missing-segments",
        "/outside/prefix/orphan/prod/route/route-1",
    ]
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(key) for key in reversed(malformed_keys)]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    assert result.actionable == ()
    assert result.malformed_keys == tuple(sorted(malformed_keys))


def test_scan_uses_production_prefix_handler_trailing_slash_semantics(data_plane, mock_etcd_client):
    data_plane.etcd_namespace_prefix = "/bk-gateway-apigw/default/"
    expected_root = production_gateway_root(data_plane)
    route_key = f"{expected_root}orphan/prod/route/route-1"
    mock_etcd_client.get_prefix.return_value = [make_etcd_item(route_key)]

    result = OrphanGatewayEtcdScanner(data_plane, mock_etcd_client).scan()

    mock_etcd_client.get_prefix.assert_called_once_with(expected_root, keys_only=True)
    assert result.actionable[0].key_prefix == (
        GatewayKeyPrefixHandler(prefix=data_plane.etcd_namespace_prefix).get_release_key_prefix("orphan", "prod")
    )


def test_command_requires_data_plane_name():
    with pytest.raises(CommandError, match="the following arguments are required: --data-plane-name"):
        call_command(COMMAND_NAME)


def test_command_rejects_unknown_data_plane():
    with pytest.raises(CommandError, match="data plane not found: unknown"):
        call_command(COMMAND_NAME, data_plane_name="unknown")


@pytest.mark.parametrize("etcd_namespace_prefix", ["", "   ", "/", "//"])
def test_command_rejects_empty_etcd_namespace_prefix(data_plane, mocker, etcd_namespace_prefix):
    data_plane.etcd_namespace_prefix = etcd_namespace_prefix
    data_plane.save(update_fields=["etcd_namespace_prefix"])
    new_etcd_client = mocker.patch(f"{COMMAND_MODULE}.new_etcd_client")

    with pytest.raises(CommandError, match="etcd namespace prefix is empty"):
        call_command(COMMAND_NAME, data_plane_name=data_plane.name)

    new_etcd_client.assert_not_called()


def test_command_aborts_when_tombstone_value_read_fails(data_plane, mocker):
    tombstone_key = f"{gateway_root(data_plane)}/cleaned/prod/_bk_release/bk.release.cleaned.prod"
    etcd_client = mocker.Mock()
    etcd_client.get_prefix.return_value = [make_etcd_item(tombstone_key)]
    etcd_client.get.side_effect = TimeoutError("etcd timeout")
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)

    with pytest.raises(CommandError) as exc_info:
        call_command(COMMAND_NAME, data_plane_name=data_plane.name)

    assert "etcd timeout" not in str(exc_info.value)
    assert "etcd timeout" not in "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))


def test_command_defaults_to_read_only_scan(data_plane, mocker):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(make_stage_keys("orphan", "prod"),),
        tombstoned=(make_stage_keys("cleaned", "prod"),),
        malformed_keys=("/bad/key",),
    )
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=mocker.Mock())
    output = StringIO()

    call_command(COMMAND_NAME, data_plane_name=data_plane.name, stdout=output)

    replace.assert_not_called()
    assert "status=actionable gateway=orphan stage=prod" in output.getvalue()
    assert "status=tombstoned gateway=cleaned stage=prod" in output.getvalue()
    assert "status=malformed key=/bad/key" in output.getvalue()
    assert "dry_run=true" in output.getvalue()


def test_apply_requires_explicit_gateway_names(data_plane, mocker):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(), tombstoned=(), malformed_keys=())

    with pytest.raises(CommandError, match="--apply requires --gateway-names"):
        call_command(COMMAND_NAME, data_plane_name=data_plane.name, apply=True, log_file="/tmp/audit.jsonl")


def test_apply_requires_log_file(data_plane, mocker):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(), tombstoned=(), malformed_keys=())

    with pytest.raises(CommandError, match="--apply requires --log-file"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
        )


def test_apply_rejects_name_not_in_actionable_scan(data_plane, mocker, tmp_path):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(), tombstoned=(), malformed_keys=())

    with pytest.raises(CommandError, match="requested gateways are not actionable"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )


def test_apply_rejects_gateway_that_exists_in_database(fake_gateway, data_plane, mocker, tmp_path):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(make_stage_keys(fake_gateway.name, "prod"),),
        tombstoned=(),
        malformed_keys=(),
    )

    with pytest.raises(CommandError, match=f"gateway exists in database: {fake_gateway.name}"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names=fake_gateway.name,
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )


def test_apply_rejects_malformed_key_for_selected_gateway(data_plane, mocker, tmp_path):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(make_stage_keys("orphan", "prod"),),
        tombstoned=(),
        malformed_keys=(f"{gateway_root(data_plane)}/orphan/missing-segments",),
    )

    with pytest.raises(CommandError, match="malformed etcd keys for selected gateways: orphan"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )


def test_apply_rejects_unwritable_log_file_before_transaction(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    tombstone_key = f"{stage.key_prefix}_bk_release/bk.release.orphan.prod"
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    etcd_client = mocker.Mock()
    etcd_client.get_prefix.return_value = [make_etcd_item(tombstone_key)]
    etcd_client.get.return_value = (
        cleanup_command.build_delete_release(stage, data_plane.apisix_version).model_dump_json().encode(),
        object(),
    )
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )

    with pytest.raises(CommandError, match="audit log file is not writable"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path),
        )

    replace.assert_not_called()


def test_build_delete_release_uses_operator_delete_contract(data_plane):
    release = cleanup_command.build_delete_release(make_stage_keys("orphan", "prod"), data_plane.apisix_version)

    assert release.id == "bk.release.orphan.prod"
    assert release.publish_id == DELETE_PUBLISH_ID
    assert release.resource_version == "orphan-cleanup"
    assert release.labels.get_label(LABEL_KEY_GATEWAY) == "orphan"
    assert release.labels.get_label(LABEL_KEY_STAGE) == "prod"
    assert release.labels.get_label(LABEL_KEY_PUBLISH_ID) == str(DELETE_PUBLISH_ID)
    assert release.labels.get_label(LABEL_KEY_APISIX_VERSION) == data_plane.apisix_version


def test_apply_successful_cleanup_replaces_stage_with_delete_release_and_writes_audit(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    tombstone_key = f"{stage.key_prefix}_bk_release/bk.release.orphan.prod"
    audit_file = tmp_path / "audit.jsonl"
    secret_payload = b'{"password":"hidden","etcd_configs":{},"plugins":[],"cert":"secret","sentinel":"payload"}'

    etcd_client = mocker.Mock()
    etcd_client.get_prefix.side_effect = [
        [make_etcd_item(stage.keys[0], value=secret_payload)],
        [make_etcd_item(stage.keys[0], value=secret_payload)],
        [make_etcd_item(tombstone_key)],
    ]
    etcd_client.get.return_value = (
        cleanup_command.build_delete_release(stage, data_plane.apisix_version).model_dump_json().encode(),
        object(),
    )
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    output = StringIO()

    order = []
    real_filter = cleanup_command.Gateway.objects.filter

    def filter_side_effect(*args, **kwargs):
        queryset = real_filter(*args, **kwargs)
        if kwargs == {"name": "orphan"}:
            order.append("per-stage-db-recheck")
        return queryset

    mocker.patch(f"{COMMAND_MODULE}.Gateway.objects.filter", side_effect=filter_side_effect)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically",
        side_effect=lambda *_args, **_kwargs: order.append("replace"),
    )

    call_command(
        COMMAND_NAME,
        data_plane_name=data_plane.name,
        gateway_names="orphan",
        apply=True,
        log_file=str(audit_file),
        stdout=output,
    )

    assert order == ["per-stage-db-recheck", "replace"]
    replace.assert_called_once()
    resources = replace.call_args.args[0]
    assert len(resources) == 1
    assert resources[0].publish_id == DELETE_PUBLISH_ID
    assert resources[0].resource_version == "orphan-cleanup"
    assert etcd_client.get_prefix.call_args_list[-1].args == (stage.key_prefix,)
    assert etcd_client.get.call_args.args == (tombstone_key,)
    printed = output.getvalue()
    assert (
        f"cleanup_applied gateway=orphan stage=prod key_prefix={stage.key_prefix} "
        "tombstone_verified=true control_plane_delete_event=written" in printed
    )
    assert (
        f"cleanup_summary data_plane_name={data_plane.name} cleaned_stage_count=1 "
        "control_plane_delete_event=written "
        "note=operator/APISIX data plane cleanup is asynchronous and not confirmed by this command" in printed
    )
    audit_line = audit_file.read_text().splitlines()[0]
    audit = json.loads(audit_line)
    assert audit["action"] == "cleanup_orphaned_gateway_etcd"
    assert audit["result"] == "success"
    assert audit["data_plane_id"] == data_plane.id
    assert audit["data_plane_name"] == data_plane.name
    assert audit["gateway_name"] == "orphan"
    assert audit["stage_name"] == "prod"
    assert audit["key_prefix"] == stage.key_prefix
    assert audit["previous_key_count"] == 1
    assert "password" not in audit_line
    assert "etcd_configs" not in audit_line
    assert "plugins" not in audit_line
    assert "cert" not in audit_line
    assert "payload" not in audit_line


def test_apply_confirmation_mismatch_fails_without_writes(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=f"{data_plane.name}-typo")
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    audit_file = tmp_path / "audit.jsonl"

    with pytest.raises(CommandError, match="data plane confirmation mismatch"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
        )

    replace.assert_not_called()
    assert not audit_file.exists()


def test_apply_confirmation_eof_fails_without_writes(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", side_effect=EOFError())
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    audit_file = tmp_path / "audit.jsonl"

    with pytest.raises(CommandError, match="confirmation input"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
        )

    replace.assert_not_called()
    assert not audit_file.exists()


def test_apply_prints_data_plane_identity_and_stage_prefixes_before_confirmation(data_plane, mocker, tmp_path):
    prod_stage = make_stage_keys("orphan", "prod")
    test_stage = make_stage_keys("orphan", "test")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(prod_stage, test_stage), tombstoned=(), malformed_keys=())
    confirmations = []
    mocker.patch("builtins.input", side_effect=lambda prompt: confirmations.append(prompt) or "typo")
    output = StringIO()

    with pytest.raises(CommandError, match="data plane confirmation mismatch"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
            stdout=output,
        )

    printed = output.getvalue()
    assert confirmations
    assert (
        f"apply_target data_plane_id={data_plane.id} data_plane_name={data_plane.name} "
        "gateway_count=1 stage_count=2 key_count=2"
    ) in printed
    assert f"apply_target gateway=orphan stage=prod key_prefix={prod_stage.key_prefix} key_count=1" in printed
    assert f"apply_target gateway=orphan stage=test key_prefix={test_stage.key_prefix} key_count=1" in printed


def test_apply_scan_output_is_not_labeled_as_dry_run(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value="typo")
    output = StringIO()

    with pytest.raises(CommandError, match="data plane confirmation mismatch"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
            stdout=output,
        )

    printed = output.getvalue()
    assert "dry_run=false status=actionable gateway=orphan stage=prod key_count=1" in printed
    assert "dry_run=true" not in printed


def test_raise_cleanup_failed_is_annotated_as_no_return():
    assert cleanup_command.Command._raise_cleanup_failed.__annotations__["return"] is NoReturn


def test_command_module_carries_blueking_license_header():
    header = Path(cleanup_command.__file__).read_text(encoding="utf-8").split("import ", 1)[0]

    assert header.startswith("#\n# TencentBlueKing is pleased to support the open source community by making")
    assert "Licensed under the MIT License" in header


def test_apply_failure_does_not_expose_exception_payload(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    sentinel = "SENTINEL-SECRET-VALUE"
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=data_plane.name)
    mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically",
        side_effect=RuntimeError(f"payload password={sentinel}"),
    )
    audit_file = tmp_path / "audit.jsonl"
    output = StringIO()

    with pytest.raises(CommandError) as exc_info:
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
            stdout=output,
        )

    audit_line = audit_file.read_text()
    assert sentinel not in str(exc_info.value)
    assert sentinel not in audit_line
    assert sentinel not in output.getvalue()
    audit = json.loads(audit_line)
    assert audit["result"] == "failed"
    assert audit["error_type"] == "RuntimeError"
    assert audit["reason"] == "atomic_replace_failed"
    assert audit["mutation_state"] == "outcome_unknown"
    assert audit["data_plane_id"] == data_plane.id
    assert audit["data_plane_name"] == data_plane.name
    assert audit["key_prefix"] == stage.key_prefix
    assert exc_info.value.__cause__ is None
    assert sentinel not in "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))


def test_apply_fails_audit_when_post_write_read_finds_extra_key(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    tombstone_key = f"{stage.key_prefix}_bk_release/bk.release.orphan.prod"
    extra_key = f"{stage.key_prefix}route/route-2"
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    etcd_client = mocker.Mock()
    etcd_client.get_prefix.return_value = [make_etcd_item(tombstone_key), make_etcd_item(extra_key)]
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    mocker.patch("apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically")
    audit_file = tmp_path / "audit.jsonl"
    output = StringIO()

    with pytest.raises(CommandError):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
            stdout=output,
        )

    audit = json.loads(audit_file.read_text())
    assert audit["result"] == "failed"
    assert audit["reason"] == "post_write_key_verification_failed"
    assert audit["mutation_state"] == "committed"
    assert "cleanup_applied" not in output.getvalue()


def test_apply_fails_audit_when_post_write_payload_is_not_tombstone(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    tombstone_key = f"{stage.key_prefix}_bk_release/bk.release.orphan.prod"
    etcd_client = mocker.Mock()
    etcd_client.get_prefix.side_effect = [
        [make_etcd_item(stage.keys[0])],
        [make_etcd_item(stage.keys[0])],
        [make_etcd_item(tombstone_key)],
    ]
    etcd_client.get.return_value = (b'{"publish_id": -2}', object())
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    mocker.patch("apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically")
    audit_file = tmp_path / "audit.jsonl"
    output = StringIO()

    with pytest.raises(CommandError):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
            stdout=output,
        )

    audit = json.loads(audit_file.read_text())
    assert audit["result"] == "failed"
    assert audit["reason"] == "post_write_tombstone_verification_failed"
    assert audit["mutation_state"] == "committed"
    assert "cleanup_applied" not in output.getvalue()


def test_apply_aborts_if_gateway_reappears_before_transaction(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    # 选中阶段查询数据库时网关还不存在，进入 cleanup_stage 复查时网关已重新出现
    gateway_filter = mocker.patch(f"{COMMAND_MODULE}.Gateway.objects.filter")
    gateway_filter.return_value.values_list.return_value = []
    gateway_filter.return_value.exists.return_value = True
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    mocker.patch("builtins.input", return_value=data_plane.name)

    with pytest.raises(CommandError, match="cleanup failed"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )
    replace.assert_not_called()
    audit = json.loads((tmp_path / "audit.jsonl").read_text())
    assert audit["reason"] == "gateway_reappeared"
    assert audit["mutation_state"] == "not_started"


def test_apply_aborts_if_stage_snapshot_changes(data_plane, mocker, tmp_path):
    initial = make_stage_keys("orphan", "prod")
    changed = make_stage_keys(
        "orphan",
        "prod",
        keys=(*initial.keys, initial.keys[0].replace("route-1", "route-2")),
    )
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(initial,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(actionable=(changed,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )

    with pytest.raises(CommandError, match="cleanup failed"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )
    replace.assert_not_called()
    audit = json.loads((tmp_path / "audit.jsonl").read_text())
    assert audit["reason"] == "stage_snapshot_changed"
    assert audit["mutation_state"] == "not_started"


def test_apply_rechecks_only_the_target_stage_prefix(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    tombstone_key = f"{stage.key_prefix}_bk_release/bk.release.orphan.prod"
    etcd_client = mocker.Mock()
    etcd_client.get_prefix.side_effect = [
        [make_etcd_item(stage.keys[0])],
        [make_etcd_item(stage.keys[0])],
        [make_etcd_item(tombstone_key)],
    ]
    etcd_client.get.return_value = (
        cleanup_command.build_delete_release(stage, data_plane.apisix_version).model_dump_json().encode(),
        object(),
    )
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=etcd_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    mocker.patch("apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically")

    call_command(
        COMMAND_NAME,
        data_plane_name=data_plane.name,
        gateway_names="orphan",
        apply=True,
        log_file=str(tmp_path / "audit.jsonl"),
    )

    list_calls = [(call.args, call.kwargs) for call in etcd_client.get_prefix.call_args_list]
    assert list_calls == [
        ((f"{gateway_root(data_plane)}/",), {"keys_only": True}),
        ((stage.key_prefix,), {"keys_only": True}),
        ((stage.key_prefix,), {"keys_only": True}),
    ]


def test_apply_aborts_when_malformed_key_appears_under_target_stage(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(
        actionable=(stage,),
        tombstoned=(),
        malformed_keys=(f"{stage.key_prefix}route/route-1/extra",),
    )
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    audit_file = tmp_path / "audit.jsonl"

    with pytest.raises(CommandError, match="cleanup failed"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
        )

    replace.assert_not_called()
    audit = json.loads(audit_file.read_text())
    assert audit["reason"] == "stage_malformed_keys"
    assert audit["mutation_state"] == "not_started"


def test_apply_aborts_when_stage_recheck_read_fails(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.side_effect = TimeoutError("etcd timeout")
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )
    audit_file = tmp_path / "audit.jsonl"
    output = StringIO()

    with pytest.raises(CommandError) as exc_info:
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(audit_file),
            stdout=output,
        )

    replace.assert_not_called()
    assert "etcd timeout" not in str(exc_info.value)
    audit = json.loads(audit_file.read_text())
    assert audit["reason"] == "stage_recheck_failed"
    assert audit["mutation_state"] == "not_started"
    assert audit["error_type"] == "TimeoutError"


def test_apply_stops_after_first_transaction_failure(data_plane, mocker, tmp_path):
    first = make_stage_keys("orphan", "prod")
    second = make_stage_keys("orphan", "test")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(first, second),
        tombstoned=(),
        malformed_keys=(),
    )
    scanner.scan_stage.return_value = ScanResult(actionable=(first, second), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically",
        side_effect=TimeoutError("etcd timeout"),
    )

    with pytest.raises(CommandError, match="cleanup failed"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )
    assert replace.call_count == 1
    audit = json.loads((tmp_path / "audit.jsonl").read_text().splitlines()[0])
    assert audit["result"] == "failed"
    assert audit["reason"] == "atomic_replace_failed"
    assert audit["mutation_state"] == "outcome_unknown"


def test_apply_rejects_tombstoned_gateway_as_not_actionable(data_plane, mocker, tmp_path):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(),
        tombstoned=(make_stage_keys("cleaned", "prod"),),
        malformed_keys=(),
    )

    with pytest.raises(CommandError, match="requested gateways are not actionable"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="cleaned",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )


def test_apply_stops_before_second_gateway_after_first_gateway_failure(data_plane, mocker, tmp_path):
    first = make_stage_keys("alpha", "prod")
    second = make_stage_keys("beta", "prod")
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(first, second),
        tombstoned=(),
        malformed_keys=(),
    )
    scanner.scan_stage.return_value = ScanResult(actionable=(first, second), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=data_plane.name)
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically",
        side_effect=TimeoutError("etcd timeout"),
    )

    with pytest.raises(CommandError, match="cleanup failed"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="alpha,beta",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )

    assert replace.call_count == 1
    audit_lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    assert len(audit_lines) == 1
    audit = json.loads(audit_lines[0])
    assert audit["gateway_name"] == "alpha"
    assert audit["result"] == "failed"
    assert audit["reason"] == "atomic_replace_failed"
    assert audit["mutation_state"] == "outcome_unknown"


def test_apply_failure_audit_write_error_reports_safe_identity_on_stderr(data_plane, mocker, tmp_path):
    stage = make_stage_keys("orphan", "prod")
    sentinel = "AUDIT-WRITE-SENTINEL"
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    scanner.scan_stage.return_value = ScanResult(actionable=(stage,), tombstoned=(), malformed_keys=())
    mocker.patch("builtins.input", return_value=data_plane.name)
    mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically",
        side_effect=TimeoutError(f"etcd timeout {sentinel}"),
    )
    mocker.patch(f"{COMMAND_MODULE}.AuditWriter.write", side_effect=OSError(f"payload password {sentinel}"))
    output = StringIO()
    errors = StringIO()

    with pytest.raises(CommandError) as exc_info:
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
            stdout=output,
            stderr=errors,
        )

    reported = errors.getvalue()
    assert (
        "audit_write_failed action=cleanup_orphaned_gateway_etcd "
        f"data_plane_name={data_plane.name} gateway=orphan stage=prod "
        "reason=atomic_replace_failed mutation_state=outcome_unknown" in reported
    )
    assert sentinel not in reported
    assert "audit log write failed" in str(exc_info.value)
    assert sentinel not in str(exc_info.value)
    assert sentinel not in output.getvalue()
    assert exc_info.value.__cause__ is None
    assert sentinel not in "".join(traceback.format_exception(exc_info.type, exc_info.value, exc_info.tb))


@pytest.fixture
def fake_etcd_keyspace(fake_gateway, data_plane):
    root = f"{gateway_root(data_plane)}/"
    return {
        f"{root}orphan/prod/route/route-1": "route-1-secret-value",
        f"{root}orphan/prod/route/route-2": "route-2-secret-value",
        f"{root}orphan/prod/service/service-1": "service-1-secret-value",
        f"{root}orphan/prod/_bk_release/bk.release.orphan.prod": '{"publish_id": 100}',
        # 已清理的兄弟环境：合法墓碑，必须保持原样
        f"{root}orphan/prod2/_bk_release/bk.release.orphan.prod2": make_delete_release_payload(
            "orphan",
            "prod2",
            "3.2",
            resource_version="20260101120000",
        ),
        # 前缀相邻的其他网关：必须保留
        f"{root}orphan-2/prod/route/route-1": "sibling-dash-value",
        f"{root}orphanx/prod/route/route-1": "sibling-suffix-value",
        # 数据库中仍存在的网关：必须保留
        f"{root}{fake_gateway.name}/prod/route/route-1": "existing-gateway-value",
    }


def test_dry_run_with_fake_etcd_does_not_change_the_keyspace(fake_gateway, data_plane, mocker, fake_etcd_keyspace):
    fake_client = FakeEtcdClient(fake_etcd_keyspace)
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=fake_client)
    output = StringIO()

    call_command(COMMAND_NAME, data_plane_name=data_plane.name, stdout=output)

    assert fake_client.keys == sorted(fake_etcd_keyspace)
    assert fake_client.transaction_ops == []
    printed = output.getvalue()
    assert "dry_run=true status=actionable gateway=orphan stage=prod key_count=4" in printed
    assert "dry_run=true status=tombstoned gateway=orphan stage=prod2 key_count=1" in printed
    assert "dry_run=true status=actionable gateway=orphan-2 stage=prod key_count=1" in printed
    assert "dry_run=true status=actionable gateway=orphanx stage=prod key_count=1" in printed
    assert "dry_run=true summary actionable=3 tombstoned=1 malformed=0" in printed
    assert fake_gateway.name not in printed


def test_apply_with_fake_etcd_leaves_one_tombstone_and_keeps_sibling_keys(
    fake_gateway,
    data_plane,
    mocker,
    tmp_path,
    fake_etcd_keyspace,
):
    root = f"{gateway_root(data_plane)}/"
    stage_prefix = f"{root}orphan/prod/"
    tombstone_key = f"{stage_prefix}_bk_release/bk.release.orphan.prod"
    fake_client = FakeEtcdClient(fake_etcd_keyspace)
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=fake_client)
    mocker.patch("builtins.input", return_value=data_plane.name)
    audit_file = tmp_path / "audit.jsonl"
    output = StringIO()

    call_command(
        COMMAND_NAME,
        data_plane_name=data_plane.name,
        gateway_names="orphan",
        apply=True,
        log_file=str(audit_file),
        stdout=output,
    )

    assert fake_client.keys == sorted(
        [
            f"{root}orphan-2/prod/route/route-1",
            tombstone_key,
            f"{root}orphan/prod2/_bk_release/bk.release.orphan.prod2",
            f"{root}orphanx/prod/route/route-1",
            f"{root}{fake_gateway.name}/prod/route/route-1",
        ]
    )

    tombstone_payload, _ = fake_client.get(tombstone_key)
    tombstone = json.loads(tombstone_payload)
    assert tombstone["id"] == "bk.release.orphan.prod"
    assert tombstone["publish_id"] == DELETE_PUBLISH_ID
    assert tombstone["resource_version"] == "orphan-cleanup"
    assert tombstone["labels"][LABEL_KEY_PUBLISH_ID] == str(DELETE_PUBLISH_ID)

    sibling_tombstone, _ = fake_client.get(f"{root}orphan/prod2/_bk_release/bk.release.orphan.prod2")
    assert sibling_tombstone == fake_etcd_keyspace[f"{root}orphan/prod2/_bk_release/bk.release.orphan.prod2"]

    assert len(fake_client.transaction_ops) == 1
    ops = fake_client.transaction_ops[0]
    delete_ranges = get_delete_ranges(ops)
    assert get_put_keys(ops) == [tombstone_key.encode()]
    assert delete_ranges == [
        (stage_prefix.encode(), tombstone_key.encode()),
        (tombstone_key.encode() + b"\x00", prefix_range_end(stage_prefix.encode())),
    ]
    assert not [(start, end) for start, end in delete_ranges if in_range(tombstone_key.encode(), start, end)]
    assert not [
        (first, second)
        for index, first in enumerate(delete_ranges)
        for second in delete_ranges[index + 1 :]
        if ranges_overlap(first, second)
    ]

    audit_line = audit_file.read_text().strip()
    audit = json.loads(audit_line)
    assert audit["result"] == "success"
    assert audit["data_plane_id"] == data_plane.id
    assert audit["data_plane_name"] == data_plane.name
    assert audit["gateway_name"] == "orphan"
    assert audit["stage_name"] == "prod"
    assert audit["key_prefix"] == stage_prefix
    assert audit["previous_key_count"] == 4
    assert "secret-value" not in audit_line

    printed = output.getvalue()
    assert f"cleanup_applied gateway=orphan stage=prod key_prefix={stage_prefix}" in printed
    assert "cleaned_stage_count=1" in printed
    assert "asynchronous" in printed
    assert "secret-value" not in printed


def test_apply_with_fake_etcd_is_idempotent_for_tombstoned_stage(data_plane, mocker, tmp_path, fake_etcd_keyspace):
    fake_client = FakeEtcdClient(fake_etcd_keyspace)
    mocker.patch(f"{COMMAND_MODULE}.new_etcd_client", return_value=fake_client)
    mocker.patch("builtins.input", return_value=data_plane.name)

    call_command(
        COMMAND_NAME,
        data_plane_name=data_plane.name,
        gateway_names="orphan",
        apply=True,
        log_file=str(tmp_path / "audit.jsonl"),
    )
    keys_after_first_run = fake_client.keys

    with pytest.raises(CommandError, match="requested gateways are not actionable: orphan"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )

    assert fake_client.keys == keys_after_first_run
    assert len(fake_client.transaction_ops) == 1


def test_apply_rejects_batch_when_any_requested_gateway_is_not_actionable(data_plane, mocker, tmp_path):
    scanner = mocker.patch(f"{COMMAND_MODULE}.OrphanGatewayEtcdScanner").return_value
    scanner.scan.return_value = ScanResult(
        actionable=(make_stage_keys("orphan", "prod"),),
        tombstoned=(),
        malformed_keys=(),
    )
    replace = mocker.patch(
        "apigateway.controller.registry.etcd.EtcdRegistry.replace_resources_by_key_prefix_atomically"
    )

    with pytest.raises(CommandError, match="requested gateways are not actionable: missing"):
        call_command(
            COMMAND_NAME,
            data_plane_name=data_plane.name,
            gateway_names="orphan,missing",
            apply=True,
            log_file=str(tmp_path / "audit.jsonl"),
        )

    replace.assert_not_called()
