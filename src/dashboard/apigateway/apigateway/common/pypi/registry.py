from typing import Any

from packaging.version import parse as parse_version
from pypi_simple import PyPISimple


class SimplePypiRegistry:
    def __init__(self, index_url: str, auth: Any = None):
        self.index_url = index_url
        self.auth = auth

    @property
    def _simple_client(self):
        return PyPISimple(self.index_url, self.auth)

    def _iter_packages(self, name: str, include_yanked: bool):
        with self._simple_client as client:
            page = client.get_project_page(name)

        if page is None:
            return

        for p in page.packages:
            if p.yanked and not include_yanked:
                continue

            if not p.version:
                continue

            version = parse_version(p.version)
            yield version, p

    def search(self, name: str, version: str = "", package_type: str = ""):
        """查找满足指定规则的包"""

        target_version = None
        if version:
            # 此处必须转换，规则：https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
            target_version = parse_version(version)

        package = None
        last_version = None

        for v, p in self._iter_packages(name, False):
            if package_type and p.package_type != package_type:
                continue

            # 指定了版本号，说明只查询指定版本
            if v == target_version:
                return p

            if last_version is None or v > last_version:
                last_version = v
                package = p

        return None if target_version else package
