# -*- coding: utf-8 -*-
"""Visible design improvements - changes that are immediately noticeable."""
import os
os.chdir(r"D:\Jarvis project")

templates = [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
]

# Read all templates
content_map = {}
for path in [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]:
    with open(path, "r", encoding="utf-8") as f:
        content_map[path] = f.read()

# =============================================================
# CHANGE 1: Add noise texture overlay + enhanced Aurora gradient
# =============================================================
aurora_enhance = """
        /* Noise texture overlay */
        body::after {
            content: ""; position: fixed; inset: 0; pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
            background-repeat: repeat; background-size: 256px 256px;
            z-index: -1; opacity: 0.5;
        }"""

# =============================================================
# CHANGE 2: More saturated Aurora colors
# =============================================================
old_aurora_before = """color-mix(in srgb, var(--primary) 25%, transparent)"""
new_aurora_before = """color-mix(in srgb, var(--primary) 35%, transparent)"""
old_aurora_after = """color-mix(in srgb, var(--primary) 12%, transparent)"""
new_aurora_after = """color-mix(in srgb, var(--primary) 20%, transparent)"""

# =============================================================
# CHANGE 3: Add accent left border to sidebar active item
# =============================================================
sidebar_active_style = """
        /* Active sidebar accent */
        .nav-item.active, a.bg-white\\/10, a.bg-white\\/5.text-white {
            position: relative;
        }
        .nav-item.active::before, a.bg-white\\/10::before, a.bg-white\\/5.text-white::before {
            content: '';
            position: absolute;
            left: -16px;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 20px;
            background: var(--primary, #8B5CF6);
            border-radius: 0 3px 3px 0;
            box-shadow: 0 0 8px color-mix(in srgb, var(--primary, #8B5CF6) 50%, transparent);
        }"""

# =============================================================
# CHANGE 4: Header title enhancement with gradient text
# =============================================================
header_title_style = """
        /* Gradient title in header */
        .header-gradient-title {
            background: linear-gradient(135deg, var(--primary, #8B5CF6), var(--secondary, #4F8CFF));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }"""

# Apply changes to each template
for path, content in content_map.items():
    file_changes = []
    name = os.path.basename(path)

    # Add noise texture after existing body::before/::after rules
    # Find the end of the Aurora CSS section (last keyframe)
    aurora_end = content.find("@keyframes aurora-reverse")
    if aurora_end >= 0:
        # Find the closing brace of aurora-reverse
        brace_end = content.find("}", aurora_end)
        if brace_end >= 0:
            insert_pos = content.find("\n", brace_end) + 1
            content = content[:insert_pos] + aurora_enhance + content[insert_pos:]
            file_changes.append("noise texture overlay")

    # Saturate Aurora colors
    if old_aurora_before in content:
        content = content.replace(old_aurora_before, new_aurora_before)
        file_changes.append("aurora saturation +10%")
    if old_aurora_after in content:
        content = content.replace(old_aurora_after, new_aurora_after)

    # Add sidebar active accent
    style_end = content.find("</style>")
    if style_end >= 0:
        # Check if already added
        if "nav-item.active::before" not in content:
            content = content[:style_end] + sidebar_active_style + content[style_end:]
            file_changes.append("sidebar active accent bar")

    # Add header gradient title support
    if "header-gradient-title" not in content:
        style_end = content.find("</style>")
        if style_end >= 0:
            content = content[:style_end] + header_title_style + content[style_end:]
            file_changes.append("gradient title support")

    # Apply header-title class to header h2 elements
    # Look for the page title in header
    if name == "timeline.html":
        content = content.replace(
            '<h2 class="text-sm font-bold uppercase tracking-widest text-[#A0A0B8]">Memory Timeline</h2>',
            '<h2 class="text-sm font-bold uppercase tracking-widest header-gradient-title">Memory Timeline</h2>'
        )
        file_changes.append("gradient Memory Timeline title")
    elif name == "home.html":
        content = content.replace(
            '<h2 class="text-xs font-medium uppercase tracking-widest text-[#A0A0B8]">System Status</h2>',
            '<h2 class="text-xs font-medium uppercase tracking-widest text-[#A0A0B8]">System Status</h2>'
        )
        # Add gradient to the "Good Morning" greeting
        content = content.replace(
            'class="text-4xl font-bold tracking-tight greeting-morning hidden">Good Morning,',
            'class="text-4xl font-bold tracking-tight greeting-morning hidden header-gradient-title">Good Morning,'
        )
        content = content.replace(
            'class="text-4xl font-bold tracking-tight greeting-afternoon hidden">Good Afternoon,',
            'class="text-4xl font-bold tracking-tight greeting-afternoon hidden header-gradient-title">Good Afternoon,'
        )
        content = content.replace(
            'class="text-4xl font-bold tracking-tight greeting-evening hidden">Good Evening,',
            'class="text-4xl font-bold tracking-tight greeting-evening hidden header-gradient-title">Good Evening,'
        )
        file_changes.append("gradient greeting text")

    content_map[path] = content
    print(f"  {path}: {' | '.join(file_changes)}")

# Write back
for path, content in content_map.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("\nDone! Visible changes applied.")
