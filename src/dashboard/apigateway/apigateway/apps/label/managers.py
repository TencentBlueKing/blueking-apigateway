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
import itertools
import operator
from typing import Any, Dict, List

from django.db import models
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpObjectTypeEnum, OpStatusEnum, OpTypeEnum
from apigateway.apps.audit.utils import record_audit_log


class APILabelManager(models.Manager):
    def get_labels(self, gateway, ids=None) -> List[Dict[int, str]]:
        queryset = self.filter(gateway=gateway)
        if ids is not None:
            queryset = queryset.filter(id__in=ids)
        return list(queryset.values("id", "name"))

    def get_label_ids(self, gateway) -> List[int]:
        return list(self.filter(gateway_id=gateway.id).values_list("id", flat=True))

    def get_name_id_map(self, gateway) -> Dict[str, int]:
        return dict(self.filter(gateway_id=gateway.id).values_list("name", "id"))

    def save_labels(self, gateway, names: List[str], username: str) -> Dict[str, int]:
        name_to_id = {}
        for name in names:
            obj, created = self.get_or_create(
                gateway_id=gateway.id,
                name=name,
                defaults={
                    "created_by": username,
                    "updated_by": username,
                },
            )
            if created:
                record_audit_log(
                    username=username,
                    op_type=OpTypeEnum.CREATE.value,
                    op_status=OpStatusEnum.SUCCESS.value,
                    op_object_group=gateway.id,
                    op_object_type=OpObjectTypeEnum.GATEWAY_LABEL.value,
                    op_object_id=obj.id,
                    op_object=obj.name,
                    comment=_("导入资源时创建网关标签"),
                )
            name_to_id[name] = obj.id

        return name_to_id

    def filter_by_label_name(self, gateway, label_name=None):
        queryset = self.filter(gateway=gateway)
        if label_name:
            queryset = queryset.filter(name=label_name)
        return queryset


class ResourceLabelManager(models.Manager):
    def filter_resource_ids(self, gateway, label_name=None) -> List[int]:
        from apigateway.apps.label.models import APILabel

        api_label_queryset = APILabel.objects.filter_by_label_name(gateway, label_name=label_name)
        queryset = self.filter(api_label__in=api_label_queryset)
        return list(set(queryset.values_list("resource_id", flat=True)))

    def filter_labels_by_gateway(self, gateway) -> Dict[int, List[Dict[str, Any]]]:
        from apigateway.apps.label.models import APILabel

        api_label_ids = APILabel.objects.get_label_ids(gateway)

        queryset = self.filter(api_label_id__in=api_label_ids)
        return self._get_resource_labels(queryset)

    def get_labels(self, resource_ids) -> Dict[int, List[Dict[str, Any]]]:
        queryset = self.filter(resource_id__in=resource_ids)
        return self._get_resource_labels(queryset)

    def _get_resource_labels(self, queryset) -> Dict[int, List[Dict[str, Any]]]:
        queryset = queryset.values("api_label_id", "api_label__name", "resource_id")

        labels = sorted(queryset, key=operator.itemgetter("resource_id"))

        label_groups = itertools.groupby(labels, key=operator.itemgetter("resource_id"))
        resource_labels = {}
        for resource_id, group in label_groups:
            resource_labels[resource_id] = [
                {
                    "id": label["api_label_id"],
                    "name": label["api_label__name"],
                }
                for label in group
            ]
        return resource_labels

    def get_api_label_ids(self, resource_id) -> List[int]:
        return list(self.filter(resource_id=resource_id).values_list("api_label_id", flat=True))
