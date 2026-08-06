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
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, NoReturn, Optional, Set, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import force_str

from apigateway.apps.data_plane.management.commands.gateway_data_plane_command_utils import parse_comma_separated_names
from apigateway.apps.data_plane.models import DataPlane
from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.convertor.constants import (
    LABEL_KEY_APISIX_VERSION,
    LABEL_KEY_GATEWAY,
    LABEL_KEY_PUBLISH_ID,
    LABEL_KEY_STAGE,
)
from apigateway.controller.convertor.utils import get_release_id
from apigateway.controller.distributor.key_prefix import GatewayKeyPrefixHandler
from apigateway.controller.models import BkRelease, Labels
from apigateway.controller.registry.etcd import AtomicReplaceConflictError, EtcdRegistry
from apigateway.core.models import Gateway
from apigateway.utils.etcd import new_etcd_client
from apigateway.utils.time import now_str

AUDIT_ACTION = "cleanup_orphaned_gateway_etcd"
DELETE_RESOURCE_VERSION = "orphan-cleanup"
APPLY_FAILURE_MESSAGE = "cleanup failed; see audit log"
ERROR_MESSAGE = "cleanup failed"
TOMBSTONE_READ_FAILED_MESSAGE = "failed to read etcd delete marker value"
MUTATION_NOT_STARTED = "not_started"
MUTATION_OUTCOME_UNKNOWN = "outcome_unknown"
MUTATION_COMMITTED = "committed"
REASON_GATEWAY_REAPPEARED = "gateway_reappeared"
REASON_STAGE_RECHECK_FAILED = "stage_recheck_failed"
REASON_STAGE_MALFORMED_KEYS = "stage_malformed_keys"
REASON_STAGE_SNAPSHOT_CHANGED = "stage_snapshot_changed"
REASON_ATOMIC_REPLACE_FAILED = "atomic_replace_failed"
REASON_POST_WRITE_KEY_VERIFICATION_FAILED = "post_write_key_verification_failed"
REASON_POST_WRITE_TOMBSTONE_VERIFICATION_FAILED = "post_write_tombstone_verification_failed"
REASON_UNEXPECTED_CLEANUP_FAILED = "unexpected_cleanup_failed"
REASON_SUCCESS_AUDIT_WRITE_FAILED = "success_audit_write_failed"
REASON_STARTED_AUDIT_WRITE_FAILED = "started_audit_write_failed"


@dataclass(frozen=True)
class StageKeys:
    gateway_name: str
    stage_name: str
    key_prefix: str
    keys: Tuple[str, ...]
    kinds: Tuple[str, ...]

    @property
    def key_count(self) -> int:
        return len(self.keys)


@dataclass(frozen=True)
class ScanResult:
    actionable: Tuple[StageKeys, ...]
    tombstoned: Tuple[StageKeys, ...]
    malformed_keys: Tuple[str, ...]
    snapshot_revision: Optional[int] = None


class TombstoneReadError(Exception):
    """读取删除标记的值失败

    这是传输层错误，与 payload 校验失败不同：无法判断 stage 是否已被清理，调用方必须中止，
    不能把 stage 当作可清理的目标。
    """

    def __init__(self):
        super().__init__(TOMBSTONE_READ_FAILED_MESSAGE)


class CleanupStageError(Exception):
    def __init__(self, reason: str, mutation_state: str, error_type: str = "CommandError"):
        super().__init__(ERROR_MESSAGE)
        self.reason = reason
        self.mutation_state = mutation_state
        self.error_type = error_type

    @classmethod
    def from_exception(cls, reason: str, mutation_state: str, err: Exception) -> "CleanupStageError":
        return cls(reason=reason, mutation_state=mutation_state, error_type=err.__class__.__name__)


