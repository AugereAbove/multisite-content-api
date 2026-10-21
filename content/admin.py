from django.contrib import admin

from .models import Page, Site

admin.site.register(Site)
admin.site.register(Page)
