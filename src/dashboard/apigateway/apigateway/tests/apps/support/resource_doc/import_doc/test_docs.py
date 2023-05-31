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
import os
from tempfile import TemporaryDirectory

import pytest

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc, BaseDoc
from apigateway.utils.file import write_to_file


class TestBaseDoc:
    @pytest.mark.parametrize(
        "language, resource_id, expected",
        [
            (
                DocLanguageEnum.EN,
                None,
                None,
            ),
            (
                DocLanguageEnum.EN,
                1,
                "1:en",
            ),
            (
                DocLanguageEnum.ZH,
                1,
                "1:zh",
            ),
        ],
    )
    def test_doc_key(self, language, resource_id, expected):
        doc = BaseDoc(language, "", resource_id=resource_id)
        assert doc.doc_key == expected


class TestArchiveDoc:
    def test_resource_doc_markdown(self):
        with TemporaryDirectory() as output_dir:
            f1_path = os.path.join(output_dir, "get_user.md.j2")
            f2_path = os.path.join(output_dir, "create_user.md")

            write_to_file("get_user", f1_path)
            write_to_file("create_user", f2_path)

            doc = ArchiveDoc(
                language=DocLanguageEnum.ZH,
                resource_name="get_user",
                resource_doc_path=f1_path,
            )
            assert doc.resource_doc_markdown == "get_user"

            doc = ArchiveDoc(
                language=DocLanguageEnum.ZH,
                resource_name="create_user",
                resource_doc_path=f2_path,
            )
            assert doc.resource_doc_markdown == "create_user"

    @pytest.mark.parametrize(
        "resource_doc_path, expected",
        [
            ("get_user.md.j2", True),
            ("get_user.md", False),
            ("get_user.j2", False),
        ],
    )
    def test_is_jinja2_template(self, faker, resource_doc_path, expected):
        doc = ArchiveDoc(
            language=DocLanguageEnum.ZH,
            resource_name=faker.pystr(),
            resource_doc_path=resource_doc_path,
        )
        assert doc._is_jinja2_template() == expected

    def test_render_jinja2_template(self, faker):
        with TemporaryDirectory() as output:
            path = os.path.join(output, "get_user.md.j2")
            write_to_file("{% include '_common.md.j2' %}, get_user", path)
            write_to_file("hi", os.path.join(output, "_common.md.j2"))

            doc = ArchiveDoc(language=DocLanguageEnum.ZH, resource_name=faker.pystr(), resource_doc_path=path)
            assert doc._render_jinja2_template() == "hi, get_user"
