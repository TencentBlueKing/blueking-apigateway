import logging

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.apps.rbac.constants import GATEWAY_ROLE_ACTIONS, GatewayActionEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import is_iam_auth_active, is_iam_gateway_action_allowed
from apigateway.components.bkiam import BkIamError
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


class GatewayActionPermission(permissions.BasePermission):
    """获取网关并按 View 声明的 Action 验证网关权限。"""

    message = gettext_lazy("当前用户无访问网关权限")

    def has_permission(self, request, view):
        request.gateway_member = None
        gateway = self.get_gateway_object(view)
        # 路径参数 gateway_id 不存在时，忽略网关权限校验
        if gateway is None:
            return True

        request.gateway = gateway
        # 跳过网关权限校验
        if getattr(view, "gateway_permission_exempt", False):
            return True

        # 本地成员用于请求上下文，以及 IAM 未启用或调用失败时的本地鉴权
        member = GatewayMember.objects.get_gateway_member(gateway.id, request.user.username)
        if member is not None:
            request.gateway_member = member

        required_action = self.get_required_action(request, view)
        if not is_iam_auth_active():
            return self._is_locally_allowed(member, required_action)

        try:
            return is_iam_gateway_action_allowed(request.user.username, gateway.id, required_action)
        except BkIamError as exc:
            logger.warning(
                "gateway IAM authorization failed, fallback to local, "
                "error=%s operation=%s status_code=%s gateway_id=%s username=%s action_id=%s",
                exc.__class__.__name__,
                exc.operation,
                exc.status_code,
                gateway.id,
                request.user.username,
                required_action,
                exc_info=True,
            )
            return self._is_locally_allowed(member, required_action)

    def _is_locally_allowed(self, member: GatewayMember | None, required_action: str) -> bool:
        if member is None:
            return False

        allowed_actions = GATEWAY_ROLE_ACTIONS.get(member.role)
        if allowed_actions is None:
            logger.warning(
                "unknown gateway member role, gateway_id=%s username=%s role=%s",
                member.gateway_id,
                member.username,
                member.role,
            )
            return False
        return required_action in allowed_actions

    def get_gateway_object(self, view):
        """根据路径参数 gateway_id 获取网关对象。"""
        lookup_url_kwarg = "gateway_id"
        if lookup_url_kwarg not in view.kwargs:
            return None

        return get_object_or_404(Gateway, id=view.kwargs[lookup_url_kwarg])

    def get_required_action(self, request, view) -> str:
        """解析当前请求需要的网关 Action。

        同一 View 若不同 HTTP 方法需要不同 Action，用 gateway_action_map（如 GET 可读、写操作需管理）。
        map 未命中时再用 gateway_action；两者都没有则默认 manage_gateway。
        """
        action_map = getattr(view, "gateway_action_map", None) or {}
        action = action_map.get(request.method) or getattr(
            view, "gateway_action", GatewayActionEnum.MANAGE_GATEWAY.value
        )
        if action not in GatewayActionEnum.get_values():
            raise ImproperlyConfigured(f"invalid gateway action: {action}")
        return action
