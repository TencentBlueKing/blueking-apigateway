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
import pytest
from jinja2 import Template
from jinja2.exceptions import SecurityError

from apigateway.utils.jinja2 import render_to_string


class TestRenderToString:
    def test_plain_text(self):
        assert render_to_string("hello world") == "hello world"

    def test_variable_substitution(self):
        assert render_to_string("hello {{ name }}", name="world") == "hello world"

    def test_multiple_variables(self):
        result = render_to_string("{{ greeting }}, {{ name }}!", greeting="hi", name="alice")
        assert result == "hi, alice!"

    def test_with_filter(self):
        assert render_to_string("{{ name | upper }}", name="alice") == "ALICE"

    def test_loop(self):
        result = render_to_string("{% for i in items %}{{ i }} {% endfor %}", items=[1, 2, 3])
        assert result == "1 2 3 "

    def test_condition(self):
        result = render_to_string("{% if show %}visible{% endif %}", show=True)
        assert result == "visible"

    def test_empty_template(self):
        assert render_to_string("") == ""

    @pytest.mark.parametrize(
        "source, kwargs",
        [
            ("hello world", {}),
            ("{{ name }}", {"name": "alice"}),
            ("{{ name | upper }}", {"name": "alice"}),
            ("{{ name | default('N/A') }}", {}),
            ("{% for i in items %}{{ i }},{% endfor %}", {"items": [1, 2, 3]}),
            ("{% if flag %}yes{% else %}no{% endif %}", {"flag": True}),
            ("{% if flag %}yes{% else %}no{% endif %}", {"flag": False}),
            (
                "{%- if verified_app_required or verified_user_required %}"
                "| bk_app_code | string | required |"
                "{%- if verified_app_required and verified_user_required %}"
                "| access_token | string | optional |"
                "{%- endif %}"
                "{%- endif %}",
                {"verified_app_required": True, "verified_user_required": True},
            ),
            (
                "ticket={{ settings.BK_LOGIN_TICKET_KEY }}",
                {"settings": type("S", (), {"BK_LOGIN_TICKET_KEY": "bk_ticket"})()},
            ),
            (
                "{%- if docs_urls.USE_GATEWAY_API %}[link]({{ docs_urls.USE_GATEWAY_API }}){%- endif %}",
                {"docs_urls": {"USE_GATEWAY_API": "https://example.com"}},
            ),
        ],
    )
    def test_output_matches_original_template(self, source, kwargs):
        """Sandboxed render must produce identical output to the old jinja2.Template() path."""
        expected = Template(source).render(**kwargs)
        assert render_to_string(source, **kwargs) == expected

    def test_sandbox_blocks_dunder_access(self):
        with pytest.raises(SecurityError):
            render_to_string("{{ ''.__class__.__mro__[1].__subclasses__() }}")

    def test_sandbox_blocks_attr_globals(self):
        with pytest.raises(SecurityError):
            render_to_string("{{ config.__class__.__init__.__globals__ }}")
