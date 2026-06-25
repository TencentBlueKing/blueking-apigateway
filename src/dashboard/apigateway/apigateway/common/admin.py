#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from django.contrib.admin.utils import flatten_fieldsets
from django.core.exceptions import FieldDoesNotExist


class AuditFieldsDisplayAdminMixin:
    audit_fields = ("created_by", "updated_by", "created_time", "updated_time")
    readonly_audit_fields = ("created_time", "updated_time")

    def _has_model_field(self, field_name):
        try:
            self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return False

        return True

    def _get_existing_audit_fields(self):
        return tuple(field_name for field_name in self.audit_fields if self._has_model_field(field_name))

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        for field_name in self.readonly_audit_fields:
            if self._has_model_field(field_name) and field_name not in readonly_fields:
                readonly_fields.append(field_name)

        return readonly_fields

    def get_fields(self, request, obj=None):
        fields = [field_name for field_name in super().get_fields(request, obj) if field_name not in self.audit_fields]
        return [*fields, *self._get_existing_audit_fields()]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        audit_fields = self._get_existing_audit_fields()
        if not audit_fields:
            return fieldsets

        existing_fields = set(flatten_fieldsets(fieldsets))
        missing_fields = tuple(field_name for field_name in audit_fields if field_name not in existing_fields)
        if not missing_fields:
            return fieldsets

        return (*fieldsets, ("Audit", {"fields": missing_fields}))
