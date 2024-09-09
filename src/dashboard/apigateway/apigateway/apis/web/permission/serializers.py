# -*- coding: utf-8 -*-
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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.biz.validators import BKAppCodeValidator, ResourceIDValidator
from apigateway.utils.time import NeverExpiresTime, to_datetime_from_now


class AppPermissionQueryInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(help_text="应用ID", required=False)
    keyword = serializers.CharField(help_text="查询关键字", required=False)
    grant_type = serializers.ChoiceField(choices=GrantTypeEnum.get_choices(), required=False)
    resource_id = serializers.IntegerField(help_text="资源id", required=False)
    order_by = serializers.ChoiceField(
        help_text="排序",
        choices=[(field, field) for field in ["bk_app_code", "-bk_app_code", "expires", "-expires"]],
        required=False,
    )
    grant_dimension = serializers.ChoiceField(
        help_text="授权维度", choices=GrantDimensionEnum.get_choices(), required=False
    )
    applied_by = serializers.CharField(help_text="申请人", required=False)


class AppPermissionOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bk_app_code = serializers.CharField(max_length=32, required=True, help_text="应用编码")
    resource_id = serializers.SerializerMethodField(help_text="资源ID")
    resource_name = serializers.SerializerMethodField(help_text="资源名称")
    resource_path = serializers.SerializerMethodField(help_text="资源路径")
    resource_method = serializers.SerializerMethodField(help_text="资源方法")
    expires = serializers.SerializerMethodField(help_text="过期时间")
    grant_dimension = serializers.ChoiceField(help_text="授权维度", choices=GrantDimensionEnum.get_choices())
    grant_type = serializers.ChoiceField(
        choices=GrantTypeEnum.get_choices(), default=GrantTypeEnum.INITIALIZE.value, help_text="授权类型"
    )
    renewable = serializers.SerializerMethodField(help_text="是否可续期")

    class Meta:
        ref_name = "apigateway.apis.web.permission.serializers.AppPermissionOutputSLZ"

    def get_resource_id(self, obj):
        resource = self.context.get("resource_map", {}).get(obj.get("resource_id", 0))
        return resource.id if resource else 0

    def get_resource_name(self, obj):
        resource = self.context.get("resource_map", {}).get(obj.get("resource_id", 0))
        return resource.name if resource else ""

    def get_resource_path(self, obj):
        resource = self.context.get("resource_map", {}).get(obj.get("resource_id", 0))
        return resource.path_display if resource else ""

    def get_resource_method(self, obj):
        resource = self.context.get("resource_map", {}).get(obj.get("resource_id", 0))
        return resource.method if resource else ""

    def get_expires(self, obj):
        expires = (
            None
            if (not obj.get("expires") or NeverExpiresTime.is_never_expired(obj.get("expires")))
            else obj.get("expires")
        )
        return serializers.DateTimeField(allow_null=True, required=False).to_representation(expires)

    def get_renewable(self, obj):
        return bool(obj.get("expires") and obj.get("expires") < to_datetime_from_now(days=RENEWABLE_EXPIRE_DAYS))


class AppPermissionRenewInputSLZ(serializers.Serializer):
    gateway_dimension_ids = serializers.ListField(
        help_text="网关维度权限id列表", child=serializers.IntegerField(), allow_empty=True, required=False
    )
    resource_dimension_ids = serializers.ListField(
        help_text="资源维度权限id列表", child=serializers.IntegerField(), allow_empty=True, required=False
    )
    expire_days = serializers.ChoiceField(
        help_text="有效期",
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        required=True,
    )

    def validate(self, data):
        gateway_dimension_ids = data.get("gateway_dimension_ids", [])
        resource_dimension_ids = data.get("resource_dimension_ids", [])

        if not gateway_dimension_ids and not resource_dimension_ids:
            raise serializers.ValidationError("must select one permission")

        return data


class AppPermissionInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(label="", max_length=32, required=True, validators=[BKAppCodeValidator()])
    expire_days = serializers.IntegerField(allow_null=True, required=True, help_text="过期天数")
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        validators=[ResourceIDValidator()],
        required=True,
        allow_empty=False,
        allow_null=True,
        help_text="资源ID列表",
    )


class AppPermissionExportInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, required=False)
    resource_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源ID")
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="查询条件")
    grant_type = serializers.ChoiceField(
        choices=GrantTypeEnum.get_choices(), allow_blank=True, required=False, help_text="授权类型"
    )
    order_by = serializers.ChoiceField(
        choices=["bk_app_code", "-bk_app_code", "expires", "-expires"],
        allow_blank=True,
        required=False,
        help_text="排序",
    )
    export_type = serializers.ChoiceField(
        choices=ExportTypeEnum.get_choices(),
        help_text=(
            "值为 all，不需其它参数；值为 filtered，支持 dimension/bk_app_code/resource_name/query 参数；"
            "值为 selected，支持 permission_ids 参数"
        ),
    )
    gateway_permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        help_text='gateway维度:export_type 值为已选资源 "selected" 时，此项必填',
    )
    resource_permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        help_text='resource维度:export_type 值为已选资源 "selected" 时，此项必填',
    )

    def validate(self, data):
        if data["export_type"] == ExportTypeEnum.SELECTED.value and (
            not data.get("gateway_permission_ids") or not data.get("resource_permission_ids")
        ):
            raise serializers.ValidationError(_("导出已选中权限时，已选中权限不能为空。"))
        return data


class AppPermissionExportOutputSLZ(AppPermissionOutputSLZ):
    grant_type = serializers.SerializerMethodField(help_text="过期时间")
    grant_dimension = serializers.SerializerMethodField(help_text="过期时间")

    def get_grant_type(self, obj):
        return _(GrantTypeEnum.get_choice_label(obj.get("grant_type", GrantTypeEnum.INITIALIZE.value)))

    def get_grant_dimension(self, obj):
        return _(GrantDimensionEnum.get_choice_label(obj.get("grant_dimension")))

    def get_expires(self, obj):
        if NeverExpiresTime.is_never_expired(obj.get("expires")):
            return _("永久有效")
        return super().get_expires(obj)


class AppPermissionIDsSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False, required=True)
    expire_days = serializers.ChoiceField(
        help_text="有效期",
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        required=False,
        default=PermissionApplyExpireDaysEnum.FOREVER.value,
    )


class AppPermissionApplyOutputSLZ(serializers.ModelSerializer):
    bk_app_code = serializers.CharField(label="", max_length=32, validators=[BKAppCodeValidator()])
    resource_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True, help_text="资源ID列表")
    expire_days_display = serializers.SerializerMethodField(help_text="过期天数")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度")

    class Meta:
        model = AppPermissionApply
        fields = [
            "id",
            "bk_app_code",
            "applied_by",
            "resource_ids",
            "status",
            "reason",
            "expire_days",
            "grant_dimension",
            "created_time",
            "expire_days_display",
            "grant_dimension_display",
        ]
        read_only_fields = ("id", "applied_by", "status", "created_time")
        lookup_field = "id"

    def get_expire_days_display(self, obj):
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj):
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)


class AppPermissionRecordOutputSLZ(serializers.ModelSerializer):
    handled_resources = serializers.SerializerMethodField(help_text="已处理的资源列表")
    expire_days_display = serializers.SerializerMethodField(help_text="过期天数")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度")

    class Meta:
        model = AppPermissionRecord
        fields = [
            "id",
            "bk_app_code",
            "applied_by",
            "applied_time",
            "handled_by",
            "handled_time",
            "status",
            "comment",
            "reason",
            "expire_days",
            "grant_dimension",
            "resource_ids",
            "handled_resources",
            "expire_days_display",
            "grant_dimension_display",
        ]
        lookup_field = "id"

    def get_handled_resources(self, obj):
        handled_resources = []
        for apply_status, resource_ids in obj.handled_resource_ids.items():
            for resource_id in resource_ids:
                resource = self.context["resource_id_map"].get(resource_id)
                handled_resources.append(
                    {
                        "apply_status": apply_status,
                        "name": resource.name
                        if resource
                        else _("资源【{resource_id}】已删除").format(resource_id=resource_id),
                        "method": resource.method if resource else "",
                        "path": resource.path_display if resource else "",
                    }
                )

        return sorted(handled_resources, key=lambda x: (x["apply_status"], x["name"]))

    def get_expire_days_display(self, obj):
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj):
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)


class AppPermissionApplyApprovalInputSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    part_resource_ids = serializers.DictField(
        label="部分审批资源ID",
        child=serializers.ListField(child=serializers.IntegerField(), allow_empty=False),
        allow_empty=True,
        required=False,
        help_text="部分审批资源ID",
    )
    status = serializers.ChoiceField(
        choices=[
            ApplyStatusEnum.PARTIAL_APPROVED.value,
            ApplyStatusEnum.APPROVED.value,
            ApplyStatusEnum.REJECTED.value,
        ],
        help_text="审批状态",
    )
    comment = serializers.CharField(allow_blank=True, max_length=512, help_text="审批意见")
