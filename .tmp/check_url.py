import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.demo"
import django
django.setup()
from django.urls import reverse, resolve
try:
    url = reverse("chat:agent_state", kwargs={"pk": 1})
    print(f"URL: {url}")
    match = resolve(url)
    print(f"View: {match.func}")
except Exception as e:
    print(f"Error: {e}")
