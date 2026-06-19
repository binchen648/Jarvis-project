import os, sys
sys.path.insert(0, r"D:\Jarvis project")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.demo"
import django
django.setup()
from django.template import loader

t = loader.get_template("chat/conversation_detail.html")
src_file = t.template.source
print("Source file length:", len(src_file))
print("Has extends base:", "{% extends" in src_file)
print("Has ai_studio title:", "Jarvis Agent Console" in src_file)
print("Has WebSocket:", "WebSocket" in src_file)
