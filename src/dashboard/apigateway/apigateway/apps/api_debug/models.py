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
    #     "authorization": {aa:"aa"},           # 授权
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
    # "response": {
    #     "status_code": 200,                   # 返回结果状态码
    #     "proxy_time": 2.22,                   # 处理的时间
    #     "body": "xxx",                        # 返回的结果内容
    #     "spec_version": 1,                    # 返回的结果版本
    # }
    response = JSONField(blank=True, help_text="返回结果")

    class Meta:
        verbose_name = "APIDebugHistory"
        verbose_name_plural = "APIDebugHistory"
        db_table = "api_debug_history"
