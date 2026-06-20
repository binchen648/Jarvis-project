# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

# The unified theme JS to inject/replace in each template
THEME_JS = '''
    <script>
        var switcher = document.getElementById('themeSwitcher');
        function applyTheme(t) {
            document.documentElement.setAttribute('data-theme', t);
            try { localStorage.setItem('jarvis-theme', t); } catch(e) {}
        }
        if (switcher) {
            switcher.addEventListener('change', function(e) { applyTheme(e.target.value); });
            window.addEventListener('DOMContentLoaded', function() {
                var saved = localStorage.getItem('jarvis-theme') || 'jarvis';
                applyTheme(saved);
                switcher.value = saved;
            });
        }
    </script>
'''

for path, marker in [
    ("templates/dashboard/home.html", "<!-- JS"),
    ("templates/memory/timeline.html", "<script>"),
    ("templates/chat/conversation_detail.html", "// Theme Switcher"),
]:
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    
    # Find old theme JS block and replace it
    # Strategy: find the theme swither-related JS and replace with unified version
    if path == "templates/dashboard/home.html":
        # Dashboard has theme JS at line ~386
        old_start = c.find("var switcher = document.getElementById")
        if old_start >= 0:
            old_end = c.find("}", old_start)
            old_end2 = c.find("}", old_end + 1)
            # Find the closing of if(switcher) block - third }
            old_end3 = c.find("}", old_end2 + 1)
            old_theme_block = c[old_start:old_end3+1]
            c = c.replace(old_theme_block, THEME_JS.strip())
    
    elif path == "templates/memory/timeline.html":
        # Memory has theme JS in the last script block
        old_start = c.find("var switcher = document.getElementById")
        if old_start >= 0:
            old_end = c.find("</script>", old_start)
            old_theme_block = c[old_start:old_end]
            c = c.replace(old_theme_block, THEME_JS.strip())
    
    elif path == "templates/chat/conversation_detail.html":
        # Agent detail has theme JS before mode switcher  
        old_start = c.find("var switcher = document.getElementById")
        if old_start >= 0:
            old_end = c.find("Mode Switcher", old_start)
            old_theme_block = c[old_start:old_end-4]  # -4 for newlines
            # Find the exact text to replace
            theme_end = c.find("}", old_start)
            theme_end2 = c.find("}", theme_end + 1)
            # Get text from var switcher to closing brace of if(switcher)
            if_saved_start = c.find("if (saved)", old_start)
            if_saved_end = c.find("}", if_saved_start) + 1
            text_to_replace = c[old_start:if_saved_end+1]
            # Also need to close the outer if(switcher)
            c = c.replace(text_to_replace, THEME_JS.strip())
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    
    print(f"  {path}: theme JS updated")

print("\nAll theme scripts unified.")
