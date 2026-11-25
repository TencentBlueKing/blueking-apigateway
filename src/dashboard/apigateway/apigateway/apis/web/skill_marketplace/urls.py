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
    SkillMarketplaceSkillCountApi,
    SkillMarketplaceSkillDownloadApi,
    SkillMarketplaceSkillFileListApi,
    SkillMarketplaceSkillListApi,
    SkillMarketplaceSkillRetrieveApi,
    SkillMarketplaceSkillVersionListApi,
    SkillMarketplaceTagListApi,
)

urlpatterns = [
    path("tags/", SkillMarketplaceTagListApi.as_view(), name="skill_marketplace.tag.list"),
    path(
        "skills/",
        include(
            [
                path("", SkillMarketplaceSkillListApi.as_view(), name="skill_marketplace.skill.list"),
                path("-/counts/", SkillMarketplaceSkillCountApi.as_view(), name="skill_marketplace.skill.counts"),
                path(
                    "<str:skill_id>/",
                    include(
                        [
                            path(
                                "",
                                SkillMarketplaceSkillRetrieveApi.as_view(),
                                name="skill_marketplace.skill.retrieve",
                            ),
                            path(
                                "versions/",
                                SkillMarketplaceSkillVersionListApi.as_view(),
                                name="skill_marketplace.skill.version.list",
                            ),
                            path(
                                "files/",
                                SkillMarketplaceSkillFileListApi.as_view(),
                                name="skill_marketplace.skill.file.list",
                            ),
                            path(
                                "download/",
                                SkillMarketplaceSkillDownloadApi.as_view(),
                                name="skill_marketplace.skill.download",
                            ),
                            path(
                                "versions/<str:version>/files/",
                                SkillMarketplaceSkillFileListApi.as_view(),
                                name="skill_marketplace.skill.version.file.list",
                            ),
                            path(
                                "versions/<str:version>/download/",
                                SkillMarketplaceSkillDownloadApi.as_view(),
                                name="skill_marketplace.skill.version.download",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
