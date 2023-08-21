from django.urls import include, path

urlpatterns = [
    path("<int:resource_id>/docs/", include("apigateway.apis.web.resource.doc.urls")),
]
