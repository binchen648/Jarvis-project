from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from apps.userprofile.models import UserProfile


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Display user profile."""
    model = UserProfile
    template_name = "userprofile/profile_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile with HTMX form submission."""
    model = UserProfile
    template_name = "userprofile/profile_edit.html"
    context_object_name = "profile"
    fields = ["bio", "avatar", "social_links"]
    success_url = reverse_lazy("accounts:profile_detail")

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