class OrphanGatewayEtcdScanner:
    def __init__(self, data_plane, etcd_client):
        self.data_plane = data_plane
        self.etcd_client = etcd_client

    def scan(self, gateway_names: Optional[Set[str]] = None) -> ScanResult:
        """扫描该数据面 `/v2/gateway/` 下的全部 key"""
        return self._scan(get_gateway_root(self.data_plane), gateway_names)

    def scan_stage(self, gateway_name: str, stage_name: str) -> ScanResult:
        """只扫描单个 stage 的 key 前缀，用于执行前复查目标 stage"""
        return self._scan(
            get_stage_key_prefix(self.data_plane, gateway_name, stage_name),
            {gateway_name},
        )

    def _scan(self, list_key_prefix: str, gateway_names: Optional[Set[str]]) -> ScanResult:
        root = get_gateway_root(self.data_plane)
        grouped: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        malformed = []
        snapshot_revision = None

        for _, metadata in self.etcd_client.get_prefix(list_key_prefix, keys_only=True):
            header = getattr(metadata, "response_header", None)
            revision = getattr(header, "revision", None)
            if revision is not None:
                snapshot_revision = revision

            key = force_str(metadata.key)
            relative = key.removeprefix(root)
            parts = relative.split("/")
            if not key.startswith(root) or len(parts) != 4 or not all(parts):
                malformed.append(key)
                continue

            gateway_name, stage_name, kind, _ = parts
            if gateway_names is None or gateway_name in gateway_names:
                grouped[(gateway_name, stage_name)].append((key, kind))

        existing_names = set(
            Gateway.objects.filter(name__in={name for name, _ in grouped}).values_list("name", flat=True)
        )
        stages = [
            self._build_stage_keys(gateway_name, stage_name, entries)
            for (gateway_name, stage_name), entries in grouped.items()
            if gateway_name not in existing_names
        ]

        actionable = []
        tombstoned = []
        for stage in stages:
            if self.is_valid_tombstone(stage):
                tombstoned.append(stage)
            else:
                actionable.append(stage)

        return ScanResult(
            actionable=tuple(sorted(actionable, key=self._sort_key)),
            tombstoned=tuple(sorted(tombstoned, key=self._sort_key)),
            malformed_keys=tuple(sorted(malformed)),
            snapshot_revision=snapshot_revision,
        )

    def _build_stage_keys(self, gateway_name: str, stage_name: str, entries: List[Tuple[str, str]]) -> StageKeys:
        sorted_entries = tuple(sorted(entries, key=lambda item: item[0]))
        return StageKeys(
            gateway_name=gateway_name,
            stage_name=stage_name,
            key_prefix=get_stage_key_prefix(self.data_plane, gateway_name, stage_name),
            keys=tuple(key for key, _ in sorted_entries),
            kinds=tuple(kind for _, kind in sorted_entries),
        )

    def is_valid_tombstone(self, stage: StageKeys) -> bool:
        """判断 stage 下是否只剩一个合法的 `publish_id=-2` 删除标记

        删除标记可能由正常的删除发布写入，因此不校验 resource_version，也不要求 apisix_version
        等于当前 DataPlane 的版本（版本升级后旧标记依然有效）；只要求 payload 自身一致。

        :raises TombstoneReadError: 读取 etcd 值失败，无法判定，调用方必须中止
        """
        if stage.key_count != 1 or stage.kinds != (BkRelease.kind,):
            return False

        release_id = get_release_id(stage.gateway_name, stage.stage_name)
        if stage.keys[0] != f"{stage.key_prefix}{BkRelease.kind}/{release_id}":
            return False

        try:
            payload, _ = self.etcd_client.get(stage.keys[0])
        except Exception:
            raise TombstoneReadError() from None

        if not payload:
            return False

        try:
            release = BkRelease.model_validate_json(payload)
        except Exception:
            return False

        return (
            release.id == release_id
            and release.publish_id == DELETE_PUBLISH_ID
            and bool(release.apisix_version)
            and release.labels.get_label(LABEL_KEY_GATEWAY) == stage.gateway_name
            and release.labels.get_label(LABEL_KEY_STAGE) == stage.stage_name
            and release.labels.get_label(LABEL_KEY_PUBLISH_ID) == str(DELETE_PUBLISH_ID)
            and release.labels.get_label(LABEL_KEY_APISIX_VERSION) == release.apisix_version
        )

    @staticmethod
    def _sort_key(stage: StageKeys) -> Tuple[str, str]:
        return stage.gateway_name, stage.stage_name


