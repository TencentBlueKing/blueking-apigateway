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
from typing import Optional
from urllib.parse import urlparse

from attrs import define
from bkapi.bcs_api_gateway.client import Client as BcsApiGatewayClient
from django.conf import settings

from apigateway.components.bcs import get_bcs_api_gateway_client
from apigateway.components.bcs_helper import BcsApiGatewayApiRequestError
from apigateway.components.chart import RepoClient
from apigateway.controller.exceptions import ChartRepoNotFound, ChartUploadFailed
from apigateway.utils.exception import check_result_code

logger = logging.getLogger(__name__)


@define(slots=False)
class ChartRepoInfo:
    project_name: str
    name: str
    type: str
    url: str
    username: str
    password: str


@define(slots=False)
class ChartInfo:
    name: str
    version: str


@define(slots=False)
class ChartHelper:
    client: Optional[BcsApiGatewayClient] = None
    access_token: str = ""

    def __attrs_post_init__(self):
        if not self.client:
            self.client = get_bcs_api_gateway_client()
        if self.access_token and self.access_token != "":
            self.client.update_bkapi_authorization(access_token=self.access_token)

    def get_public_repo_info(self) -> ChartRepoInfo:
        """Get the public chart repos info."""
        return self.get_repo_info(settings.BCS_PUBLIC_CHART_PROJECT, settings.BCS_PUBLIC_CHART_REPOSITORY)

    def get_project_repo_info(self, project_name: str) -> ChartRepoInfo:
        """Get the project chart repos info."""
        return self.get_repo_info(project_name, project_name)

    def get_repo_info(self, project_name: str, repo_name: str) -> ChartRepoInfo:
        """Get the chart repo info by name."""
        assert self.client
        result = self.client.api.get_repo(
            path_params={
                "projectCode": project_name,
                "name": repo_name,
            }
        )

        check_result_code("query chart repo", BcsApiGatewayApiRequestError, result.get("code"), result.get("message"))

        if not result.get("result"):
            raise ChartRepoNotFound(repo_name)

        repo = result["data"]
        return ChartRepoInfo(
            project_name=repo["projectCode"],
            name=repo["name"],
            type=repo["type"],
            url=repo["repoURL"],
            username=repo["username"],
            password=repo["password"],
        )

    def push_chart(self, chart_file: str, repo_info: ChartRepoInfo):
        """Push the chart to the repo."""

        url = urlparse(repo_info.url)
        repo_info = self.get_repo_info(repo_info.project_name, repo_info.name)
        client = RepoClient(
            endpoint=f"{url.scheme}://{url.netloc}",
            project_name=repo_info.project_name,
            repo_name=repo_info.name,
        )
        client.set_auth(repo_info.username, repo_info.password)

        upload_result = client.api.upload(files={"chart": open(chart_file, "rb")}, params={"force": "1"})
        if not upload_result.get("saved"):
            raise ChartUploadFailed()

    def check_chart_exists(self, project_name: str, repo_name: str, name: str, version: str, operator: str):
        """Check the chart exists in the repo."""
        assert self.client

        result = self.client.api.get_chart_versions(
            path_params={
                "projectCode": project_name,
                "repoName": repo_name,
                "name": name,
            },
            params={"operator": operator},
        )

        check_result_code(
            "query chart versions", BcsApiGatewayApiRequestError, result.get("code"), result.get("message")
        )

        if not result["result"]:
            return False

        data = result["data"]
        for i in data["data"]:
            if i.get("version") == version:
                return True

        return False
