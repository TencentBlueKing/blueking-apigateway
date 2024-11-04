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
from typing import ClassVar, Dict

from pydantic import BaseModel, Field

BkGatewayResourceLabelPrefix = "gateway.bk.tencent.com/"


class KubernetesModel(BaseModel):
    """K8S 自定义资源的通用结构声明"""

    class Config:
        populate_by_name = True

    def __str__(self):
        return repr(self)


class KubernetesResourceMetadata(BaseModel):
    label_prefix: ClassVar[str] = BkGatewayResourceLabelPrefix
    name: str = Field(default="", description="名称")
    labels: Dict[str, str] = Field(default_factory=dict, description="标签")
    annotations: Dict[str, str] = Field(default_factory=dict, description="注解")

    def add_labels(self, labels: Dict[str, str]):
        """添加标签"""
        self.labels.update({f"{self.label_prefix}{l}": v for l, v in labels.items()})

    def set_label(self, label: str, value: str):
        """设置标签"""
        self.labels[f"{self.label_prefix}{label}"] = value

    def get_label(self, label: str, default=""):
        """获取标签"""

        return self.labels.get(f"{self.label_prefix}{label}", default)


class KubernetesResource(KubernetesModel):
    """K8S 资源"""

    kind: ClassVar[str]
    metadata: KubernetesResourceMetadata = Field(default_factory=KubernetesResourceMetadata, description="元数据")


class CustomResourceSpec(KubernetesModel):
    """K8S 自定义资源的声明"""