def get_delete_release_id(gateway_name: str, stage_name: str) -> str:
    return get_release_id(gateway_name, stage_name)


def build_delete_release(stage: StageKeys, apisix_version: str) -> BkRelease:
    return BkRelease(
        id=get_release_id(stage.gateway_name, stage.stage_name),
        publish_id=DELETE_PUBLISH_ID,
        publish_time=now_str(),
        apisix_version=apisix_version,
        resource_version=DELETE_RESOURCE_VERSION,
        labels=Labels(
            **{
                LABEL_KEY_GATEWAY: stage.gateway_name,
                LABEL_KEY_STAGE: stage.stage_name,
                LABEL_KEY_PUBLISH_ID: DELETE_PUBLISH_ID,
                LABEL_KEY_APISIX_VERSION: apisix_version,
            }
        ),
    )


def get_stage_key_prefix(data_plane: DataPlane, gateway_name: str, stage_name: str) -> str:
    return GatewayKeyPrefixHandler(prefix=data_plane.etcd_namespace_prefix).get_release_key_prefix(
        gateway_name,
        stage_name,
    )


def get_gateway_root(data_plane: DataPlane) -> str:
    return get_stage_key_prefix(data_plane, "__gateway__", "__stage__").removesuffix("__gateway__/__stage__/")


def validate_etcd_namespace_prefix(data_plane: DataPlane) -> None:
    """空的 namespace 前缀会让扫描和删除范围扩散到 etcd 根路径，必须拒绝"""
    if not (data_plane.etcd_namespace_prefix or "").strip().strip("/"):
        raise CommandError(f"data plane etcd namespace prefix is empty: {data_plane.name}")


def cleanup_stage(stage: StageKeys, data_plane: DataPlane, etcd_client) -> None:
    if Gateway.objects.filter(name=stage.gateway_name).exists():
        raise CleanupStageError(REASON_GATEWAY_REAPPEARED, MUTATION_NOT_STARTED)

    scanner = OrphanGatewayEtcdScanner(data_plane, etcd_client)
    try:
        latest = scanner.scan_stage(stage.gateway_name, stage.stage_name)
    except Exception as err:
        raise CleanupStageError.from_exception(REASON_STAGE_RECHECK_FAILED, MUTATION_NOT_STARTED, err) from None

    if latest.malformed_keys:
        raise CleanupStageError(REASON_STAGE_MALFORMED_KEYS, MUTATION_NOT_STARTED)

    latest_stage = next(
        (
            item
            for item in latest.actionable
            if item.gateway_name == stage.gateway_name and item.stage_name == stage.stage_name
        ),
        None,
    )
    if latest_stage is None or latest_stage.keys != stage.keys:
        raise CleanupStageError(REASON_STAGE_SNAPSHOT_CHANGED, MUTATION_NOT_STARTED)

    delete_release = build_delete_release(stage, data_plane.apisix_version)
    try:
        EtcdRegistry(stage.key_prefix, etcd_client).replace_resources_by_key_prefix_atomically(
            [delete_release],
            expected_max_mod_revision=latest.snapshot_revision,
        )
    except AtomicReplaceConflictError as err:
        raise CleanupStageError.from_exception(
            REASON_ATOMIC_REPLACE_FAILED,
            MUTATION_NOT_STARTED,
            err,
        ) from None
    except Exception as err:
        raise CleanupStageError.from_exception(
            REASON_ATOMIC_REPLACE_FAILED,
            MUTATION_OUTCOME_UNKNOWN,
            err,
        ) from None

    expected_key = f"{stage.key_prefix}{BkRelease.kind}/{delete_release.id}"
    try:
        remaining_keys = tuple(
            sorted(force_str(metadata.key) for _, metadata in etcd_client.get_prefix(stage.key_prefix, keys_only=True))
        )
    except Exception as err:
        raise CleanupStageError.from_exception(
            REASON_POST_WRITE_KEY_VERIFICATION_FAILED,
            MUTATION_COMMITTED,
            err,
        ) from None
    if remaining_keys != (expected_key,):
        raise CleanupStageError(REASON_POST_WRITE_KEY_VERIFICATION_FAILED, MUTATION_COMMITTED)

    tombstone_stage = StageKeys(
        gateway_name=stage.gateway_name,
        stage_name=stage.stage_name,
        key_prefix=stage.key_prefix,
        keys=(expected_key,),
        kinds=(BkRelease.kind,),
    )
    try:
        tombstone_verified = scanner.is_valid_tombstone(tombstone_stage)
    except TombstoneReadError as err:
        raise CleanupStageError.from_exception(
            REASON_POST_WRITE_TOMBSTONE_VERIFICATION_FAILED,
            MUTATION_COMMITTED,
            err,
        ) from None

    if not tombstone_verified:
        raise CleanupStageError(REASON_POST_WRITE_TOMBSTONE_VERIFICATION_FAILED, MUTATION_COMMITTED)


