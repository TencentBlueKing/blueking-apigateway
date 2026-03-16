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
from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from apigateway.core.models import Gateway


class Command(BaseCommand):
    help = "Export gateway names to a file (one name per line), for use with --gateway-names-file in other commands"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--output", type=str, required=True, help="Output file path")
        parser.add_argument(
            "--prefix", type=str, default="", help="Only export gateways whose name starts with this prefix"
        )

    def handle(self, *args, **options) -> None:
        output_path = Path(options["output"])
        prefix = options["prefix"].strip()

        qs = Gateway.objects.values_list("name", flat=True)
        if prefix:
            qs = qs.filter(name__startswith=prefix)

        names = sorted(qs)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(names) + "\n" if names else "", encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"exported {len(names)} gateway names to {output_path}"))
        if prefix:
            self.stdout.write(f"  prefix filter: {prefix}")
