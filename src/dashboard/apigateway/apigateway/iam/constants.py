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
from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext as _

from apigateway.common.constants import ExtendEnumField

# 永不过期的时间（伪，其实是 2100.01.01 08:00:00，与权限中心保持一致)
NEVER_EXPIRE_TIMESTAMP = 4102444800

# 权限中心的用户组授权为异步行为，即创建用户组，添加用户，对用户组授权后，需要等待一段时间（10~20秒），才能鉴权生效，
# 因此，需要在网关创建后的一定时间内，对创建者（拥有网关最高权限）的操作进行权限豁免以保证功能可正常使用
IAM_PERMISSION_EXEMPTED_SECONDS_FOR_GATEWAY_CREATOR = 10 * 60


class UserRoleEnum(str, StructuredEnum):
    MANAGER = EnumField("manager", label=_("管理员"))
    DEVELOPER = EnumField("developer", label=_("开发者"))
    OPERATOR = EnumField("operator", label=_("运营者"))


# 网关默认的用户角色，需为这些角色创建用户组
GATEWAY_DEFAULT_ROLES = [
    UserRoleEnum.MANAGER,
    UserRoleEnum.DEVELOPER,
    UserRoleEnum.OPERATOR,
]


class ResourceTypeEnum(str, StructuredEnum):
    GATEWAY = EnumField("gateway", label="网关")
    STAGE = EnumField("stage", label="环境")
    RESOURCE = EnumField("resource", label="资源")
    PLUGIN_CONFIG = EnumField("plugin_config", label="插件配置")


class ActionEnum(str, StructuredEnum):
    """网关在权限中心的操作"""

    # 未关联资源
    CREATE_GATEWAY = ExtendEnumField("create_gateway", label="网关创建")
    # 网关
    VIEW_GATEWAY = ExtendEnumField(
        "view_gateway",
        label="网关查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    MANAGE_GATEWAY = ExtendEnumField(
        "manage_gateway",
        label="网关管理",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    MANAGE_MEMBERS = ExtendEnumField(
        "manage_members",
        label="成员管理",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    MANAGE_SDK = ExtendEnumField(
        "manage_sdk",
        label="SDK 管理",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    API_TEST = ExtendEnumField(
        "api_test",
        label="在线调试",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    # 环境
    CREATE_STAGE = ExtendEnumField(
        "create_stage",
        label="环境新建",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    VIEW_STAGE = ExtendEnumField(
        "view_stage",
        label="环境查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.STAGE.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    EDIT_STAGE = ExtendEnumField(
        "edit_stage",
        label="环境编辑",
        metadata={
            "related_resource_type": ResourceTypeEnum.STAGE.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    RELEASE_STAGE = ExtendEnumField(
        "release_stage",
        label="环境发布",
        metadata={
            "related_resource_type": ResourceTypeEnum.STAGE.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    DELETE_STAGE = ExtendEnumField(
        "delete_stage",
        label="环境删除",
        metadata={
            "related_resource_type": ResourceTypeEnum.STAGE.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    # 资源
    CREATE_RESOURCE = ExtendEnumField(
        "create_resource",
        label="资源新建",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    VIEW_RESOURCE = ExtendEnumField(
        "view_resource",
        label="资源查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.RESOURCE.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    EDIT_RESOURCE = ExtendEnumField(
        "edit_resource",
        label="资源编辑",
        metadata={
            "related_resource_type": ResourceTypeEnum.RESOURCE.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    DELETE_RESOURCE = ExtendEnumField(
        "delete_resource",
        label="资源删除",
        metadata={
            "related_resource_type": ResourceTypeEnum.RESOURCE.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    MANAGE_RESOURCE_DOC = ExtendEnumField(
        "manage_resource_doc",
        label="资源文档管理",
        metadata={
            "related_resource_type": ResourceTypeEnum.RESOURCE.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    # 标签
    MANAGE_LABEL = ExtendEnumField(
        "manage_label",
        label="标签管理",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    # 插件
    CREATE_PLUGIN_CONFIG = ExtendEnumField(
        "create_plugin_config",
        label="插件启用",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    VIEW_PLUGIN_CONFIG = ExtendEnumField(
        "view_plugin_config",
        label="插件查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.PLUGIN_CONFIG.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    EDIT_PLUGIN_CONFIG = ExtendEnumField(
        "edit_plugin_config",
        label="插件编辑",
        metadata={
            "related_resource_type": ResourceTypeEnum.PLUGIN_CONFIG.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    BIND_PLUGIN_CONFIG = ExtendEnumField(
        "bind_plugin_config",
        label="插件绑定",
        metadata={
            "related_resource_type": ResourceTypeEnum.PLUGIN_CONFIG.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    DELETE_PLUGIN_CONFIG = ExtendEnumField(
        "delete_plugin_config",
        label="插件删除",
        metadata={
            "related_resource_type": ResourceTypeEnum.PLUGIN_CONFIG.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    # 版本
    VIEW_VERSION = ExtendEnumField(
        "view_version",
        label="版本查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value],
        },
    )
    # 权限
    APPROVE_PERMISSION = ExtendEnumField(
        "approve_permission",
        label="权限审批",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    GRANT_PERMISSION = ExtendEnumField(
        "grant_permission",
        label="主动授权",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    REVOKE_PERMISSION = ExtendEnumField(
        "revoke_permission",
        label="权限回收",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    VIEW_PERMISSION = ExtendEnumField(
        "view_permission",
        label="权限查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    # 日志
    VIEW_LOG = ExtendEnumField(
        "view_log",
        label="流水日志查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    VIEW_STATISTICS = ExtendEnumField(
        "view_statistics",
        label="统计报表查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value, UserRoleEnum.DEVELOPER.value, UserRoleEnum.OPERATOR.value],
        },
    )
    # 审计
    VIEW_AUDIT = ExtendEnumField(
        "view_audit",
        label="操作审计查看",
        metadata={
            "related_resource_type": ResourceTypeEnum.GATEWAY.value,
            "role": [UserRoleEnum.MANAGER.value],
        },
    )
    # 组件
    MANAGE_COMPONENTS = ExtendEnumField("manage_components", label="组件管理")
