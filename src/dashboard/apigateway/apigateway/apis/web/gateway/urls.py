from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.GatewayListCreateApi.as_view(), name="gateways.list_create"),
    path(
        # 使用 gateway_id，复用 GatewayPermission 的权限校验
        "<int:gateway_id>/",
        include(
            [
                path("", views.GatewayRetrieveUpdateDestroyApi.as_view(), name="gateways.retrieve_update_destroy"),
                path("status/", views.GatewayUpdateStatusApi.as_view(), name="gateways.update_status"),
            ]
        ),
    ),
]
