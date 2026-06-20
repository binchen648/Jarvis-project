# -*- coding: utf-8 -*-
"""Unify all 3 templates to eliminate 25 structural discrepancies."""
import os, re
os.chdir(r"D:\Jarvis project")

def fix_file(path, fixes):
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    applied = []
    for desc, old, new in fixes:
        if old in c:
            c = c.replace(old, new)
            applied.append(desc)
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    return applied

# ============================================================
# FIX 1: conversation_detail.html (Agent chat page)
# ============================================================
agent_fixes = [
    # Body CSS: add missing margin, height, position
    ("body margin+height+pos",
     "body {\n            background: var(--surface-bg);\n            color: var(--text-main);\n            font-family: Inter, system-ui, sans-serif;\n            overflow: hidden;\n            position: relative;",
     "body {\n            background: var(--surface-bg);\n            color: var(--text-main);\n            font-family: Inter, system-ui, sans-serif;\n            overflow: hidden;\n            margin: 0;\n            height: 100vh;\n            position: relative;"),
    # Body class: add overflow-hidden
    ('body class overflow-hidden',
     '<body class="flex h-screen">',
     '<body class="flex h-screen overflow-hidden">'),
    # Sidebar z-index: unify to z-10
    ('sidebar z-20 -> z-10',
     'class="w-64 bg-black/20 backdrop-blur-3xl border-r border-white/5 flex flex-col z-20"',
     'class="w-64 bg-black/20 backdrop-blur-3xl border-r border-white/5 flex flex-col z-10"'),
]
a = fix_file("templates/chat/conversation_detail.html", agent_fixes)
print("Agent chat:", ", ".join(a) if a else "no changes")

# ============================================================
# FIX 2: dashboard/home.html 
# ============================================================
dash_fixes = [
    # Theme script null guard
    ('theme null guard',
     'const switcher = document.getElementById("themeSwitcher");\n        switcher.addEventListener("change",',
     'var switcher = document.getElementById("themeSwitcher");\n        if (switcher) {\n            switcher.addEventListener("change",'),
    # Close the if block
    ('theme null guard close',
     'localStorage.setItem("jarvis-theme", theme); });\n        const saved = localStorage.getItem("jarvis-theme");',
     'localStorage.setItem("jarvis-theme", theme); });\n            var saved = null;\n            try { saved = localStorage.getItem("jarvis-theme"); } catch(e3) {}\n            if (saved) { document.documentElement.setAttribute("data-theme", saved); switcher.value = saved; }\n        }'),
    # Remove duplicate code after the guard
    ('remove duplicate localstorage code',
     '\n            var saved = null;\n            try { saved = localStorage.getItem("jarvis-theme"); } catch(e3) {}\n            if (saved) { document.documentElement.setAttribute("data-theme", saved); switcher.value = saved; }\n        }\n\n        var saved = null;',
     ''),
    # Active nav bg unify to bg-white/10
    ('active nav bg-white/5 -> bg-white/10',
     'class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/5 text-white"><i class="bi bi-grid-fill" style="color: var(--secondary)"></i> Dashboard',
     'class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/10 text-white"><i class="bi bi-grid-fill" style="color: var(--secondary)"></i> Dashboard'),
    # Sidebar backdrop unify to blur-3xl
    ('sidebar backdrop blur-2xl -> blur-3xl',
     'backdrop-blur-2xl',
     'backdrop-blur-3xl'),
]
d = fix_file("templates/dashboard/home.html", dash_fixes)
print("Dashboard:", ", ".join(d) if d else "no changes")

# ============================================================
# FIX 3: memory/timeline.html
# ============================================================
with open("templates/memory/timeline.html", "r", encoding="utf-8") as f:
    mc = f.read()

mem_applied = []

# Add system-ui to font-family
if "font-family: Inter, sans-serif" in mc:
    mc = mc.replace("font-family: Inter, sans-serif", "font-family: Inter, system-ui, sans-serif")
    mem_applied.append("font-family system-ui")

# Add overflow-hidden to body class
if 'class="flex"' in mc[:200]:
    mc = mc.replace('<body class="flex">', '<body class="flex h-screen overflow-hidden">')
    mem_applied.append("body class h-screen+overflow-hidden")

# Add z-index to sidebar
if 'backdrop-blur-3xl border-r border-white/5 flex flex-col">' in mc:
    mc = mc.replace('backdrop-blur-3xl border-r border-white/5 flex flex-col">', 'backdrop-blur-3xl border-r border-white/5 flex flex-col z-10">')
    mem_applied.append("sidebar z-index z-10")

# Add user profile section before closing </aside>
old_aside_close = '</nav>    </aside>'
new_aside_close = '</nav>        </nav>        <div class="p-6 border-t border-white/5 flex items-center gap-3">\n            <div class="w-8 h-8 rounded-full bg-zinc-800 border border-white/10"></div>\n            <span class="text-xs text-[#C8C8D8] font-medium">{{ user.username|default:"Alex" }} OS</span>\n        </div>\n    </aside>'
if old_aside_close in mc:
    mc = mc.replace(old_aside_close, new_aside_close)
    mem_applied.append("user profile section")

# Add AI Surface FAB before closing </body>
old_body_close = '</body>'
fab_html = '\n    <div class="fixed bottom-8 right-8 z-50">\n        <div class="w-14 h-14 bg-[var(--primary)] rounded-full flex items-center justify-center text-white shadow-[0_0_20px_rgba(139,92,246,0.4)] cursor-pointer hover:scale-110 transition relative">\n            <div class="absolute inset-0 rounded-full bg-[var(--primary)] animate-ping opacity-20"></div>\n            <i class="bi bi-stars text-xl"></i>\n        </div>\n    </div>\n</body>'
if 'AI Surface' not in mc:
    mc = mc.replace(old_body_close, fab_html)
    mem_applied.append("AI Surface FAB")

# Add focus-ring to theme select
mc = mc.replace(
    'class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-[10px] text-white outline-none cursor-pointer"',
    'class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-[10px] text-white outline-none focus:ring-1 focus:ring-white/20 transition cursor-pointer"'
)
mem_applied.append("theme select focus-ring")

# Fix the aurora-reverse keyframe (50% was nested inside 0%,100%)
if "0%,100% { transform: translate(0,0) scale(1);  50% { transform: translate(6%,5%) scale(1.2); } }" in mc:
    mc = mc.replace(
        "0%,100% { transform: translate(0,0) scale(1);  50% { transform: translate(6%,5%) scale(1.2); } }",
        "0%,100% { transform: translate(0,0) scale(1); }\n            50% { transform: translate(6%,5%) scale(1.2); }"
    )
    mem_applied.append("aurora-reverse 50% keyframe fix")

with open("templates/memory/timeline.html", "w", encoding="utf-8") as f:
    f.write(mc)
print("Memory:", ", ".join(mem_applied) if mem_applied else "no changes")

print("\nAll fixes applied.")
