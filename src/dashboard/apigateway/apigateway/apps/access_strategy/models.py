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
import re
from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.common.mixins.models import ConfigModelMixin, OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway
from apigateway.schema.models import Schema

# 现有的访问策略是通过中间件来实现功能的，需要明确两个概念：
# 1. 通过中间件方式来改变请求和响应的技术方式，叫做插件；
# 2. 用户在页面上配置的，如 IP 白名单，流控等，这些是访问策略；
# 现有的访问策略是通过插件的方式来实现的，换言之，这类的插件可以被归入访问控制这个分组。
# 那么类似 CORS 这类改写请求头的插件，严格意义上不属于访问控制，应该有另外的分组。
# 但是本质上，在代码的实现都是通过插件的方式来处理的，因此代码需要将访问策略的概念扩展成插件的概念，而流程上不需要调整。j

logger = logging.getLogger(__name__)


# FIXME: remove in 1.14
class IPGroup(TimestampedModelMixin, OperatorModelMixin):
    """
    IPGroup, manager the ip list
    """

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)

    name = models.CharField(max_length=64, blank=False, null=False)
    _ips = models.TextField(db_column="ips")
    comment = models.CharField(max_length=512, blank=True, default="")

    def __str__(self):
        return f"<IPGroup: {self.api}/{self.name}>"

    class Meta:
        verbose_name = _("IP分组")
        verbose_name_plural = _("IP分组")
        unique_together = ("api", "name")
        db_table = "access_strategy_ip_group"

    @property
    def ips(self) -> List[str]:
        if not self._ips:
            return []

        # split with \n\r, then ignore blank line and `# comment`
        lines = re.split(r"[\n\r]+", self._ips)
        valid_lines = [line for line in lines if line and (not line.startswith("#"))]
        return valid_lines

    @ips.setter
    def ips(self, data):
        self._ips = data


# FIXME: remove in 1.14
class AccessStrategy(ConfigModelMixin):
    """
    access strategy
    """

    api = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, db_index=True)
    type = models.CharField(max_length=32, choices=AccessStrategyTypeEnum.get_choices())

    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    # config from ConfigModelMixin

    comment = models.CharField(max_length=512, blank=True, default="")

    def __str__(self):
        return f"<AccessStrategy: {self.pk}/{self.api}/{self.name}/{self.type}>"

    class Meta:
        verbose_name = _("访问策略")
        verbose_name_plural = _("访问策略")
        unique_together = ("api", "name", "type")
        db_table = "access_strategy"

    def save(self, *args, **kwargs):
        if self.type not in dict(AccessStrategyTypeEnum.get_choices()):
            raise ValueError("type should be one of AccessStrategyTypeEnum")

        # check the config value
        try:
            self.config
        except Exception as e:
            logger.exception("the config field is not a valid json")
            raise e

        super().save(*args, **kwargs)

    def add_ip_group_list(self, ip_group_list):
        """
        将 IP 分组列表添加到当前配置
        """
        config = self.config
        config["ip_group_list"].extend(ip_group_list)
        # 去重
        config["ip_group_list"] = sorted(list(set(config["ip_group_list"])))
        self.config = config


# FIXME: remove in 1.14
class AccessStrategyBinding(TimestampedModelMixin, OperatorModelMixin):
    """
    strategy binding

    需求:
    - 一个环境, 只能绑定一个ip访问控制策略, 白名单或黑名单
    - 资源不能绑定ip访问控制策略
    - 一个环境, 只能绑定一个频率控制(包含多个应用, 每个应用不同的频率)
    - 一个资源, 只能绑定一个频率控制(包含多个应用, 每个应用不同的频率)
    """

    scope_type = models.CharField(
        max_length=32,
        choices=AccessStrategyBindScopeEnum.choices(),
        blank=False,
        null=False,
        db_index=True,
    )
    scope_id = models.IntegerField(blank=False, null=False, db_index=True)
    type = models.CharField(max_length=32, choices=AccessStrategyTypeEnum.get_choices(), blank=False, null=False)

    access_strategy = models.ForeignKey(AccessStrategy, on_delete=models.PROTECT)

    def __str__(self):
        return f"<AccessStrategyBinding: {self.scope_type}/{self.scope_id}/{self.type}>"

    class Meta:
        verbose_name = _("访问策略绑定")
        verbose_name_plural = _("访问策略绑定")
        unique_together = ("scope_type", "scope_id", "type")
        db_table = "access_strategy_binding"

    def save(self, *args, **kwargs):
        if self.type not in dict(AccessStrategyTypeEnum.get_choices()):
            raise ValueError("type should be one of AccessStrategyTypeEnum")
        super().save(*args, **kwargs)
