#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import json

from django import forms
from django.contrib import admin

from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding


class DataPlaneAdminForm(forms.ModelForm):
    """Custom form for DataPlane admin to handle etcd_configs as JSON"""

    etcd_configs_json = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "cols": 80}),
        required=False,
        help_text="ETCD configuration in JSON format. Example: "
        '{"host": "localhost", "port": 2379, "user": "", "password": ""}',
    )

    class Meta:
        model = DataPlane
        fields = [
            "name",
            "description",
            "bk_api_url_tmpl",
            "status",
            "is_recommend",
            "created_by",
            "updated_by",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Load existing etcd_configs as JSON string for display
            etcd_configs = self.instance.etcd_configs
            if etcd_configs:
                self.fields["etcd_configs_json"].initial = json.dumps(etcd_configs, indent=2)

    def clean_etcd_configs_json(self):
        """Validate and parse the JSON input"""
        value = self.cleaned_data.get("etcd_configs_json", "")
        if not value or not value.strip():
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON format: {e}")

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set the etcd_configs using the property (which encrypts the data)
        etcd_configs = self.cleaned_data.get("etcd_configs_json", {})
        instance.etcd_configs = etcd_configs
        if commit:
            instance.save()
        return instance


@admin.register(DataPlane)
class DataPlaneAdmin(admin.ModelAdmin):
    form = DataPlaneAdminForm

    list_display = [
        "id",
        "name",
        "description",
        "status",
        "is_recommend",
        "has_etcd_configs",
        "created_time",
        "updated_time",
    ]
    list_filter = ["status", "is_recommend"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_time", "updated_time"]
    ordering = ["-created_time"]

    fieldsets = (
        (None, {"fields": ("name", "description", "status", "is_recommend")}),
        ("ETCD Configuration", {"fields": ("etcd_configs_json", "bk_api_url_tmpl")}),
        ("Audit", {"fields": ("created_by", "updated_by", "created_time", "updated_time")}),
    )

    def has_etcd_configs(self, obj):
        """Display whether the data plane has ETCD configs configured"""
        return bool(obj.etcd_configs)

    has_etcd_configs.boolean = True  # type: ignore[attr-defined]
    has_etcd_configs.short_description = "Has ETCD Config"  # type: ignore[attr-defined]


@admin.register(GatewayDataPlaneBinding)
class GatewayDataPlaneBindingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "gateway",
        "data_plane",
        "created_time",
        "created_by",
    ]
    list_filter = ["data_plane"]
    search_fields = ["gateway__name", "data_plane__name"]
    readonly_fields = ["created_time"]
    raw_id_fields = ["gateway", "data_plane"]
    ordering = ["-created_time"]
