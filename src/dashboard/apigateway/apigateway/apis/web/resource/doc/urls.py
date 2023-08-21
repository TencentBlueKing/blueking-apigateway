from django.urls import path

from . import views

urlpatterns = [
    path("", views.DocListCreateApi.as_view(), name="resource_doc.list_create"),
    path("<int:id>/", views.DocUpdateDestroyApi.as_view(), name="resource_doc.update_destroy"),
]
