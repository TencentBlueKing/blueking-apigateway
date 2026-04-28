# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import os
import tarfile
import zipfile

import pytest
from ddf import G
from django.core.management.base import CommandError

from apigateway.apps.support.constants import DocArchiveTypeEnum
from apigateway.apps.support.management.commands.export_released_resource_doc import Command
from apigateway.apps.support.models import ResourceDocVersion
from apigateway.core.models import ResourceVersion

pytestmark = pytest.mark.django_db


class TestCommand:
    def test_gateway_not_found(self):
        with pytest.raises(CommandError, match="Gateway not found"):
            Command().handle(
                gateway_name="not-exist", resource_version="1.0.0", output="/tmp/test.zip", file_type="zip"
            )

    def test_resource_version_not_found(self, fake_gateway):
        with pytest.raises(CommandError, match="ResourceVersion not found"):
            Command().handle(
                gateway_name=fake_gateway.name, resource_version="1.0.0", output="/tmp/test.zip", file_type="zip"
            )

    def test_resource_doc_version_not_found(self, fake_gateway):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps([{"id": 1, "name": "test"}]),
        )
        with pytest.raises(CommandError, match="ResourceDocVersion not found"):
            Command().handle(
                gateway_name=fake_gateway.name,
                resource_version=resource_version.version,
                output="/tmp/test.zip",
                file_type="zip",
            )

    def test_no_resource_docs(self, fake_gateway):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps([{"id": 1, "name": "test"}]),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=resource_version,
            _data=json.dumps([]),
        )
        with pytest.raises(CommandError, match="No resource docs found"):
            Command().handle(
                gateway_name=fake_gateway.name,
                resource_version=resource_version.version,
                output="/tmp/test.zip",
                file_type="zip",
            )

    def test_export_success_zip(self, fake_gateway, tmp_path):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps([{"id": 1, "name": "hello"}]),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=resource_version,
            _data=json.dumps([{"resource_id": 1, "language": "zh", "content": "# Hello", "type": "markdown"}]),
        )
        output = str(tmp_path / "test.zip")

        Command().handle(
            gateway_name=fake_gateway.name,
            resource_version=resource_version.version,
            output=output,
            file_type=DocArchiveTypeEnum.ZIP.value,
        )

        assert os.path.exists(output)
        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert "zh/hello.md" in names
            assert zf.read("zh/hello.md").decode("utf-8") == "# Hello"

    def test_export_success_tgz(self, fake_gateway, tmp_path):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="2.0.0",
            _data=json.dumps([{"id": 2, "name": "world"}]),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=resource_version,
            _data=json.dumps([{"resource_id": 2, "language": "en", "content": "# World", "type": "markdown"}]),
        )
        output = str(tmp_path / "test.tgz")

        Command().handle(
            gateway_name=fake_gateway.name,
            resource_version=resource_version.version,
            output=output,
            file_type=DocArchiveTypeEnum.TGZ.value,
        )

        assert os.path.exists(output)

        with tarfile.open(output, "r:gz") as tf:
            names = tf.getnames()
            assert "en/world.md" in names
            assert tf.extractfile("en/world.md").read().decode("utf-8") == "# World"

    def test_export_skip_unknown_resource_id(self, fake_gateway, tmp_path, capsys):
        resource_version = G(
            ResourceVersion,
            gateway=fake_gateway,
            version="1.0.0",
            _data=json.dumps([{"id": 1, "name": "hello"}]),
        )
        G(
            ResourceDocVersion,
            gateway=fake_gateway,
            resource_version=resource_version,
            _data=json.dumps(
                [
                    {"resource_id": 1, "language": "zh", "content": "# Hello", "type": "markdown"},
                    {"resource_id": 999, "language": "zh", "content": "# Unknown", "type": "markdown"},
                ]
            ),
        )
        output = str(tmp_path / "test.zip")

        Command().handle(
            gateway_name=fake_gateway.name,
            resource_version=resource_version.version,
            output=output,
            file_type="zip",
        )

        captured = capsys.readouterr()
        assert "Resource name not found for resource_id=999" in captured.out
        assert os.path.exists(output)
        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert "zh/hello.md" in names
            assert "zh/unknown.md" not in names
