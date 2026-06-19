import time

from django.test import TestCase
from django.db import IntegrityError
from django.db.models import URLField, TextField, JSONField
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.utils import timezone

from apps.userprofile.models import UserProfile
from apps.userprofile.admin import UserProfileAdmin

User = get_user_model()


class UserProfileModelTests(TestCase):
    """Tests for the UserProfile model — fields, defaults, constraints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="modeluser", password="pass123",
        )
        # UserProfile is NOT auto-created on User.create_user — signal
        # (user_signed_up) only fires on allauth signup flow.
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def test_str_method(self):
        """__str__ returns \"{user}'s profile\"."""
        expected = f"{self.user}'s profile"
        self.assertEqual(str(self.profile), expected)

    def test_default_field_values(self):
        """bio and avatar default to '', social_links defaults to {} (dict)."""
        self.assertEqual(self.profile.bio, "")
        self.assertEqual(self.profile.avatar, "")
        self.assertIsInstance(self.profile.social_links, dict)
        self.assertEqual(self.profile.social_links, {})

    def test_bio_max_length(self):
        """bio field has max_length=500."""
        field = UserProfile._meta.get_field("bio")
        self.assertEqual(field.max_length, 500)

    def test_avatar_max_length(self):
        """avatar field has max_length=500."""
        field = UserProfile._meta.get_field("avatar")
        self.assertEqual(field.max_length, 500)

    def test_created_at_auto_set_on_create(self):
        """created_at is set automatically when profile is created."""
        self.assertIsNotNone(self.profile.created_at)
        self.assertLessEqual(
            self.profile.created_at, timezone.now(),
        )

    def test_updated_at_auto_set_on_create(self):
        """updated_at is set automatically when profile is created."""
        self.assertIsNotNone(self.profile.updated_at)

    def test_updated_at_changes_on_update(self):
        """updated_at refreshes when the profile is saved."""
        original_updated = self.profile.updated_at
        self.profile.bio = "Updated bio"
        time.sleep(0.05)  # Ensure measurable time delta (DB-agnostic)
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertGreater(self.profile.updated_at, original_updated)

    def test_one_to_one_uniqueness(self):
        """Cannot create a second UserProfile for the same user."""
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=self.user)

    def test_cascade_delete_user_deletes_profile(self):
        """Deleting a user deletes their UserProfile (CASCADE)."""
        user_pk = self.user.pk
        profile_pk = self.profile.pk
        self.user.delete()
        self.assertFalse(
            UserProfile.objects.filter(pk=profile_pk).exists(),
        )

    def test_cascade_delete_profile_keeps_user(self):
        """Deleting a profile does NOT delete the user."""
        user_pk = self.user.pk
        self.profile.delete()
        self.assertTrue(User.objects.filter(pk=user_pk).exists())

    def test_json_field_stores_and_retrieves(self):
        """social_links correctly serializes/deserializes JSON."""
        links = {"github": "https://github.com/jarvis", "twitter": "@jarvis"}
        self.profile.social_links = links
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.social_links, links)

    def test_db_table(self):
        """Model uses custom db_table 'userprofile_profile'."""
        self.assertEqual(
            UserProfile._meta.db_table, "userprofile_profile",
        )

    def test_verbose_names(self):
        """Verbose names are set in Chinese."""
        meta = UserProfile._meta
        self.assertEqual(meta.verbose_name, "用户资料")
        self.assertEqual(meta.verbose_name_plural, "用户资料")

    def test_related_name_from_user(self):
        """Access profile via user.profile (related_name='profile')."""
        self.assertEqual(self.user.profile, self.profile)

    def test_bio_blank_and_empty_allowed(self):
        """bio is blank=True, so empty string passes full_clean."""
        self.profile.bio = ""
        self.profile.full_clean()
        self.assertEqual(self.profile.bio, "")

    def test_avatar_blank_and_empty_allowed(self):
        """avatar is blank=True, so empty string passes full_clean."""
        self.profile.avatar = ""
        self.profile.full_clean()
        self.assertEqual(self.profile.avatar, "")

    def test_avatar_field_type(self):
        """avatar is a URLField."""
        field = UserProfile._meta.get_field("avatar")
        self.assertIsInstance(field, URLField)

    def test_bio_field_type(self):
        """bio is a TextField."""
        field = UserProfile._meta.get_field("bio")
        self.assertIsInstance(field, TextField)

    def test_social_links_field_type(self):
        """social_links is a JSONField."""
        field = UserProfile._meta.get_field("social_links")
        self.assertIsInstance(field, JSONField)

    def test_field_verbose_names(self):
        """Field-level verbose_name is set correctly."""
        self.assertEqual(
            UserProfile._meta.get_field("bio").verbose_name, "个人简介",
        )
        self.assertEqual(
            UserProfile._meta.get_field("avatar").verbose_name, "头像 URL",
        )
        self.assertEqual(
            UserProfile._meta.get_field("social_links").verbose_name, "社交链接",
        )


class UserProfileAdminTests(TestCase):
    """Tests for UserProfileAdmin registration and configuration."""

    def test_admin_registered(self):
        """UserProfileAdmin is registered for UserProfile model."""
        self.assertIn(UserProfile, site._registry)

    def test_admin_list_display(self):
        """UserProfileAdmin.list_display == ['user']."""
        registered_admin = site._registry[UserProfile]
        self.assertEqual(registered_admin.list_display, ["user"])

    def test_admin_model_admin_type(self):
        """Registered admin is a UserProfileAdmin instance."""
        registered_admin = site._registry[UserProfile]
        self.assertIsInstance(registered_admin, UserProfileAdmin)
