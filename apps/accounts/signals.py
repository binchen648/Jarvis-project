from django.dispatch import receiver
from allauth.account.signals import user_signed_up


@receiver(user_signed_up, dispatch_uid="create_user_profile_on_signup")
def create_user_profile(sender, **kwargs):
    """Auto-create UserProfile when a user signs up via allauth.

    Uses get_or_create to be idempotent if signal fires twice.
    Uses dispatch_uid to prevent duplicate connections.
    """
    user = kwargs["user"]
    from apps.userprofile.models import UserProfile
    UserProfile.objects.get_or_create(user=user)
