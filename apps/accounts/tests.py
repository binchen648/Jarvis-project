from django.test import TestCase, RequestFactory
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model

from allauth.account.signals import user_signed_up

from apps.accounts.middleware import HtmxRedirectMiddleware
from apps.accounts.signals import create_user_profile  # noqa: F401 — ensure signal is connected
from apps.userprofile.models import UserProfile

User = get_user_model()


class HtmxRedirectMiddlewareTests(TestCase):
    """Tests for HtmxRedirectMiddleware.

    Verifies that HTMX requests with 302 redirects get converted to
    204 No Content with HX-Redirect header, while other requests pass through.
    """

    def setUp(self):
        self.factory = RequestFactory()

    @staticmethod
    def _redirect_response(request):
        return HttpResponseRedirect("/target/")

    @staticmethod
    def _ok_response(request):
        return HttpResponse("OK")

    def test_htmx_redirect_converted(self):
        """HTMX request with 302 → 204 No Content + HX-Redirect header."""
        request = self.factory.get("/profile/", HTTP_HX_REQUEST="true")
        middleware = HtmxRedirectMiddleware(self._redirect_response)
        response = middleware(request)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], "/target/")
        self.assertNotIn("Location", response)

    def test_non_htmx_redirect_unchanged(self):
        """Non-HTMX request with 302 → stays 302 (passthrough)."""
        request = self.factory.get("/profile/")
        middleware = HtmxRedirectMiddleware(self._redirect_response)
        response = middleware(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/target/")

    def test_htmx_non_redirect_unchanged(self):
        """HTMX request with 200 OK → stays 200 (passthrough)."""
        request = self.factory.get("/profile/", HTTP_HX_REQUEST="true")
        middleware = HtmxRedirectMiddleware(self._ok_response)
        response = middleware(request)
        self.assertEqual(response.status_code, 200)


class SignalTests(TestCase):
    """Tests for user_signed_up signal → UserProfile auto-creation."""

    def test_profile_created_on_signup(self):
        """UserProfile is created when user_signed_up signal fires."""
        user = User.objects.create_user(username="signaltest", password="pass123")
        user_signed_up.send(sender=User, user=user, request=None)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.bio, "")
        self.assertEqual(profile.avatar, "")
        self.assertEqual(profile.social_links, {})

    def test_profile_not_duplicated(self):
        """Signal fires twice → still only one UserProfile (idempotent)."""
        user = User.objects.create_user(username="duptest", password="pass123")
        user_signed_up.send(sender=User, user=user, request=None)
        user_signed_up.send(sender=User, user=user, request=None)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)


class ProfileViewsTests(TestCase):
    """Tests for ProfileDetailView and ProfileEditView."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="viewuser", password="pass123",
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    # -- ProfileDetailView --

    def test_profile_detail_requires_login(self):
        """Unauthenticated GET /profile/ → redirects to login."""
        url = reverse("accounts:profile_detail")
        response = self.client.get(url)
        expected_url = f"/accounts/login/?next={url}"
        self.assertRedirects(response, expected_url)

    def test_profile_detail_shows_profile(self):
        """Authenticated GET /profile/ → 200 with profile rendered."""
        self.client.login(username="viewuser", password="pass123")
        response = self.client.get(reverse("accounts:profile_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "userprofile/profile_detail.html")
        self.assertContains(response, "viewuser")
        self.assertContains(response, "暂未填写")

    # -- ProfileEditView --

    def test_profile_edit_requires_login(self):
        """Unauthenticated GET /profile/edit/ → redirects to login."""
        url = reverse("accounts:profile_edit")
        response = self.client.get(url)
        expected_url = f"/accounts/login/?next={url}"
        self.assertRedirects(response, expected_url)

    def test_profile_edit_updates_profile(self):
        """Authenticated POST → profile updated in DB + redirect to detail."""
        self.client.login(username="viewuser", password="pass123")
        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "bio": "Hello, world!",
                "avatar": "https://example.com/avatar.png",
                "social_links": '{"twitter": "@testuser"}',
            },
        )
        self.assertRedirects(response, reverse("accounts:profile_detail"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, "Hello, world!")
        self.assertEqual(self.profile.avatar, "https://example.com/avatar.png")
        self.assertEqual(self.profile.social_links, {"twitter": "@testuser"})


class URLTests(TestCase):
    """Tests that all accounts URL names resolve to expected paths."""

    def test_profile_detail_url_resolves(self):
        """reverse('accounts:profile_detail') → '/profile/'."""
        url = reverse("accounts:profile_detail")
        self.assertEqual(url, "/profile/")

    def test_profile_edit_url_resolves(self):
        """reverse('accounts:profile_edit') → '/profile/edit/'."""
        url = reverse("accounts:profile_edit")
        self.assertEqual(url, "/profile/edit/")

    def test_unprefixed_urls_fail_as_expected(self):
        """Un-namespaced URL names raise NoReverseMatch (by design)."""
        with self.assertRaises(NoReverseMatch):
            reverse("profile_detail")
        with self.assertRaises(NoReverseMatch):
            reverse("profile_edit")
