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
from datetime import timedelta

import pytest
from ddf import G
from django.utils import timezone

from apigateway.apps.support.models import ResourceDocVersion
from apigateway.controller.tasks.clean_task import delete_old_publish_events, delete_old_resource_doc_version_records
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import PublishEvent


@pytest.mark.django_db
def test_delete_old_publish_events(fake_publish_event, fake_release_history):
    old_time = timezone.now() - timedelta(days=366)
    new_time = timezone.now()
    fake_publish_event.created_time = new_time
    fake_publish_event.save()

    G(
        PublishEvent,
        publish=fake_release_history,
        created_time=old_time,
        name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
        status=PublishEventStatusTypeEnum.SUCCESS.value,
    )

    delete_old_publish_events()

    assert PublishEvent.objects.filter(created_time__lt=old_time).count() == 0
    assert PublishEvent.objects.filter(created_time__gte=old_time).count() == 1


@pytest.mark.django_db
def test_delete_old_resource_version_records(fake_gateway, fake_resource_version, fake_resource_doc):
    old_time = timezone.now() - timedelta(days=366)
    fake_resource_doc.created_time = old_time
    fake_resource_doc.save()

    new_time = timezone.now()
    G(
        ResourceDocVersion,
        gateway=fake_gateway,
        resource_version=fake_resource_version,
        created_time=new_time,
    )

    delete_old_resource_doc_version_records()

    assert ResourceDocVersion.objects.filter(created_time__lt=old_time).count() == 0
    assert ResourceDocVersion.objects.filter(created_time__gte=old_time).count() == 1
