# -*- coding: utf-8 -*-
import os, sys, re
os.chdir(r"D:\Jarvis project")

with open("templates/dashboard/home.html", "r", encoding="utf-8") as f:
    c = f.read()

# Count braces in style block
style_match = re.search(r'<style>(.*?)</style>', c, re.DOTALL)
if style_match:
    css = style_match.group(1)
    opens = css.count('{')
    closes = css.count('}')
    status = 'OK' if opens == closes else 'MISMATCH ' + str(opens) + ' vs ' + str(closes)
    print("CSS braces: " + status)

# Check JS
script_match = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
if script_match:
    js = script_match.group(1)
    print("Has applyTheme: " + str('applyTheme' in js))
    print("Has DOMContentLoaded: " + str('DOMContentLoaded' in js))
    print("Has var switcher: " + str('var switcher' in js or 'const switcher' in js))
