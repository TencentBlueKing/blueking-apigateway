#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

from typing import List, Optional

from django.conf import settings
from rest_framework.exceptions import ValidationError

from apigateway.apps.data_plane.constants import BkPluginsDataPlaneGrayStageEnum
from apigateway.apps.data_plane.models import DataPlane
from apigateway.core.constants import PLUGIN_GATEWAY_PREFIX


def _get_default_data_plane_id() -> int:
    return DataPlane.objects.get_default().id


def _resolve_data_plane_ids_by_names(data_plane_names: List[str]) -> List[int]:
    # it not care about if the data plane is active or inactive, only bound
    # only release to the data plane when the data plane is active
    data_planes = DataPlane.objects.filter(name__in=data_plane_names)
    name_to_id = {item.name: item.id for item in data_planes}

    missing_names = [name for name in data_plane_names if name not in name_to_id]
    if missing_names:
        raise ValidationError({"data_planes": f"data planes not found: {', '.join(sorted(set(missing_names)))}"})

    data_plane_ids = [name_to_id[name] for name in data_plane_names]
    return list(set(data_plane_ids))


def _get_te_bp_sync_data_plane_ids(default_data_plane_id: int) -> List[int]:
    """if bk-plugins data plane gray:
    - not start: return default data plane id
    - start: return default data plane id and bk-plugins data plane id (binding 2 data planes)
    - done: return bk-plugins data plane id (binding 1 new data plane)
    """
    bp_data_plane_name = settings.BK_PLUGINS_DATA_PLANE_NAME
    bp_data_plane = DataPlane.objects.filter(name=bp_data_plane_name).first()
    bp_data_plane_id = bp_data_plane and bp_data_plane.id

    if not bp_data_plane_id:
        return [default_data_plane_id]

    gray_stage = getattr(settings, "BK_PLUGINS_DATA_PLANE_GRAY_STAGE", BkPluginsDataPlaneGrayStageEnum.NOT_START.value)
    if gray_stage == BkPluginsDataPlaneGrayStageEnum.START.value:
        return list({default_data_plane_id, bp_data_plane_id})
    if gray_stage == BkPluginsDataPlaneGrayStageEnum.DONE.value:
        return [bp_data_plane_id]

    # TODO: after remove the BK_PLUGINS_DATA_PLANE_GRAY_STAGE, change this to bp_data_plane_id
    return [default_data_plane_id]


def get_sync_data_plane_ids(gateway_name: str, data_plane_names: Optional[List[str]] = None) -> List[int]:
    if data_plane_names:
        return _resolve_data_plane_ids_by_names(data_plane_names)

    default_data_plane_id = _get_default_data_plane_id()
    if settings.EDITION == "te" and gateway_name.startswith(PLUGIN_GATEWAY_PREFIX):
        return _get_te_bp_sync_data_plane_ids(default_data_plane_id)

    return [default_data_plane_id]
