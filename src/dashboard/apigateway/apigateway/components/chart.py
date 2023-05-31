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

from bkapi_client_core.base import Operation, OperationGroup
from bkapi_client_core.client import BaseClient
from bkapi_client_core.property import bind_property
from requests.auth import HTTPBasicAuth

from apigateway.components.utils import inject_accept_language

logger = logging.getLogger(__name__)


class RepoApiGroup(OperationGroup):
    # https://chartmuseum.com/docs/#chart-manipulation

    upload = bind_property(
        Operation,
        method="POST",
        path="/helm/api/{project_name}/{repo_name}/charts",
    )
    list = bind_property(
        Operation,
        method="GET",
        path="/helm/{project_name}/{repo_name}/api/charts/{name}",
    )
    get = bind_property(
        Operation,
        method="GET",
        path="/helm/{project_name}/{repo_name}/api/charts/{name}/{version}",
    )
    delete = bind_property(
        Operation,
        method="DELETE",
        path="/helm/{project_name}/{repo_name}/api/charts/{name}/{version}",
    )


class RepoClient(BaseClient):
    """操作 chart 仓库"""

    api = bind_property(RepoApiGroup)

    def __init__(self, project_name: str, repo_name: str, *args, **kwargs):
        super(RepoClient, self).__init__(*args, **kwargs)
        self.session.path_params = {
            "project_name": project_name,
            "repo_name": repo_name,
        }
        self.session.register_hook("request", inject_accept_language)

    def set_auth(self, username: str, password: str):
        self.session.auth = HTTPBasicAuth(username, password)

    def _handle_exception(self, operation, context, exception):
        # to_curl 会导致密码泄露，覆盖基类实现
        logger.exception("request operation failed. operation: %s, context: %s", operation, context)
        raise exception
