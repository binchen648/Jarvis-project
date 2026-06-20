# -*- coding: utf-8 -*-
import os, sys
os.chdir(r"D:\Jarvis project")
sys.path.insert(0, ".")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    
    # Login
    page.goto("http://localhost:8001/accounts/login/")
    page.fill('input[name="login"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    
    # Go to Dashboard
    page.goto("http://localhost:8001/")
    page.wait_for_timeout(2000)
    
    # Save screenshot
    page.screenshot(path=r"D:\Jarvis project\.playwright-mcp\screenshot-dashboard-check.png", full_page=True)
    print("Screenshot saved")
    
    # Check page title
    print("Title:", page.title())
    
    # Check console errors
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.reload()
    page.wait_for_timeout(2000)
    if errors:
        print("Errors:", errors)
    else:
        print("No console errors")
    
    # Check if body has background color
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    print("Body BG:", bg)
    
    # Check if CSS is loading
    css_vars = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary')")
    print("Primary CSS var:", css_vars)
    
    browser.close()
