from io import StringIO

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Page, Site

class MultisiteAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.primary = Site.objects.create(name="Main site", slug="main")
        cls.secondary = Site.objects.create(name="Second site", slug="second")
        cls.empty = Site.objects.create(name="Empty site", slug="empty")
        cls.page = Page.objects.create(
            site=cls.primary, slug="hello", title="Main hello", published=True,
        )
        cls.other_page = Page.objects.create(
            site=cls.secondary, slug="hello", title="Second hello", published=True,
        )
        cls.draft = Page.objects.create(
            site=cls.primary, slug="draft", title="Unfinished page",
        )
        users = get_user_model()
        cls.editor = users.objects.create_user(
            username="editor", password="testpass", is_staff=True,
        )
        cls.reader = users.objects.create_user(username="reader", password="testpass")

    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("page-list", kwargs={"site_slug": "main"})
        self.detail_url = self.page_url("main", "hello")

    def page_url(self, site, slug):
        return reverse("page-detail", kwargs={"site_slug": site, "slug": slug})

    def test_public_list_contains_only_published_pages_from_selected_site(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([page["title"] for page in response.data], ["Main hello"])

    def test_identical_slugs_resolve_within_the_selected_site(self):
        response = self.client.get(self.page_url("second", "hello"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Second hello")

    def test_response_has_only_the_public_page_fields(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(
            set(response.data), {"slug", "title", "body", "published", "updated_at"},
        )

    def test_public_cannot_retrieve_a_draft(self):
        response = self.client.get(self.page_url("main", "draft"))
        self.assertEqual(response.status_code, 404)

    def test_signed_in_reader_cannot_retrieve_a_draft(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.page_url("main", "draft"))
        self.assertEqual(response.status_code, 404)

    def test_signed_in_reader_gets_only_published_pages(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(self.list_url)
        self.assertEqual([page["slug"] for page in response.data], ["hello"])

    def test_editor_can_list_drafts_in_slug_order(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(self.list_url)
        self.assertEqual([page["slug"] for page in response.data], ["draft", "hello"])

    def test_editor_can_retrieve_a_draft(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.get(self.page_url("main", "draft"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["published"])

    def test_unknown_site_returns_not_found(self):
        url = reverse("page-list", kwargs={"site_slug": "missing"})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_missing_page_returns_not_found(self):
        self.assertEqual(self.client.get(self.page_url("main", "missing")).status_code, 404)

    def test_page_in_another_site_does_not_resolve(self):
        response = self.client.get(self.page_url("second", "draft"))
        self.assertEqual(response.status_code, 404)

    def test_existing_site_without_pages_returns_an_empty_list(self):
        url = reverse("page-list", kwargs={"site_slug": "empty"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_anonymous_users_cannot_write(self):
        for method, url in [
            ("post", self.list_url),
            ("put", self.detail_url),
            ("patch", self.detail_url),
            ("delete", self.detail_url),
        ]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, {}, format="json")
                self.assertEqual(response.status_code, 403)
        self.assertTrue(Page.objects.filter(pk=self.page.pk).exists())

    def test_signed_in_readers_cannot_write(self):
        self.client.force_authenticate(user=self.reader)
        for method, url in [
            ("post", self.list_url),
            ("put", self.detail_url),
            ("patch", self.detail_url),
            ("delete", self.detail_url),
        ]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, {}, format="json")
                self.assertEqual(response.status_code, 403)

    def test_editor_creates_in_the_site_from_the_url(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, {
            "slug": "new", "title": "New page", "published": True,
            "site": self.secondary.pk,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Page.objects.filter(site=self.primary, slug="new").exists())
        self.assertFalse(Page.objects.filter(site=self.secondary, slug="new").exists())

    def test_new_pages_default_to_drafts(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, {
            "slug": "new", "title": "New page",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["published"])
        self.assertEqual(response.data["body"], "")

    def test_editor_can_publish_a_draft(self):
        self.client.force_authenticate(user=self.editor)
        url = self.page_url("main", "draft")
        self.assertEqual(self.client.patch(url, {"published": True}).status_code, 200)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_editor_can_replace_a_page_without_changing_its_site(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.put(self.detail_url, {
            "slug": "hello", "title": "Updated", "body": "New body",
            "published": True, "site": self.secondary.pk,
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title, "Updated")
        self.assertEqual(self.page.site_id, self.primary.pk)
        self.other_page.refresh_from_db()
        self.assertEqual(self.other_page.title, "Second hello")

    def test_editor_can_delete_a_page_without_touching_another_site(self):
        self.client.force_authenticate(user=self.editor)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 204)
        self.assertFalse(Page.objects.filter(pk=self.page.pk).exists())
        self.assertTrue(Page.objects.filter(pk=self.other_page.pk).exists())

    def test_editor_cannot_create_in_an_unknown_site(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse("page-list", kwargs={"site_slug": "missing"})
        response = self.client.post(url, {"slug": "new", "title": "New"})
        self.assertEqual(response.status_code, 404)

    def test_required_fields_are_validated(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.assertIn("title", response.data)

    def test_duplicate_slug_in_one_site_is_a_validation_error(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(self.list_url, {"slug": "hello", "title": "Duplicate"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)

    def test_renaming_to_an_existing_slug_is_a_validation_error(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {"slug": "draft"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("slug", response.data)
        self.page.refresh_from_db()
        self.assertEqual(self.page.slug, "hello")

    def test_same_slug_can_be_created_in_another_site(self):
        self.client.force_authenticate(user=self.editor)
        url = reverse("page-list", kwargs={"site_slug": "second"})
        response = self.client.post(url, {"slug": "draft", "title": "Second draft"})
        self.assertEqual(response.status_code, 201)

    def test_updated_at_cannot_be_supplied_by_the_client(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {
            "updated_at": "2000-01-01T00:00:00Z", "title": "Updated",
        })
        self.assertEqual(response.status_code, 200)
        self.page.refresh_from_db()
        self.assertNotEqual(self.page.updated_at.year, 2000)

    def test_database_rejects_duplicate_slugs_within_a_site(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Page.objects.create(site=self.primary, slug="hello", title="Duplicate")

    def test_deleting_a_site_deletes_only_its_pages(self):
        self.primary.delete()
        self.assertFalse(Page.objects.filter(pk=self.page.pk).exists())
        self.assertFalse(Page.objects.filter(pk=self.draft.pk).exists())
        self.assertTrue(Page.objects.filter(pk=self.other_page.pk).exists())

    def test_safe_methods_are_available_without_authentication(self):
        self.assertEqual(self.client.head(self.list_url).status_code, 200)
        self.assertEqual(self.client.options(self.list_url).status_code, 200)

    def test_admin_login_page_loads(self):
        self.assertEqual(self.client.get(reverse("admin:login")).status_code, 200)

    def test_editor_can_use_a_real_admin_session(self):
        self.assertTrue(self.client.login(username="editor", password="testpass"))
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        response = self.client.get(self.page_url("main", "draft"))
        self.assertEqual(response.status_code, 200)

    def test_session_writes_require_a_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="editor", password="testpass"))
        response = client.post(self.list_url, {"slug": "new", "title": "New"})
        self.assertEqual(response.status_code, 403)

class DemoSetupTests(TestCase):
    def run_seed(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        return output.getvalue()

    def test_demo_creates_two_sites_with_published_pages_and_a_draft(self):
        self.assertEqual(self.run_seed(), "Created 2 sites and 3 pages.\n")
        self.assertEqual(set(Site.objects.values_list("slug", flat=True)), {"main", "notes"})
        self.assertEqual(Page.objects.filter(published=True).count(), 2)
        self.assertFalse(Page.objects.get(site__slug="main", slug="draft").published)

    def test_running_demo_setup_again_does_not_duplicate_content(self):
        self.run_seed()
        self.assertEqual(self.run_seed(), "Created 0 sites and 0 pages.\n")
        self.assertEqual(Site.objects.count(), 2)
        self.assertEqual(Page.objects.count(), 3)

    def test_existing_names_and_page_content_are_preserved(self):
        site = Site.objects.create(name="Existing site", slug="main")
        page = Page.objects.create(
            site=site, slug="hello", title="Keep this", body="Existing text", published=False,
        )
        self.run_seed()
        site.refresh_from_db()
        page.refresh_from_db()
        self.assertEqual(site.name, "Existing site")
        self.assertEqual(page.title, "Keep this")
        self.assertEqual(page.body, "Existing text")
        self.assertFalse(page.published)

    def test_demo_setup_does_not_create_user_accounts(self):
        self.run_seed()
        self.assertEqual(get_user_model().objects.count(), 0)
