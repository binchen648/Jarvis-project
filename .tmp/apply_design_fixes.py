# -*- coding: utf-8 -*-
import os, re
os.chdir(r"D:\Jarvis project")

templates = [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]

for filepath in templates:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    changes = []
    
    # ===== FIX 1: Gray text contrast =====
    # Replace low-contrast text colors
    # text-white/40 -> use a proper hex color
    content = content.replace('text-white/40', 'text-[#A0A0B8]')
    content = content.replace('text-white/30', 'text-[#808098]')
    content = content.replace('text-white/20', 'text-[#686880]')
    content = content.replace('text-[#9191A8]', 'text-[#A0A0B8]')
    content = content.replace('text-[#5C5C72]', 'text-[#808098]')
    content = content.replace('color: var(--text-tertiary);', 'color: #A0A0B8;')
    content = content.replace('color: var(--text-secondary);', 'color: #C0C0D0;')
    
    # Fix white/50 and white/60 too
    content = content.replace('text-white/50', 'text-[#B0B0C8]')
    content = content.replace('text-white/60', 'text-[#C8C8D8]')
    
    changes.append("Gray text contrast fixed")
    
    # ===== FIX 2: prefers-reduced-motion =====
    # Add reduced motion styles before </style>
    reduced_motion_css = """
        /* prefers-reduced-motion */
        @media (prefers-reduced-motion: reduce) {
            body::before, body::after { animation: none !important; }
            .glass-card { transition: none !important; }
            .glass-card:hover { transform: none !important; }
            .animate-pulse, .animate-ping, .animate-spin { animation: none !important; }
            .jarvis-core-sphere { animation: none !important; }
            [class*="hover:scale-"]:hover { transform: none !important; }
            [class*="hover:translate"]:hover { transform: none !important; }
            .transition, .transition-all, .transition-colors { transition: none !important; }
            .group-hover\\:translate-x-1 { transform: none !important; }
        }"""
    
    style_end = content.find("</style>")
    if style_end >= 0:
        content = content[:style_end] + reduced_motion_css + content[style_end:]
        changes.append("prefers-reduced-motion added")
    
    # ===== FIX 3: Font pairing =====
    # Add Google Fonts link in head
    google_fonts = '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">'
    head_end = content.find("</head>")
    if head_end >= 0:
        # Insert after Bootstrap Icons CDN
        bi_cdn = content.rfind("bootstrap-icons", 0, head_end)
        if bi_cdn >= 0:
            insert_pos = content.find(">", bi_cdn) + 1
            content = content[:insert_pos] + "\n    " + google_fonts + content[insert_pos:]
            changes.append("Google Fonts (Space Grotesk) added")
    
    # Replace Inter with Space Grotesk for headings
    # We'll add font-family to body and h1-h6
    body_tag = content.find("<body")
    if body_tag >= 0:
        # Check if font-family is already customized
        if 'font-family' not in content[body_tag:body_tag+200]:
            # Add style for heading fonts
            font_style = '\n    <style>h1,h2,h3,h4{font-family:"Space Grotesk",Inter,system-ui,sans-serif}h1{font-weight:700}h2{font-weight:600}h3{font-weight:600}</style>\n    '
            content = content[:body_tag] + font_style + content[body_tag:]
            changes.append("Heading font set to Space Grotesk")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"  {filepath}: {' | '.join(changes)}")

print("\nDone! All 3 fixes applied.")