class AuditWriter:
    def __init__(self, log_file: str, data_plane: DataPlane):
        self.log_file = Path(log_file)
        self.data_plane = data_plane

    def validate_writable(self) -> None:
        try:
            with self.log_file.open("a", encoding="utf-8"):
                pass
        except OSError:
            raise CommandError("audit log file is not writable") from None

    def write(
        self,
        stage: StageKeys,
        result: str,
        operator: str,
        error: Optional[CleanupStageError] = None,
        mutation_state: Optional[str] = None,
    ) -> None:
        if mutation_state is None:
            if error is not None:
                mutation_state = error.mutation_state
            elif result == "started":
                mutation_state = MUTATION_NOT_STARTED
            else:
                mutation_state = MUTATION_COMMITTED

        record = {
            "action": AUDIT_ACTION,
            "result": result,
            "data_plane_id": self.data_plane.id,
            "data_plane_name": self.data_plane.name,
            "gateway_name": stage.gateway_name,
            "mutation_state": mutation_state,
            "stage_name": stage.stage_name,
            "key_prefix": stage.key_prefix,
            "previous_key_count": stage.key_count,
            "operator": operator,
            "timestamp": now_str(),
        }
        if error is not None:
            record["reason"] = error.reason
            record["error_type"] = error.error_type
            record["error"] = ERROR_MESSAGE

        with self.log_file.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            fp.write("\n")
            fp.flush()
            os.fsync(fp.fileno())


