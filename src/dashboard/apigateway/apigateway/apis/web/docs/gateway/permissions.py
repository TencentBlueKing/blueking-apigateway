from django.http import Http404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.apps.rbac.models import GatewayMember
from apigateway.common.tenant.query import gateway_filter_by_app_tenant_id
from apigateway.common.tenant.request import get_user_tenant_id
from apigateway.core.constants import GatewaySourceEnum, GatewayStatusEnum
from apigateway.core.models import Gateway


class GatewayDisplayablePermission(permissions.BasePermission):
    """Allow public or debug access within the user's tenant and global gateways."""

    message = gettext_lazy("网关不存在")

    def has_permission(self, request, view):
        gateway_name = view.kwargs.get("gateway_name")
        if not gateway_name:
            raise Http404

        queryset = gateway_filter_by_app_tenant_id(
            Gateway.objects.filter(name=gateway_name), get_user_tenant_id(request)
        )
        source = request.GET.get("source")
        if source == GatewaySourceEnum.API_DEBUG.value:
            gateway = self._get_gateway_with_permission(request, queryset)
        else:
            gateway = self._get_displayable_gateway(queryset)
        if not gateway:
            raise Http404

        request.gateway = gateway
        return True

    def _get_displayable_gateway(self, queryset):
        return queryset.filter(
            status=GatewayStatusEnum.ACTIVE.value,
            is_public=True,
        ).first()

    def _get_gateway_with_permission(self, request, queryset):
        gateway = queryset.first()
        if not gateway:
            return None
        if not GatewayMember.objects.is_gateway_administrator(gateway.id, request.user.username):
            return None
        return gateway
