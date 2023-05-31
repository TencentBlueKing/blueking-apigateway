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
import time
from typing import Optional

import cattr
import jwt
from attrs import define, field
from django.utils.translation import gettext_lazy
from redis import Redis
from rest_framework import permissions

from apigateway.core.micro_gateway_config import MicroGatewayJWTAuth
from apigateway.core.models import MicroGateway
from apigateway.utils.redis_utils import get_default_redis_client, get_redis_key

logger = logging.getLogger(__name__)


@define(slots=True)
class MicroGatewayJWTPayload:
    sub: str = ""
    name: str = ""
    iat: int = 0
    exp: int = 0


@define
class MicroGatewayInstancePermission(permissions.BasePermission):
    """
    获取微网关实例并认证权限
    """

    message = gettext_lazy("当前微网关实例无权限调用")
    subject = "micro-gateway"
    default_algorithm = "HS512"
    tolerable_seconds = 60
    redis: Redis = field(factory=get_default_redis_client)

    def has_permission(self, request, view):
        micro_gateway = self._get_micro_gateway(view)
        if not micro_gateway:
            return False

        token = self._get_token(request)
        if not token:
            return False

        cache_key = get_redis_key(f"{self.subject}:{micro_gateway.id}:{token}")
        jwt_payload = self._get_result_from_cache(cache_key)
        if jwt_payload is None:
            jwt_auth_info = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
            jwt_payload = self._decode_jwt(jwt_auth_info.secret_key, token)

        if not jwt_payload:
            logger.warning("can not decode jwt token %s for gateway %s", token, micro_gateway.id)
            return False

        logger.debug(
            "checking micro-gateway instance %s permission for client %s",
            micro_gateway.pk,
            jwt_payload.name,
        )

        try:
            return self._check_jwt_permissions(jwt_payload)
        finally:
            self._cache_token_check_result(cache_key, jwt_payload)

    def _cache_token_check_result(self, cache_key: str, jwt_payload: MicroGatewayJWTPayload):
        """
        缓存 token 验证结果
        """

        expires = jwt_payload.exp - int(time.time()) + self.tolerable_seconds
        if expires < self.tolerable_seconds:
            expires = self.tolerable_seconds

        with self.redis.pipeline() as pipe:
            pipe.hmset(
                cache_key,
                {
                    "sub": jwt_payload.sub,
                    "name": jwt_payload.name,
                    "iat": jwt_payload.iat,
                    "exp": jwt_payload.exp,
                },
            )
            pipe.expire(cache_key, expires)

    def _get_result_from_cache(self, cache_key: str) -> Optional[MicroGatewayJWTPayload]:
        """
        从缓存中获取 token 验证结果
        """
        result = self.redis.hgetall(cache_key)
        if result is None:
            return None

        try:
            return MicroGatewayJWTPayload(
                name=result["name"].decode(),
                sub=result["sub"].decode(),
                iat=int(result["iat"]),
                exp=int(result["exp"]),
            )
        except Exception:
            # 因格式问题无法解析
            return None

    def _check_jwt_permissions(self, jwt_payload: MicroGatewayJWTPayload) -> bool:
        """
        检查 jwt 权限
        """

        if jwt_payload.sub != self.subject:
            return False

        now = int(time.time())
        # 判断生效时间，允许一定误差
        if jwt_payload.iat - self.tolerable_seconds < now < jwt_payload.exp + self.tolerable_seconds:
            return True

        return False

    def _decode_jwt(self, secret, token) -> Optional[MicroGatewayJWTPayload]:
        """
        解码 jwt
        """

        try:
            jwt_header = jwt.get_unverified_header(token)
            algorithm = jwt_header.get("alg", self.default_algorithm)
            decoded = jwt.decode(token, secret, algorithms=[algorithm])
        except Exception:
            return None

        return cattr.structure(decoded, MicroGatewayJWTPayload)

    def _get_micro_gateway(self, view) -> Optional[MicroGateway]:
        """
        根据路径参数 instance_id 获取微网关对象
        如果 instance_id 不在路径参数中，则返回 None，忽略此权限验证
        """
        instance_id = view.kwargs.get("instance_id")
        if not instance_id:
            return None

        return MicroGateway.objects.filter(pk=instance_id).first()

    def _get_token(self, request):
        """
        从请求头获取 JWT token
        """
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if not authorization:
            return ""

        prefix, _, token = authorization.partition(" ")
        if prefix != "Bearer":
            return ""

        return token
