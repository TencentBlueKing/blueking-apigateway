from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^announcements/$", views.get_current_information, name="get_current_information"),
]
