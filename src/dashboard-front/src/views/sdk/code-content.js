/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
export default {
  get_client_by_request: `
    from bkapigw.#apigw_name#.shortcuts import get_client_by_request
    # 从环境配置获取APP信息，从django request获取当前用户信息
    # stage通过【部署环境】获取
    client = get_client_by_request(request, stage='prod')
    kwargs = {
        "bk_biz_id": 1234
    }
    result = client.api.post_create_task(kwargs)
`,
  get_client_by_user: `
    from bkapigw.#apigw_name#.shortcuts import get_client_by_user
    # 从环境配置获取APP信息，从user获取当前用户信息，user为User对象或User中username数据
    # stage通过【部署环境】获取
    user = "xxx"
    client = get_client_by_user(user, stage='prod')
    kwargs = {
        "bk_biz_id": 1234
    }
    result = client.api.post_create_task(kwargs)
`,
  RequestAPIClient: `
    from bkapigw.#apigw_name#.client import RequestAPIClient
    # APP信息
    app_code = "xxx"
    app_secret = "xxx"
    # 用户信息
    common_args = {"access_token": "xxx"}
    # APP信息app_code, app_secret如未提供，从环境配置获取
    # stage通过【部署环境】获取
    client = RequestAPIClient(
        app_code=app_code,
        app_secret=app_secret,
        stage='prod',
        common_args=common_args
    )
    kwargs = {
        "bk_biz_id": 1234
    }
    result = client.api.post_create_task(kwargs)
`
}
