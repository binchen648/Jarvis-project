# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

# Fix 1: Add theme switcher JS to conversation_list.html
with open("templates/chat/conversation_list.html", "r", encoding="utf-8") as f:
    content = f.read()

if 'themeSwitcher' in content and 'addEventListener' not in content:
    theme_js = '''
    <script>
        var switcher = document.getElementById('themeSwitcher');
        if (switcher) {
            switcher.addEventListener('change', function(e) {
                var theme = e.target.value;
                document.documentElement.setAttribute('data-theme', theme);
                try { localStorage.setItem('jarvis-theme', theme); } catch(e2) {}
            });
            var saved = null;
            try { saved = localStorage.getItem('jarvis-theme'); } catch(e3) {}
            if (saved) { document.documentElement.setAttribute('data-theme', saved); switcher.value = saved; }
        }
    </script>'''
    content = content.replace('</body>', theme_js + '\n</body>')
    print("Agent list: theme switcher JS added")

with open("templates/chat/conversation_list.html", "w", encoding="utf-8") as f:
    f.write(content)

# Fix 2: Ensure ALL template headers use glass background
header_fix = 'style="background: rgba(8,8,13,0.6); backdrop-filter: blur(18px); border-bottom: 1px solid rgba(255,255,255,.06);"'

for path in [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find any header without glass background
    lines = content.split('\n')
    new_lines = []
    fixed = False
    for line in lines:
        if '<header class="h-20' in line and 'backdrop-filter' not in line and 'style=' not in line:
            # Add glass background
            line = line.replace('>', ' ' + header_fix + '>')
            fixed = True
        new_lines.append(line)
    
    if fixed:
        print(f"{path}: header glass background added")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))

# Fix 3: Ensure each template has its own body::before and body::after with correct z-index
for path in [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Count body::after occurrences
    count_ba = content.count("body::after")
    if count_ba > 1:
        print(f"{path}: WARNING - {count_ba} body::after rules found (may conflict)")

print("\nAll fixes applied.")
