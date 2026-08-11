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
import csv
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.metrics.models import StatisticsGatewayRequestByDay
from apigateway.core.models import Resource

pytestmark = pytest.mark.django_db

COMMAND_NAME = "list_inactive_resources"


def test_list_inactive_resources_by_gateway_names(fake_gateway, fake_resource, fake_stage, tmp_path):
    active_resource = fake_resource
    inactive_resource = G(
        Resource,
        gateway=fake_gateway,
        name="inactive-resource",
        method="GET",
        path="/inactive/",
    )

    now = timezone.now()
    StatisticsGatewayRequestByDay.objects.create(
        gateway_id=fake_gateway.id,
        stage_name=fake_stage.name,
        resource_id=active_resource.id,
        total_count=10,
        failed_count=0,
        total_msecs=100,
        start_time=now - timedelta(days=1),
        end_time=now - timedelta(days=1),
    )
    StatisticsGatewayRequestByDay.objects.create(
        gateway_id=fake_gateway.id,
        stage_name=fake_stage.name,
        resource_id=inactive_resource.id,
        total_count=5,
        failed_count=0,
        total_msecs=50,
        start_time=now - timedelta(days=40),
        end_time=now - timedelta(days=40),
    )

    output = StringIO()
    call_command(
        COMMAND_NAME,
        gateway_names=[fake_gateway.name],
        days=30,
        output_dir=str(tmp_path),
        stdout=output,
    )

    csv_files = list(tmp_path.glob("inactive_resources_*.csv"))
    assert len(csv_files) == 1

    with csv_files[0].open(encoding="utf-8-sig") as csvfile:
        rows = list(csv.DictReader(csvfile))

    assert len(rows) == 1
    assert rows[0]["resource_id"] == str(inactive_resource.id)
    assert rows[0]["resource_name"] == inactive_resource.name
    assert rows[0]["last_request_time"] != ""
    assert "过去 30 天无请求记录的资源数: 1" in output.getvalue()


def test_list_inactive_resources_by_gateway_names_file(fake_gateway, fake_resource, fake_stage, tmp_path):
    StatisticsGatewayRequestByDay.objects.create(
        gateway_id=fake_gateway.id,
        stage_name=fake_stage.name,
        resource_id=fake_resource.id,
        total_count=1,
        failed_count=0,
        total_msecs=10,
        start_time=timezone.now() - timedelta(days=1),
        end_time=timezone.now() - timedelta(days=1),
    )

    names_file = tmp_path / "gateway_names.txt"
    names_file.write_text(f"{fake_gateway.name}\n", encoding="utf-8")

    call_command(
        COMMAND_NAME,
        gateway_names_file=str(names_file),
        days=30,
        output_dir=str(tmp_path),
    )

    csv_files = list(tmp_path.glob("inactive_resources_*.csv"))
    assert len(csv_files) == 1
    with csv_files[0].open(encoding="utf-8-sig") as csvfile:
        rows = list(csv.DictReader(csvfile))
    assert rows == []


def test_list_inactive_resources_missing_gateway(tmp_path):
    with pytest.raises(CommandError, match="no gateway names provided"):
        call_command(
            COMMAND_NAME,
            days=30,
            output_dir=str(tmp_path),
        )
