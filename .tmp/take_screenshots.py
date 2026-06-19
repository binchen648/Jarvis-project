import os, sys
sys.path.insert(0, r"D:\Jarvis project")
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.demo"

import django
django.setup()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    # Login first
    page.goto("http://localhost:8001/login/")
    page.wait_for_load_state("networkidle")
    
    # Check if we're on a login page
    title = page.title()
    print(f"Login page title: {title}")
    
    # Try to find login inputs
    login_input = page.query_selector('input[name="login"], input[type="text"], input[name="username"]')
    if login_input:
        login_input.fill("admin")
    
    password_input = page.query_selector('input[name="password"], input[type="password"]')
    if password_input:
        password_input.fill("admin123")
    
    submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
    if submit_btn:
        submit_btn.click()
        page.wait_for_load_state("networkidle")
    
    # Dashboard
    page.goto("http://localhost:8001/dashboard/")
    page.wait_for_timeout(2000)
    page.screenshot(path=r"D:\Jarvis project\.tmp\layout-dashboard.png", full_page=True)
    print("Dashboard screenshot saved")
    
    # Memory Timeline
    page.goto("http://localhost:8001/memory/timeline/")
    page.wait_for_timeout(2000)
    page.screenshot(path=r"D:\Jarvis project\.tmp\layout-memory.png", full_page=True)
    print("Memory screenshot saved")
    
    browser.close()
    print("Done!")
