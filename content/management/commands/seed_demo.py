from django.core.management.base import BaseCommand

from content.models import Page, Site

class Command(BaseCommand):
    help = "Create demo sites and pages without changing existing content."

    def handle(self, *args, **options):
        sites_created = 0
        pages_created = 0
        examples = [
            ("main", "Main site", [
                ("hello", "Hello", "Welcome to the main site.", True),
                ("draft", "Work in progress", "This page is not public.", False),
            ]),
            ("notes", "Notes", [
                ("hello", "Hello from Notes", "A separate site with the same page slug.", True),
            ]),
        ]
        for site_slug, site_name, pages in examples:
            site, created = Site.objects.get_or_create(
                slug=site_slug, defaults={"name": site_name},
            )
            sites_created += created
            for slug, title, body, published in pages:
                _, created = Page.objects.get_or_create(
                    site=site,
                    slug=slug,
                    defaults={"title": title, "body": body, "published": published},
                )
                pages_created += created

        self.stdout.write(f"Created {sites_created} sites and {pages_created} pages.")
