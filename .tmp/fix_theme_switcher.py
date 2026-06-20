# -*- coding: utf-8 -*-
import os, glob
os.chdir(r"D:\Jarvis project")

count = 0
for f in glob.glob("templates/**/*.html", recursive=True):
    with open(f, "r", encoding="utf-8") as fp:
        c = fp.read()
    
    if "themeSwitcher" not in c:
        continue
    
    # Check if already fixed
    if 'color-scheme:dark' in c:
        continue
    
    old = '<select id="themeSwitcher"'
    new = '<select id="themeSwitcher" style="color-scheme:dark;"'
    if old in c:
        c = c.replace(old, new)
        count += 1
        with open(f, "w", encoding="utf-8") as fp:
            fp.write(c)
        print(f"Fixed: {f}")

print(f"\nFixed {count} files")
