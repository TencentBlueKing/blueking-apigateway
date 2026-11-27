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
from django.urls import include, path

from .views import (
    SkillCurrentVersionUpdateApi,
    SkillDownloadApi,
    SkillFileListApi,
    SkillListCreateApi,
    SkillPackageCheckApi,
    SkillRetrieveUpdateDestroyApi,
    SkillTagListApi,
    SkillUpdateStatusApi,
    SkillVersionListCreateApi,
)

urlpatterns = [
    path("", SkillListCreateApi.as_view(), name="skill.list_create"),
    path("-/tags/", SkillTagListApi.as_view(), name="skill.tag.list"),
    path("-/check/", SkillPackageCheckApi.as_view(), name="skill.package.check"),
    path(
        "<str:skill_id>/",
        include(
            [
                path("", SkillRetrieveUpdateDestroyApi.as_view(), name="skill.retrieve_update_destroy"),
                path("versions/", SkillVersionListCreateApi.as_view(), name="skill.version.list_create"),
                path("current-version/", SkillCurrentVersionUpdateApi.as_view(), name="skill.current_version.update"),
                path("status/", SkillUpdateStatusApi.as_view(), name="skill.status.update"),
                path("files/", SkillFileListApi.as_view(), name="skill.file.list"),
                path("download/", SkillDownloadApi.as_view(), name="skill.download"),
                path("versions/<str:version>/files/", SkillFileListApi.as_view(), name="skill.version.file.list"),
                path("versions/<str:version>/download/", SkillDownloadApi.as_view(), name="skill.version.download"),
            ]
        ),
    ),
]
