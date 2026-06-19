# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

# The new sidebar HTML to inject (replaces the old nav section in each template)
new_sidebar_nav = """        <nav class="flex-1 px-4 space-y-2">
            <a href="/" class="flex items-center gap-3 px-4 py-3 rounded-2xl DASHBOARD_CLASS"><i class="bi bi-grid-fill" DASHBOARD_COLOR></i> Dashboard</a>
            <a href="/chat/" class="flex items-center gap-3 px-4 py-3 rounded-2xl AGENT_CLASS"><i class="bi bi-stars" AGENT_COLOR></i> Agent</a>
            <a href="/memory/timeline/" class="flex items-center gap-3 px-4 py-3 rounded-2xl MEMORY_CLASS"><i class="bi bi-brain" MEMORY_COLOR></i> Memory</a>
            <a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl GOALS_CLASS"><i class="bi bi-target" GOALS_COLOR></i> Goals</a>
            <a href="/wellness/suggestions/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-heart"></i> Wellness</a>
        </nav>
        <div class="h-px bg-white/5 mx-4 my-2"></div>
        <nav class="px-4 space-y-2">
            <a href="/content/feed/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-book"></i> Content</a>
            <a href="/trajectory/skills/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-diagram-3"></i> Trajectory</a>
        </nav>
        <div class="h-px bg-white/5 mx-4 my-2"></div>
        <nav class="px-4 space-y-2">
            <a href="/profile/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-gear"></i> Settings</a>
        </nav>"""

# Dashboard sidebar (active=Dashboard)
dashboard_nav = new_sidebar_nav.replace("DASHBOARD_CLASS", "bg-white/5 text-white").replace("DASHBOARD_COLOR", 'style="color: var(--secondary)"')
dashboard_nav = dashboard_nav.replace("AGENT_CLASS", "text-white/50 hover:bg-white/5 transition").replace("AGENT_COLOR", "")
dashboard_nav = dashboard_nav.replace("MEMORY_CLASS", "text-white/50 hover:bg-white/5 transition").replace("MEMORY_COLOR", "")
dashboard_nav = dashboard_nav.replace("GOALS_CLASS", "text-white/50 hover:bg-white/5 transition").replace("GOALS_COLOR", "")

# Memory sidebar (active=Memory)
memory_nav = new_sidebar_nav.replace("DASHBOARD_CLASS", "text-white/50 hover:bg-white/5 transition").replace("DASHBOARD_COLOR", "")
memory_nav = memory_nav.replace("AGENT_CLASS", "text-white/50 hover:bg-white/5 transition").replace("AGENT_COLOR", "")
memory_nav = memory_nav.replace("MEMORY_CLASS", "bg-white/10 text-white").replace("MEMORY_COLOR", 'style="color: var(--primary)"')
memory_nav = memory_nav.replace("GOALS_CLASS", "text-white/50 hover:bg-white/5 transition").replace("GOALS_COLOR", "")

# Agent sidebar (active=Agent)
agent_nav = new_sidebar_nav.replace("DASHBOARD_CLASS", "text-white/50 hover:bg-white/5 transition").replace("DASHBOARD_COLOR", "")
agent_nav = agent_nav.replace("AGENT_CLASS", "bg-white/10 text-white shadow-lg").replace("AGENT_COLOR", 'style="color: var(--primary)"')
agent_nav = agent_nav.replace("MEMORY_CLASS", "text-white/50 hover:bg-white/5 transition").replace("MEMORY_COLOR", "")
agent_nav = agent_nav.replace("GOALS_CLASS", "text-white/50 hover:bg-white/5 transition").replace("GOALS_COLOR", "")

# Process each template
files = [
    ("templates/dashboard/home.html", '<nav class="flex-1 px-4 space-y-2">', dashboard_nav),
    ("templates/memory/timeline.html", '<nav class="flex-1 px-4 space-y-2">', memory_nav),
    ("templates/chat/conversation_detail.html", '<nav class="flex-1 px-4 space-y-2">', agent_nav),
]

for filepath, marker, replacement in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the nav section - from first <nav to closing </nav>
    nav_start = content.find(marker)
    if nav_start < 0:
        print(f"WARNING: {filepath} - marker not found")
        continue
    
    # Find the end of this nav section - the </nav> after marker
    nav_end = content.find("</nav>", nav_start)
    if nav_end < 0:
        print(f"WARNING: {filepath} - nav end not found")
        continue
    
    # Find the NEXT </nav> (there are two navs: primary nav + user area nav)
    nav_end2 = content.find("</nav>", nav_end + 6)
    if nav_end2 >= 0 and nav_end2 - nav_end < 100:
        # Close together - this might be the user nav, find the real one
        pass
    
    # Actually, let me find all </nav> occurrences and use a smarter approach
    # The sidebar structure is: <nav>...</nav> then user area
    # I need to replace everything from first <nav> to the closing </nav> before the user area
    
    # Find user area (p-6 or similar) to know where nav section ends
    user_markers = ['<div class="p-6">', '<div class="p-6 border-t']
    user_pos = -1
    for um in user_markers:
        p = content.find(um, nav_start)
        if p >= 0:
            user_pos = p
            break
    
    # Find the last </nav> before user area
    last_nav_end = content.rfind("</nav>", nav_start, user_pos if user_pos > 0 else len(content))
    if last_nav_end < 0:
        print(f"WARNING: {filepath} - last nav end not found")
        continue
    
    old_nav_section = content[nav_start:last_nav_end + 7]
    new_content = content.replace(old_nav_section, replacement)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"OK: {filepath} ({len(old_nav_section)} -> {len(replacement)})")

print("Done")
