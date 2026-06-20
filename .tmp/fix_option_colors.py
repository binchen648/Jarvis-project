# -*- coding: utf-8 -*-
import os, glob, re
os.chdir(r"D:\Jarvis project")

count = 0
for f in glob.glob("templates/**/*.html", recursive=True):
    with open(f, "r", encoding="utf-8") as fp:
        c = fp.read()
    
    if "themeSwitcher" not in c:
        continue
    
    # Find the select block and add dark bg to each option
    # Pattern: <option value="xxx">Label</option>
    # Replace with: <option value="xxx" style="background:#08080D;color:white;">Label</option>
    
    # Only process options inside themeSwitcher select
    # Find the select element
    select_start = c.find('<select id="themeSwitcher"')
    if select_start < 0:
        select_start = c.find("<select id='themeSwitcher'")
    if select_start < 0:
        continue
    
    select_end = c.find("</select>", select_start)
    select_block = c[select_start:select_end]
    
    # Check if options already have background styling
    if 'background:#08080D' in select_block:
        continue
    
    # Add style to each option
    new_block = re.sub(
        r'<option value="([^"]+)"([^>]*)>',
        r'<option value="\1" style="background:#08080D;color:white;"\2>',
        select_block
    )
    
    c = c[:select_start] + new_block + c[select_end:]
    
    with open(f, "w", encoding="utf-8") as fp:
        fp.write(c)
    count += 1
    print(f"Fixed: {f}")

print(f"\nFixed {count} files")
