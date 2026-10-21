from django.db import models

class Site(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Page(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="pages")
    slug = models.SlugField()
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    published = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"],
                name="unique_page_slug_per_site",
            ),
        ]
        ordering = ["slug"]
