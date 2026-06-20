# -*- coding: utf-8 -*-
import os, sys
os.chdir(r"D:\Jarvis project")

with open("templates/dashboard/home.html", "r", encoding="utf-8") as f:
    c = f.read()

# Count opening and closing braces in style block
import re
style_match = re.search(r'<style>(.*?)</style>', c, re.DOTALL)
if style_match:
    css = style_match.group(1)
    opens = css.count('{')
    closes = css.count('}')
    print(f"CSS braces: {opens} open, {closes} close -> {'OK' if opens == closes else 'MISMATCH'}")
    
    # Check specific rules
    for rule in [':root', '[data-theme="ocean"]', 'body::before', '.glass-card', '.nav-active']:
        if rule in css:
            # Check if closing brace exists
            idx = css.index(rule)
            next_brace = css.find('}', idx)
            print(f"  {rule}: found at {idx}, next } at {next_brace}")
else:
    print("ERROR: No <style> block found!")

# Check JS
script_match = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
if script_match:
    js = script_match.group(1)
    print(f"\nJS length: {len(js)} chars")
    print(f"Has applyTheme: {'applyTheme' in js}")
    print(f"Has DOMContentLoaded: {'DOMContentLoaded' in js}")
    print(f"Has var switcher: {'var switcher' in js}")
    print(f"Has if(switcher): {'if (switcher)' in js}")
