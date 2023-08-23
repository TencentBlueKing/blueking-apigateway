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
import logging
from typing import Any, Dict, List, Tuple

from attrs import define, field
from bkapi.bcs_api_gateway.client import Client as BcsApiGatewayClient

from apigateway.components.bcs import get_bcs_api_gateway_client
from apigateway.components.bcs_helper import BcsApiGatewayApiRequestError
from apigateway.controller.exceptions import ReleaseError, ReleaseNotFound
from apigateway.utils.exception import check_result_code
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


@define(slots=False)
class ReleaseInfo:
    name: str
    namespace: str
    revision: int
    status: str
    chart_name: str
    chart_version: str
    app_version: str

    @classmethod
    def from_api(cls, result: Dict[str, Any]):
        return cls(
            name=result.get("name", ""),
            namespace=result.get("namespace", ""),
            revision=result.get("revision", -1),
            status=result.get("status", ""),
            chart_name=result.get("chart", ""),
            chart_version=result.get("chartVersion", ""),
            app_version=result.get("appVersion", ""),
        )


@define(slots=False)
class ReleaseHelper:
    client: BcsApiGatewayClient = field(factory=get_bcs_api_gateway_client)
    access_token: str = ""

    def __attrs_post_init__(self):
        if self.access_token and self.access_token != "":
            self.client.update_bkapi_authorization(access_token=self.access_token)

    def upgrade_release(
        self,
        cluster_id: str,
        project_id: str,
        repository: str,
        chart_name: str,
        chart_version: str,
        release_name: str,
        namespace: str,
        values: dict,
        operator: str,
    ) -> ReleaseInfo:
        """Upgrade release upgrade with the given parameters."""

        values_yaml = yaml_dumps(values)
        result = self.client.api.upgrade_release(
            path_params={
                "projectCode": project_id,
                "clusterID": cluster_id,
                "namespace": namespace,
                "name": release_name,
            },
            json={
                "name": release_name,
                "namespace": namespace,
                "clusterID": cluster_id,
                "projectCode": project_id,
                "repository": repository,
                "chart": chart_name,
                "version": chart_version,
                "operator": operator,
                "values": [values_yaml],
            },
        )

        code = result.get("code")
        logger.debug(
            "upgraded release %s by chart %s:%s, code %s, message %s",
            release_name,
            chart_name,
            chart_version,
            code,
            result.get("message"),
        )

        if code != 0:
            raise ReleaseError(code=code, message=result.get("message", ""))

        # 查询更新后的release
        release_result = self.client.api.get_release_detail(
            path_params={
                "projectCode": project_id,
                "clusterID": cluster_id,
                "namespace": namespace,
                "name": release_name,
            }
        )

        code = release_result.get("code")
        logger.debug(
            "get release after upgrading release %s by chart %s:%s, code %s, message %s",
            release_name,
            chart_name,
            chart_version,
            code,
            release_result.get("message"),
        )

        if code != 0:
            raise ReleaseError(code=code, message=release_result.get("message", ""))

        return ReleaseInfo.from_api(release_result["data"])

    def install_release(
        self,
        cluster_id: str,
        project_id: str,
        repository: str,
        chart_name: str,
        chart_version: str,
        release_name: str,
        namespace: str,
        values: dict,
        operator: str,
    ) -> ReleaseInfo:
        """Install release upgrade with the given parameters."""
        values_yaml = yaml_dumps(values)
        result = self.client.api.install_release(
            path_params={
                "projectCode": project_id,
                "clusterID": cluster_id,
                "namespace": namespace,
                "name": release_name,
            },
            json={
                "name": release_name,
                "namespace": namespace,
                "clusterID": cluster_id,
                "projectCode": project_id,
                "repository": repository,
                "chart": chart_name,
                "version": chart_version,
                "operator": operator,
                "values": [values_yaml],
            },
        )

        code = result.get("code")
        logger.debug(
            "installed release %s by chart %s:%s, code %s, message %s",
            release_name,
            chart_name,
            chart_version,
            code,
            result.get("message"),
        )

        if code != 0:
            raise ReleaseError(code=code, message=result.get("message", ""))

        # 查询安装后的release
        release_result = self.client.api.get_release_detail(
            path_params={
                "projectCode": project_id,
                "clusterID": cluster_id,
                "namespace": namespace,
                "name": release_name,
            }
        )

        code = release_result.get("code")
        logger.debug(
            "get release after installing release %s by chart %s:%s, code %s, message %s",
            release_name,
            chart_name,
            chart_version,
            code,
            release_result.get("message"),
        )

        if code != 0:
            raise ReleaseError(code=code, message=release_result.get("message", ""))

        return ReleaseInfo.from_api(release_result["data"])

    def ensure_release(
        self,
        cluster_id: str,
        project_id: str,
        repository: str,
        chart_name: str,
        chart_version: str,
        release_name: str,
        namespace: str,
        values: dict,
        operator: str,
    ) -> Tuple[bool, ReleaseInfo]:
        """Ensure release upgrade with the given parameters."""

        try:
            self.get_release_info(project_id, cluster_id, namespace, release_name)
            found = True
        except ReleaseNotFound:
            found = False

        if found:
            return True, self.upgrade_release(
                cluster_id=cluster_id,
                project_id=project_id,
                repository=repository,
                chart_name=chart_name,
                chart_version=chart_version,
                release_name=release_name,
                namespace=namespace,
                values=values,
                operator=operator,
            )

        return False, self.install_release(
            cluster_id=cluster_id,
            project_id=project_id,
            repository=repository,
            chart_name=chart_name,
            chart_version=chart_version,
            release_name=release_name,
            namespace=namespace,
            values=values,
            operator=operator,
        )

    def _list_releases(self, project_id: str, cluster_id: str, params: Dict[str, Any]) -> List[ReleaseInfo]:
        result = self.client.api.list_releases(
            path_params={
                "projectCode": project_id,
                "clusterID": cluster_id,
            },
            params=params,
        )

        check_result_code("list releases", BcsApiGatewayApiRequestError, result.get("code"), result.get("message"))
        data = result["data"]

        return [ReleaseInfo.from_api(release) for release in data["data"]]

    def get_release_info(self, project_id: str, cluster_id: str, namespace: str, name: str) -> ReleaseInfo:
        """Get release info by release name."""

        releases = self._list_releases(project_id, cluster_id, {"namespace": namespace, "name": name})

        if not releases:
            raise ReleaseNotFound(name)

        return releases[0]

    def list_releases(self, project_id: str, cluster_id: str, namespace: str) -> List[ReleaseInfo]:
        """List all releases in the given namespace."""

        # 接口支持分页，设置 desire_all_data=1 获取符合条件的全部数据
        return self._list_releases(project_id, cluster_id, {"namespace": namespace, "desire_all_data": 1})
