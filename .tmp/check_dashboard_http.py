# -*- coding: utf-8 -*-
import sys
try:
    from urllib.request import urlopen, Request
except ImportError:
    import urllib2 as urllib

# Try with cookies to access protected pages
import http.cookiejar
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# First login
login_url = "http://localhost:8001/accounts/login/"
resp = opener.open(login_url)
html = resp.read().decode('utf-8')

# Get CSRF token
import re
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
if csrf:
    csrf_token = csrf.group(1)
    
    # Login
    login_data = "csrfmiddlewaretoken={}&login=admin&password=admin123".format(csrf_token)
    req = Request(login_url, data=login_data.encode())
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    resp = opener.open(req)
    print("Login status:", resp.getcode())

# Now get dashboard
resp = opener.open("http://localhost:8001/")
html = resp.read().decode('utf-8')

# Check key elements
checks = [
    ("title", '<title>Jarvis OS'),
    ("applyTheme", 'applyTheme'),
    ("DOMContentLoaded", 'DOMContentLoaded'),
    ("themeSwitcher", 'themeSwitcher'),
    ("glass-card", 'glass-card'),
    ("nav-active", 'nav-active'),
    ("body background", 'var(--surface-bg)'),
]
for name, pattern in checks:
    found = pattern in html
    print(f"  {'OK' if found else 'MISS'}: {name}")

print(f"\nHTML length: {len(html)} chars")
print(f"Has nav-active: {'nav-active' in html}")
print(f"Has applyTheme: {'applyTheme' in html}")