class Command(BaseCommand):
    help = (
        "Scan orphaned gateway etcd keys for one data plane. Defaults to dry-run. "
        "--apply writes operator-compatible delete tombstones to etcd and requires "
        "--gateway-names, --log-file, and interactive confirmation of the data plane name."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-plane-name",
            required=True,
            help="Exact DataPlane.name whose control-plane etcd will be scanned or cleaned.",
        )
        parser.add_argument(
            "--gateway-names",
            default="",
            help="Comma-separated gateway names to include. Required with --apply; optional for dry-run filters.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help=(
                "Execute cleanup: writes delete tombstones to etcd for allowlisted orphan stages. "
                "Requires --gateway-names, --log-file, and typing the data plane name to confirm."
            ),
        )
        parser.add_argument(
            "--log-file",
            default="",
            help="Writable JSONL audit log path. Required with --apply.",
        )
        parser.add_argument(
            "--operator",
            default="system",
            help="Operator identity recorded in the audit log. Default: system.",
        )

    def handle(self, *args, **options):
        data_plane_name = options["data_plane_name"].strip()
        try:
            data_plane = DataPlane.objects.get(name=data_plane_name)
        except DataPlane.DoesNotExist as err:
            raise CommandError(f"data plane not found: {data_plane_name}") from err

        validate_etcd_namespace_prefix(data_plane)

        apply = options["apply"]
        parsed_gateway_names = parse_comma_separated_names(options["gateway_names"])
        log_file = options["log_file"].strip()
        if apply and not parsed_gateway_names:
            raise CommandError("--apply requires --gateway-names")
        if apply and not log_file:
            raise CommandError("--apply requires --log-file")

        gateway_names = set(parsed_gateway_names) if parsed_gateway_names else None
        etcd_client = new_etcd_client(data_plane.etcd_configs)
        try:
            result = OrphanGatewayEtcdScanner(data_plane, etcd_client).scan(gateway_names=gateway_names)
        except TombstoneReadError:
            raise CommandError(TOMBSTONE_READ_FAILED_MESSAGE) from None

        self._write_scan_result(result, dry_run=not apply)
        if not apply:
            return

        selected_stages = self._get_selected_stages(data_plane, result, set(parsed_gateway_names))
        self._write_apply_target(data_plane, selected_stages)
        self._confirm_data_plane(data_plane)

        audit_writer = AuditWriter(log_file, data_plane)
        audit_writer.validate_writable()
        self._apply_selected_stages(
            selected_stages=selected_stages,
            data_plane=data_plane,
            etcd_client=etcd_client,
            audit_writer=audit_writer,
            operator=options["operator"],
        )

    def _get_selected_stages(
        self,
        data_plane: DataPlane,
        result: ScanResult,
        requested_names: Set[str],
    ) -> List[StageKeys]:
        actionable_names = {stage.gateway_name for stage in result.actionable}
        if missing_names := sorted(requested_names - actionable_names):
            raise CommandError(f"requested gateways are not actionable: {', '.join(missing_names)}")

        existing_names = sorted(set(Gateway.objects.filter(name__in=requested_names).values_list("name", flat=True)))
        if existing_names:
            raise CommandError(f"gateway exists in database: {', '.join(existing_names)}")

        malformed_gateway_names = self._get_selected_malformed_gateway_names(
            data_plane,
            requested_names,
            result.malformed_keys,
        )
        if malformed_gateway_names:
            raise CommandError(
                f"malformed etcd keys for selected gateways: {', '.join(malformed_gateway_names)}; "
                "fix or remove them before applying"
            )

        return sorted(
            (stage for stage in result.actionable if stage.gateway_name in requested_names),
            key=lambda stage: (stage.gateway_name, stage.stage_name),
        )

    def _write_apply_target(self, data_plane: DataPlane, selected_stages: List[StageKeys]) -> None:
        self.stdout.write(
            "apply_target "
            f"data_plane_id={data_plane.id} data_plane_name={data_plane.name} "
            f"gateway_count={len({stage.gateway_name for stage in selected_stages})} "
            f"stage_count={len(selected_stages)} "
            f"key_count={sum(stage.key_count for stage in selected_stages)}"
        )
        for stage in selected_stages:
            self.stdout.write(
                f"apply_target gateway={stage.gateway_name} stage={stage.stage_name} "
                f"key_prefix={stage.key_prefix} key_count={stage.key_count}"
            )

    @staticmethod
    def _confirm_data_plane(data_plane: DataPlane) -> None:
        try:
            confirmed_data_plane_name = input(f"Type data plane name '{data_plane.name}' to continue: ").strip()
        except EOFError:
            raise CommandError("apply aborted: confirmation input is closed") from None

        if confirmed_data_plane_name != data_plane.name:
            raise CommandError("apply aborted: data plane confirmation mismatch")

    def _apply_selected_stages(
        self,
        selected_stages: List[StageKeys],
        data_plane: DataPlane,
        etcd_client,
        audit_writer: AuditWriter,
        operator: str,
    ) -> None:
        for stage in selected_stages:
            try:
                audit_writer.write(stage, "started", operator)
            except Exception:
                self._raise_audit_write_failed(
                    audit_writer,
                    stage,
                    reason=REASON_STARTED_AUDIT_WRITE_FAILED,
                    mutation_state=MUTATION_NOT_STARTED,
                )

            try:
                cleanup_stage(stage, data_plane, etcd_client)
            except CleanupStageError as err:
                self._raise_cleanup_failed(audit_writer, stage, operator, err)
            except Exception as err:
                unexpected = CleanupStageError.from_exception(
                    REASON_UNEXPECTED_CLEANUP_FAILED,
                    MUTATION_OUTCOME_UNKNOWN,
                    err,
                )
                self._raise_cleanup_failed(audit_writer, stage, operator, unexpected)

            try:
                audit_writer.write(stage, "success", operator)
            except Exception:
                self._raise_audit_write_failed(
                    audit_writer,
                    stage,
                    reason=REASON_SUCCESS_AUDIT_WRITE_FAILED,
                    mutation_state=MUTATION_COMMITTED,
                )

            self.stdout.write(
                f"cleanup_applied gateway={stage.gateway_name} stage={stage.stage_name} "
                f"key_prefix={stage.key_prefix} tombstone_verified=true control_plane_delete_event=written"
            )

        self.stdout.write(
            f"cleanup_summary data_plane_name={data_plane.name} "
            f"cleaned_stage_count={len(selected_stages)} "
            "control_plane_delete_event=written "
            "note=operator/APISIX data plane cleanup is asynchronous and not confirmed by this command"
        )

    def _raise_cleanup_failed(
        self,
        audit_writer: AuditWriter,
        stage: StageKeys,
        operator: str,
        error: CleanupStageError,
    ) -> NoReturn:
        try:
            audit_writer.write(stage, "failed", operator, error)
        except Exception:
            self._raise_audit_write_failed(
                audit_writer,
                stage,
                reason=error.reason,
                mutation_state=error.mutation_state,
            )

        raise CommandError(APPLY_FAILURE_MESSAGE) from None

    def _raise_audit_write_failed(
        self,
        audit_writer: AuditWriter,
        stage: StageKeys,
        *,
        reason: str,
        mutation_state: str,
    ) -> NoReturn:
        # 审计写入失败时，审计日志无法说明本次结果，改为向 stderr 输出固定的白名单字段；
        # 不输出第三方异常文本，避免泄露 etcd 配置或资源内容
        self.stderr.write(
            f"audit_write_failed action={AUDIT_ACTION} "
            f"data_plane_name={audit_writer.data_plane.name} "
            f"gateway={stage.gateway_name} stage={stage.stage_name} "
            f"reason={reason} mutation_state={mutation_state}"
        )
        raise CommandError(f"{ERROR_MESSAGE}; audit log write failed") from None

    @staticmethod
    def _get_selected_malformed_gateway_names(
        data_plane: DataPlane,
        gateway_names: Set[str],
        malformed_keys: Tuple[str, ...],
    ) -> List[str]:
        root = get_gateway_root(data_plane)
        selected_names = set()
        for key in malformed_keys:
            if not key.startswith(root):
                continue

            gateway_name = key.removeprefix(root).split("/", 1)[0]
            if gateway_name in gateway_names:
                selected_names.add(gateway_name)

        return sorted(selected_names)

    def _write_scan_result(self, result: ScanResult, dry_run: bool) -> None:
        prefix = f"dry_run={str(dry_run).lower()} "
        for stage in result.actionable:
            self.stdout.write(
                f"{prefix}status=actionable gateway={stage.gateway_name} stage={stage.stage_name} "
                f"key_count={stage.key_count}"
            )
        for stage in result.tombstoned:
            self.stdout.write(
                f"{prefix}status=tombstoned gateway={stage.gateway_name} stage={stage.stage_name} "
                f"key_count={stage.key_count}"
            )
        for key in result.malformed_keys:
            self.stdout.write(f"{prefix}status=malformed key={key}")

        self.stdout.write(
            f"{prefix}summary actionable={len(result.actionable)} "
            f"tombstoned={len(result.tombstoned)} "
            f"malformed={len(result.malformed_keys)}"
        )
