# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

DASH_BB = 'body::before {\n            content: ""; position: fixed; top: -30%; left: -30%; width: 160%; height: 160%; pointer-events: none;\n            background: radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 35%, transparent), transparent 30%),\n                        radial-gradient(circle at 80% 25%, color-mix(in srgb, var(--secondary) 20%, transparent), transparent 35%),\n                        radial-gradient(circle at 60% 80%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 40%);\n            filter: blur(120px); animation: aurora-drift 35s ease-in-out infinite; z-index: -3;\n        }'

DASH_BA = 'body::after {\n            content: ""; position: fixed; inset: 0; pointer-events: none;\n            background: radial-gradient(circle at 70% 60%, color-mix(in srgb, var(--primary) 20%, transparent), transparent 30%),\n                        radial-gradient(circle at 30% 70%, color-mix(in srgb, var(--secondary) 10%, transparent), transparent 35%);\n            filter: blur(150px); animation: aurora-reverse 60s ease-in-out infinite; z-index: -2;\n        }'

for path in [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    changes = []

    # Fix: Remove broken noise overlay inserted inside aurora-reverse
    if "/* Noise texture overlay */" in content:
        lines = content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if "/* Noise texture overlay */" in line:
                skip = True
                continue
            if skip and "body::after" in line and "content:" in line:
                continue
            if skip and "background-image: url" in line:
                continue
            if skip and "background-repeat:" in line:
                continue
            if skip and ("z-index: -1" in line or "opacity: 0.5" in line):
                skip = False
                continue
            if skip:
                continue
            new_lines.append(line)
        content = "\n".join(new_lines)
        changes.append("removed broken noise overlay")

    # Fix aurora-reverse if broken
    if "@keyframes aurora-reverse" in content:
        idx = content.index("@keyframes aurora-reverse")
        end_idx = content.index("}", idx)
        block = content[idx:end_idx+1]
        if "50%" not in block:
            new_block = "@keyframes aurora-reverse {\n            0%,100% { transform: translate(0,0) scale(1); }\n            50% { transform: translate(6%,5%) scale(1.2); }\n        }"
            content = content.replace(block, new_block)
            changes.append("fixed broken aurora-reverse keyframes")

    # Unify body::before to Dashboard spec
    if path != "templates/dashboard/home.html":
        # Find existing body::before
        bb_markers = ["body::before {\n            content:", "body::before {\n            content:"]
        bb_start = content.find("body::before {")
        if bb_start >= 0:
            bb_end = content.find("}", bb_start)
            old_bb = content[bb_start:bb_end+1]
            if "35%, transparent" not in old_bb:
                content = content.replace(old_bb, DASH_BB)
                changes.append("body::before unified to Dashboard spec")

        # Find existing body::after (Aurora, not noise)
        ba_start = content.find("body::after {")
        if ba_start >= 0:
            ba_end = content.find("}", ba_start)
            old_ba = content[ba_start:ba_end+1]
            if "20%, transparent" not in old_ba:
                content = content.replace(old_ba, DASH_BA)
                changes.append("body::after unified to Dashboard spec")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  {path}: {' | '.join(changes) if changes else 'already unified'}")

print("\nAll fixed.")
