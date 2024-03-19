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
import csv
import logging
import time

from blue_krill.async_utils.django_utils import delay_on_commit
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log
from apigateway.controller.tasks import revoke_release, rolling_update_release
from apigateway.core.constants import APIStatusEnum
from apigateway.core.models import Gateway
from apigateway.core.signals import reversion_update_signal
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)


def _update_micro_gateway_release(instance: Gateway):
    if not instance.is_micro_gateway:
        return

    if instance.is_active:
        delay_on_commit(rolling_update_release, gateway_id=instance.pk)
    else:
        delay_on_commit(revoke_release, gateway_id=instance.pk)


class Command(BaseCommand):
    """批量停用网关"""

    def add_arguments(self, parser):
        parser.add_argument("--file-path", type=str, dest="file_path", required=True)
        parser.add_argument("--dry-run", action="store_true", dest="dry_run", required=False)

    def handle(self, file_path: str, dry_run: bool, **options):
        gateways = []
        # read the csv file
        with open(file_path, "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                name = row[0]
                desc = row[1]
                maintainers = row[4]
                operate = row[8]

                if operate == "待停用" or operate == "待删除":
                    gateways.append(
                        {
                            "name": name,
                            "desc": desc,
                            "maintainers": maintainers,
                            "operate": operate,
                        }
                    )

        assert len(gateways) == 299

        for gateway in gateways:
            print("-" * 20)
            print(f"process gateway: {gateway}")
            g = Gateway.objects.filter(name=gateway["name"]).first()
            if not g:
                print(f"gateway not found: {gateway['name']}")
                continue
            if g.status == APIStatusEnum.INACTIVE.value:
                print(f"gateway already inactive: {gateway['name']}")
                continue

            if dry_run:
                print(f"dry run, skip deactivate gateway: {gateway['name']}")
                continue
            else:
                username = "system_deactivate"
                print(f"deactivate gateway: {gateway['name']}")
                # 1. save instance
                g.status = APIStatusEnum.INACTIVE.value
                g.updated_by = username
                g.updated_time = now_datetime()
                g.save()

                # 2. send signal
                reversion_update_signal.send(sender=Gateway, instance_id=g.pk, action="update status")

                # 3. revoke micro_gateway instance released resources
                _update_micro_gateway_release(g)

                # 4. audit log
                record_audit_log(
                    username=username,
                    op_type=OpTypeEnum.MODIFY.value,
                    op_status=OpStatusEnum.SUCCESS.value,
                    op_object_group=g.pk,
                    op_object_type=OpObjectTypeEnum.API.value,
                    op_object_id=g.pk,
                    op_object=g.name,
                    comment=_("更新网关状态"),
                )
                time.sleep(2)
