from django.http import Http404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.constants import GatewaySourceEnum, GatewayStatusEnum
from apigateway.core.models import Gateway


class GatewayDisplayablePermission(permissions.BasePermission):
    """Allow public gateways, or administrator access from API debug."""

    message = gettext_lazy("网关不存在")

    def has_permission(self, request, view):
        source = request.GET.get("source")
        if source == GatewaySourceEnum.API_DEBUG.value:
            gateway = self._get_gateway_with_permission(request, view)
        else:
            gateway = self._get_displayable_gateway(view)
        if not gateway:
            raise Http404

        request.gateway = gateway
        return True

    def _get_displayable_gateway(self, view):
        lookup_url_kwarg = "gateway_name"
        if lookup_url_kwarg not in view.kwargs:
            return None

        return Gateway.objects.filter(
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
            name=view.kwargs[lookup_url_kwarg],
        ).first()

    def _get_gateway_with_permission(self, request, view):
        lookup_url_kwarg = "gateway_name"
        if lookup_url_kwarg not in view.kwargs:
            return None

        gateway = Gateway.objects.filter(name=view.kwargs[lookup_url_kwarg]).first()
        if not gateway:
            return None
        if not GatewayMember.objects.is_gateway_administrator(gateway.id, request.user.username):
            return None
        return gateway
