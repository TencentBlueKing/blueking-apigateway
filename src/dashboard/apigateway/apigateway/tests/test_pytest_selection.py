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

pytest_plugins = ["pytester"]


@pytest.mark.parametrize(
    "expression, expected_files",
    [
        ("migration", {"test_migration_unmarked.py", "test_migrations.py", "test_explicit.py"}),
        ("not migration", {"test_plain.py"}),
        ("", {"test_plain.py", "test_migration_unmarked.py", "test_migrations.py", "test_explicit.py"}),
    ],
)
def test_migration_selection_includes_unmarked_migration_files(pytester, expression, expected_files):
    pytester.makeconftest(
        """
        from apigateway.tests import conftest as project_tests

        if hasattr(project_tests, "pytest_collection_modifyitems"):
            pytest_collection_modifyitems = project_tests.pytest_collection_modifyitems
        """
    )
    pytester.makeini("[pytest]\nmarkers = migration: migration tests\n")
    pytester.makepyfile(
        test_plain="def test_plain(): pass",
        test_migration_unmarked="def test_unmarked(): pass",
        test_migrations="def test_unmarked_plural(): pass",
        test_explicit="import pytest\npytestmark = pytest.mark.migration\ndef test_marked(): pass",
    )
    args = ["--ds=apigateway.settings", "--nomigrations", "-p", "no:pretty", "-q"]
    if expression:
        args.extend(["-m", expression])

    result = pytester.inline_run("--collect-only", *args)

    assert result.ret == pytest.ExitCode.OK
    session = result.getcall("pytest_collection_finish").session
    assert {item.path.name for item in session.items} == expected_files
