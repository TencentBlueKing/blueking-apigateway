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
from django.db import models
from jsonfield import JSONField

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, Stage


class APIDebugHistory(TimestampedModelMixin, OperatorModelMixin):
    gateway = models.ForeignKey(Gateway, db_column="gateway_id", on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, db_column="stage_id", on_delete=models.CASCADE)
    resource_name = models.CharField(null=False, blank=False, max_length=32, help_text="资源名称")
    # "request": {
    #     "request_url": "www.baidu.com",       # 请求路由
    #     "request_method": "GET",              # 请求方法
    #     "type":"HTTP",                        # 请求类型
    #     "path_params": {aa:"aa"},             # 路径参数
    #     "query_params": {aa:"aa"},            # 查询参数
    #     "body": "",                           # 请求Body
    #     "headers": {aa:"aa"},                 # 请求headers
    #     "subpath": "",                        # 分割路径参数
    #     "use_test_app": True,                 # 请求参数中的 是否使用测试账号
    #     "use_user_from_cookies": False,       # 请求参数中的 是否使用用户中的cookies
    #     "request_time":YYYY-MM-DD HH:MM:SS,   # 请求开始时间
    #     "spec_version": 1,                    # 请求版本
    # }
    request = JSONField(blank=True, help_text="请求参数")
    #   "response": {
    #     "data": {                             # 和在线调试一样的结果
    #         "status_code":200,                # 结果状态码
    #         "proxy_time": 0.00001,            # 处理时间
    #         "size": 1024,                     # 结果大小
    #         "body": "返回的body结果",           # 返回结果的body
    #         "headers": "返回的headers",        # 返回结果的header
    #         "curl": "路由",                    # 路由
    #      },
    #     "spec_version": 1,                    # 返回的结果版本
    #     "error":null,                         # 返回的错误信息（如果发起调用的时候报错等于调用都没成功，就直接将错误信息放入其中，上面全部字段都没数据）
    # }
    response = JSONField(blank=True, help_text="返回结果")

    class Meta:
        verbose_name = "APIDebugHistory"
        verbose_name_plural = "APIDebugHistory"
        db_table = "api_debug_history"
