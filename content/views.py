from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from .models import Page, Site
from .serializers import PageSerializer

class ReadOnlyOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user.is_authenticated and request.user.is_staff)

class ScopedPages:
    serializer_class = PageSerializer
    permission_classes = [ReadOnlyOrStaff]

    def get_site(self):
        return get_object_or_404(Site, slug=self.kwargs["site_slug"])

    def get_queryset(self):
        pages = Page.objects.filter(site=self.get_site())
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return pages
        return pages.filter(published=True)

class PageList(ScopedPages, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(site=self.get_site())

class PageDetail(ScopedPages, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"
