from django.contrib import admin
from django.urls import path

from content.views import PageDetail, PageList

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/sites/<slug:site_slug>/pages/", PageList.as_view(), name="page-list"),
    path(
        "api/sites/<slug:site_slug>/pages/<slug:slug>/",
        PageDetail.as_view(),
        name="page-detail",
    ),
]
