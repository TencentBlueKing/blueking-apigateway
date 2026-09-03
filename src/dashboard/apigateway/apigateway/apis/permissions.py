from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway


class GatewayPermission(permissions.BasePermission):
    """Load a gateway from the URL and require an administrator member."""

    message = gettext_lazy("当前用户无访问网关权限")

    def has_permission(self, request, view):
        gateway = self.get_gateway_object(view)
        if not gateway:
            return True

        request.gateway = gateway
        if getattr(view, "gateway_permission_exempt", False):
            return True

        return GatewayMember.objects.is_gateway_administrator(gateway.id, request.user.username)

    def get_gateway_object(self, view):
        lookup_url_kwarg = "gateway_id"
        if lookup_url_kwarg not in view.kwargs:
            return None

        return get_object_or_404(Gateway, id=view.kwargs[lookup_url_kwarg])


class GatewayApprovalPermission(GatewayPermission):
    """Load a gateway from the URL and require an approval member."""

    def has_permission(self, request, view):
        gateway = self.get_gateway_object(view)
        if not gateway:
            return True

        request.gateway = gateway
        if getattr(view, "gateway_permission_exempt", False):
            return True

        return GatewayMember.objects.has_gateway_approve_permission(gateway.id, request.user.username)
