"""
TencentBlueKing is pleased to support the open source community
蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
Copyright (C) 2025 Tencent. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except
in compliance with the License. You may obtain a copy of the License at

    http://opensource.org/licenses/MIT

Unless required by applicable law or agreed to in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the License for the specific language governing permissions and
limitations under the License.

We undertake not to change the open source license (MIT license) applicable
to the current version of the project delivered to anyone in the future.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict

logger = logging.getLogger(__name__)

# Global compiled regex patterns
env_regexp = re.compile(r"\{env\.(\w+)\}")
param_regexp = re.compile(r"\{(\w+)\}")


class Render(ABC):
    """Abstract base class for URI renderers."""

    @abstractmethod
    def render(self, source: str, vars: Dict[str, str]) -> str:
        """Render the source string with the provided variables."""


class URIRender(Render):
    """Renderer that converts /path/{env.varName}/{pathParamName}/xxx to /path/actualValue/:pathParamName/xxx"""

    def render(self, source: str, vars: Dict[str, str]) -> str:
        """Render the URI with environment variables and path parameters."""
        return self._param_render(env_render(source, vars))

    def _param_render(self, source: str) -> str:
        """Parameter rendering - converts {param} to :param"""
        return param_regexp.sub(r":\1", source)


class UpstreamURIRender(Render):
    """Renderer that converts /path/{env.varName}/{pathParamName}/xxx to /path/actualValue/${pathParamName}/xxx"""

    def render(self, source: str, vars: Dict[str, str]) -> str:
        """Render the upstream URI with environment variables and path parameters."""
        return self._param_render(env_render(source, vars))

    def _param_render(self, source: str) -> str:
        """Parameter rendering - converts {param} to ${param}"""
        return param_regexp.sub(r"${\1}", source)


def env_render(source: str, vars: Dict[str, str]) -> str:
    """Render environment variables in the source string."""
    all_matches = env_regexp.findall(source)
    if not all_matches:
        return source

    result = source
    missing_vars = []
    for var_name in all_matches:
        if var_name in vars:
            pattern = f"{{env.{var_name}}}"
            result = result.replace(pattern, vars[var_name])
        else:
            missing_vars.append(var_name)

    if missing_vars:
        logger.warning("Missing environment variables: %s in source: %s", missing_vars, source)

    return result


if __name__ == "__main__":
    # Example usage and testing
    vars_dict = {"stage": "prod", "version": "v1"}

    # Test URIRender
    uri_renderer = URIRender()
    source_uri = "/api/{env.stage}/{env.version}/users/{userId}/profile"
    result_uri = uri_renderer.render(source_uri, vars_dict)
    print(f"URIRender: {source_uri} -> {result_uri}")
    # Expected: /api/prod/v1/users/:userId/profile

    # Test UpstreamURIRender
    upstream_renderer = UpstreamURIRender()
    result_upstream = upstream_renderer.render(source_uri, vars_dict)
    print(f"UpstreamURIRender: {source_uri} -> {result_upstream}")
    # Expected: /api/prod/v1/users/${userId}/profile

    # Test with missing variables
    incomplete_vars = {"stage": "dev"}
    result_incomplete = uri_renderer.render(source_uri, incomplete_vars)
    print(f"With incomplete vars: {source_uri} -> {result_incomplete}")
    # Expected: /api/dev/{env.version}/users/:userId/profile
