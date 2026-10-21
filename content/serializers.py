from rest_framework import serializers

from .models import Page

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["slug", "title", "body", "published", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_slug(self, value):
        view = self.context.get("view")
        if view is None:
            return value

        matches = Page.objects.filter(
            site__slug=view.kwargs["site_slug"], slug=value,
        )
        if self.instance is not None:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError(
                "A page with this slug already exists on this site.",
            )
        return value
