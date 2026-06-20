# -*- coding: utf-8 -*-
"""Fix CSS braces mismatches and hardcoded colors across all templates."""
import os, re
os.chdir(r"D:\Jarvis project")

templates = [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/memory/timeline.html",
]

for path in templates:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    changes = []
    
    # ===== FIX 1: CSS brace balancing =====
    # Find all CSS blocks (between <style> and </style>)
    pattern = re.compile(r'(<style>)(.*?)(</style>)', re.DOTALL)
    
    def balance_css(match):
        open_tag = match.group(1)
        css = match.group(2)
        close_tag = match.group(3)
        
        opens = css.count('{')
        closes = css.count('}')
        
        if opens > closes:
            # Add missing closing braces at the end
            css = css.rstrip() + '\n' + ('}' * (opens - closes))
            changes.append(f"CSS braces: +{opens - closes}")
        elif closes > opens:
            # Too many closing braces - warn but don't remove (might be inside strings)
            pass
        
        return open_tag + css + close_tag
    
    content = pattern.sub(balance_css, content)
    
    # ===== FIX 2: Replace hardcoded colors with CSS variables =====
    # emerald-500 -> var(--color-success) or similar
    # blue-500 -> var(--jarvis-blue)
    
    # text-blue-400 -> use inline style or class
    replacements = {
        # Text colors
        'text-emerald-400': 'text-[var(--color-success)]',
        'text-emerald-500': 'text-[var(--color-success)]',
        'text-cyan-400': 'text-[var(--jarvis-cyan)]',
        'text-blue-400': 'text-[var(--jarvis-blue)]',
        'text-[var(--color-success)]': 'text-[var(--color-success)]',  # prevent double
        # Background colors  
        'bg-emerald-500': 'bg-[var(--color-success)]',
        'bg-purple-300': 'bg-[var(--jarvis-purple)]',
        'bg-cyan-400': 'bg-[var(--jarvis-cyan)]',
        # Border colors
        'border-emerald-500': 'border-[var(--color-success)]',
        'border-cyan-400': 'border-[var(--jarvis-cyan)]',
        # Ring colors
        'ring-emerald-500': 'ring-[var(--color-success)]',
    }
    
    for old, new in replacements.items():
        if old != new and old in content:
            content = content.replace(old, new)
            changes.append(f"color: {old} -> var()")
    
    # Replace inline style colors like color: #22C55E etc.
    # Replace the CSS variable references if they don't exist
    if '--color-success' not in content:
        # Add after :root
        content = content.replace(
            '--text-secondary: #9191A8;',
            '--text-secondary: #9191A8;\n            --color-success: #22C55E;\n            --jarvis-blue: #4F8CFF;\n            --jarvis-cyan: #06B6D4;\n            --jarvis-purple: #8B5CF6;'
        )
        changes.append("added CSS color variables")
    
    # ===== FIX 3: Ensure theme script uses var keyword not const =====
    # Replace 'const switcher' with 'var switcher' and add null checks
    if 'const switcher = document.getElementById("themeSwitcher")' in content:
        content = content.replace(
            'const switcher = document.getElementById("themeSwitcher");',
            'var switcher = document.getElementById("themeSwitcher");'
        )
        changes.append("const -> var in theme JS")
    
    # Add if(switcher) guard if missing
    if 'var switcher' in content and 'if (switcher)' not in content:
        content = content.replace(
            'var switcher = document.getElementById("themeSwitcher");\n        switcher.addEventListener(',
            'var switcher = document.getElementById("themeSwitcher");\n        if (switcher) {\n            switcher.addEventListener('
        )
        # Add closing brace before next section
        content = content.replace(
            'localStorage.getItem("jarvis-theme");\n        if (saved)',
            'localStorage.getItem("jarvis-theme");\n            if (saved)'
        )
        changes.append("added if(switcher) null guard")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  {path}: {' | '.join(changes) if changes else 'no changes'}")

print("\nAll fixes applied.")
