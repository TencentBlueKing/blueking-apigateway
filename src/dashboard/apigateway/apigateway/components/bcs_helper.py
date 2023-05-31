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
from logging import getLogger
from typing import List

from attrs import define, field
from bkapi.bcs_api_gateway.client import Client as BcsApiGatewayClient
from django.conf import settings

from apigateway.components.bcs import get_bcs_api_gateway_admin_client, get_bcs_api_gateway_client
from apigateway.components.exceptions import ApiRequestError
from apigateway.utils.exception import check_result_code

logger = getLogger(__name__)


class BcsApiGatewayApiRequestError(ApiRequestError):
    """BcsApiGateway API 请求错误"""


@define(slots=False)
class ProjectInfo:
    project_id: str
    project_name: str


@define(slots=False)
class ClusterInfo:
    cluster_id: str


@define(slots=False)
class NamespaceInfo:
    namespace: str


@define(slots=False)
class BcsHelper:
    access_token: str = ""
    bcs_client: BcsApiGatewayClient = field(factory=get_bcs_api_gateway_client)
    bcs_admin_client: BcsApiGatewayClient = field(factory=get_bcs_api_gateway_admin_client)

    def __attrs_post_init__(self):
        self.bcs_client.update_bkapi_authorization(
            bk_app_code=settings.BK_APP_CODE,
            bk_app_secret=settings.BK_APP_SECRET,
            access_token=self.access_token,
        )

    def get_projects(self) -> List[ProjectInfo]:
        result = self.bcs_client.api.list_auth_projects()

        check_result_code(
            "query bcs projects", BcsApiGatewayApiRequestError, result.get("code"), result.get("message")
        )
        data = result["data"]

        return [
            ProjectInfo(
                project_id=p.get("projectID"),
                project_name=p.get("projectCode"),
            )
            for p in data["results"]
        ]

    def get_clusters(self, project_id: str) -> List[ClusterInfo]:
        result = self.bcs_client.api.list_project_clusters(
            params={
                "projectID": project_id,
            },
        )

        check_result_code(
            "query bcs clusters", BcsApiGatewayApiRequestError, result.get("code"), result.get("message")
        )

        clusters = result["data"]
        if not clusters:
            return []

        return [ClusterInfo(cluster_id=c.get("clusterID")) for c in clusters]

    def get_namespaces(self, project_id: str, cluster_id: str) -> List[NamespaceInfo]:
        result = self.bcs_admin_client.api.list_cluster_namespaces(
            path_params={
                "cluster_id": cluster_id,
            },
        )

        namespaces = result.get("items")
        if namespaces is None:
            raise BcsApiGatewayApiRequestError("cluster namespaces not found")

        return [NamespaceInfo(namespace=n["metadata"]["name"]) for n in namespaces]
