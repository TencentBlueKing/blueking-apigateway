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
import logging

from blue_krill.async_utils.django_utils import delay_on_commit
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import Signal, receiver

from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding, IPGroup
from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.controller.tasks.syncing import revoke_release_by_stage
from apigateway.core import models
from apigateway.utils.redis_publisher import RedisPublisher
from apigateway.utils.redis_utils import get_default_redis_client, get_redis_key

logger = logging.getLogger(__name__)

reversion_update_signal = Signal(providing_args=["instance_id", "action"])
gateway_update_signal = Signal(providing_args=["gateway_id"])


@receiver(reversion_update_signal, dispatch_uid="reversion_update")
def _notify_reversion_update(sender, instance_id, action, *args, **kwargs):
    RedisPublisher().publish(f"{sender.__name__}[id={instance_id}] {action}")


@receiver(gateway_update_signal)
def _mark_gateway_updated(sender, gateway_id, *args, **kwargs):
    client = get_default_redis_client()
    client.sadd(get_redis_key(settings.APIGW_REVERSION_UPDATE_SET_KEY), gateway_id)


@receiver(post_save, sender=models.Gateway)
def _on_gateway_updated(sender, instance: models.Gateway, created: bool, **kwargs):
    if created:
        return

    if not instance.is_micro_gateway:
        return

    gateway_update_signal.send(sender, gateway_id=instance.pk)


@receiver(post_save, sender=PluginConfig)
@receiver(post_save, sender=PluginBinding)
@receiver(post_save, sender=AccessStrategy)
@receiver(post_save, sender=models.JWT)
@receiver(post_save, sender=models.Stage)
@receiver(post_save, sender=models.MicroGateway)
@receiver(post_save, sender=models.StageItemConfig)
@receiver(post_save, sender=models.SslCertificate)
def _on_gateway_related_updated(sender, instance, created: bool, **kwargs):
    if created:
        return

    gateway_update_signal.send(sender, gateway_id=instance.api_id)


@receiver(post_delete, sender=PluginConfig)
@receiver(post_delete, sender=PluginBinding)
@receiver(post_delete, sender=AccessStrategy)
def _on_gateway_related_delete(sender, instance, **kwargs):
    gateway_update_signal.send(sender, gateway_id=instance.api_id)


@receiver([post_save, post_delete], sender=AccessStrategyBinding)
def _on_gateway_access_strategy_binding_updated(sender, instance: AccessStrategyBinding, **kwargs):
    result = AccessStrategy.objects.filter(id=instance.access_strategy_id).values("api_id").first()
    if not result:
        return

    gateway_update_signal.send(sender, gateway_id=result["api_id"])


@receiver([post_save, post_delete], sender=IPGroup)
def _on_ip_group_changed(sender, instance, **kwargs):
    gateway_update_signal.send(sender, gateway_id=instance.api_id)


@receiver([post_delete], sender=models.Release)
def _on_release_deleted(sender, instance: models.Release, **kwargs):
    delay_on_commit(revoke_release_by_stage, instance.stage_id)  # type: ignore
