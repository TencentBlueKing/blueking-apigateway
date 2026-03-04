#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
import json
from typing import Dict, List

from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.data_plane.constants import DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane

REQUIRED_ETCD_CONFIG_KEYS = ["host", "port", "user", "password", "ca_cret", "cert_cert", "cert_key"]


def _normalize_prefix(prefix: str) -> str:
    parts = [part for part in prefix.strip().split("/") if part]
    if not parts:
        return "/"
    return "/" + "/".join(parts)


def _is_namespace_prefix(left: str, right: str) -> bool:
    left_norm = _normalize_prefix(left)
    right_norm = _normalize_prefix(right)

    if left_norm == "/":
        return True
    if right_norm == "/":
        return False

    left_parts = [part for part in left_norm.strip("/").split("/") if part]
    right_parts = [part for part in right_norm.strip("/").split("/") if part]
    if len(left_parts) > len(right_parts):
        return False
    return right_parts[: len(left_parts)] == left_parts


class Command(BaseCommand):
    help = "Create a data plane with validated ETCD configuration"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, required=True, help="Data plane name.")
        parser.add_argument("--description", type=str, default="", help="Data plane description.")
        parser.add_argument("--bk-api-url-tmpl", type=str, required=True, help="Data plane bk_api_url_tmpl.")
        parser.add_argument(
            "--status",
            type=int,
            required=True,
            help=f"Data plane status, allowed values: {DataPlaneStatusEnum.ACTIVE.value}/{DataPlaneStatusEnum.INACTIVE.value}.",
        )
        parser.add_argument(
            "--etcd-config",
            type=str,
            required=True,
            help="ETCD config JSON string.",
        )
        parser.add_argument(
            "--etcd-namespace-prefix",
            type=str,
            required=True,
            help="ETCD namespace prefix.",
        )
        parser.add_argument("--created-by", type=str, default="system", help="Creator username.")

    def _validate_required_non_empty(self, name: str, value: str):
        if not value or not value.strip():
            raise CommandError(f"{name} should not be empty")

    def _parse_etcd_config(self, etcd_config_raw: str) -> Dict:
        try:
            value = json.loads(etcd_config_raw)
        except json.JSONDecodeError as err:
            raise CommandError(f"etcd_config is not valid JSON: {err}") from err

        if not isinstance(value, dict):
            raise CommandError("etcd_config should be a JSON object")

        missing_keys: List[str] = [key for key in REQUIRED_ETCD_CONFIG_KEYS if key not in value]
        if missing_keys:
            raise CommandError(f"etcd_config missing required keys: {', '.join(missing_keys)}")
        return value

    def _validate_status(self, status: int):
        allowed = set(DataPlaneStatusEnum.get_values())
        if status not in allowed:
            raise CommandError(f"status should be one of: {sorted(allowed)}")

    def _validate_etcd_conflicts(self, etcd_config: Dict, etcd_namespace_prefix: str):
        normalized_prefix = _normalize_prefix(etcd_namespace_prefix)

        for existed in DataPlane.objects.all():
            try:
                existed_etcd_config = existed.etcd_configs
            except Exception:
                continue

            if existed_etcd_config != etcd_config:
                continue

            existed_prefix = _normalize_prefix(existed.etcd_namespace_prefix)
            if existed_prefix == normalized_prefix:
                raise CommandError(
                    "etcd_config is the same as existing data_plane "
                    f"[name={existed.name}] and etcd_namespace_prefix is also the same: {normalized_prefix}"
                )

            if _is_namespace_prefix(existed_prefix, normalized_prefix) or _is_namespace_prefix(
                normalized_prefix, existed_prefix
            ):
                raise CommandError(
                    "etcd_config is the same as existing data_plane "
                    f"[name={existed.name}] and namespace prefix overlaps: "
                    f"existing={existed_prefix}, input={normalized_prefix}"
                )

            self.stdout.write(
                self.style.WARNING(
                    "Warning: etcd_config is the same as existing data_plane "
                    f"[name={existed.name}], but etcd_namespace_prefix is different."
                )
            )

    def handle(self, *args, **options):
        name = options["name"]
        description = options["description"]
        bk_api_url_tmpl = options["bk_api_url_tmpl"]
        status = options["status"]
        etcd_namespace_prefix = options["etcd_namespace_prefix"]
        created_by = options["created_by"]

        self._validate_required_non_empty("name", name)
        self._validate_required_non_empty("bk_api_url_tmpl", bk_api_url_tmpl)
        self._validate_required_non_empty("etcd_namespace_prefix", etcd_namespace_prefix)
        self._validate_status(status)

        if DataPlane.objects.filter(name=name).exists():
            raise CommandError(f"data_plane name already exists: {name}")

        etcd_config = self._parse_etcd_config(options["etcd_config"])
        self._validate_etcd_conflicts(etcd_config, etcd_namespace_prefix)

        data_plane = DataPlane(
            name=name.strip(),
            description=description,
            bk_api_url_tmpl=bk_api_url_tmpl.strip(),
            etcd_namespace_prefix=_normalize_prefix(etcd_namespace_prefix),
            status=status,
            created_by=created_by,
            updated_by=created_by,
        )
        data_plane.etcd_configs = etcd_config
        data_plane.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Data plane created successfully: id={data_plane.id}, name={data_plane.name}, status={data_plane.status}"
            )
        )
