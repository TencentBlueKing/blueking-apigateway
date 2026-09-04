from django.urls import path

from . import views

urlpatterns = [
    path("", views.GatewayMemberListCreateApi.as_view(), name="gateway_member.list_create"),
    path(
        "<int:member_id>/",
        views.GatewayMemberUpdateDestroyApi.as_view(),
        name="gateway_member.update_destroy",
    ),
]
