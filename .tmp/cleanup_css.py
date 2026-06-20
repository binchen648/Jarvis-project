import os
os.chdir(r"D:\Jarvis project")

for path in [
    "templates/dashboard/home.html",
    "templates/chat/conversation_detail.html",
    "templates/chat/conversation_list.html",
    "templates/memory/timeline.html",
]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix 1: Remove cruft after aurora-reverse keyframe closing brace
    # Pattern: "} 50% { ... } }" followed by orphaned "}"
    import re
    content = re.sub(r'\}\s*50%\s*\{[^}]*\}\s*\}', '', content)
    # Fix 2: Remove orphaned single }
    content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)

    # Fix 3: Remove duplicate .glass-card definitions (keep only first)
    lines = content.split('\n')
    new_lines = []
    glass_card_count = 0
    in_glass_card = False
    glass_card_brace_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped == '.glass-card {':
            glass_card_count += 1
            if glass_card_count > 1:
                # Skip this duplicate block
                in_glass_card = True
                glass_card_brace_count = 0
                continue
        if in_glass_card:
            glass_card_brace_count += stripped.count('{') - stripped.count('}')
            if glass_card_brace_count <= 0:
                in_glass_card = False
            continue
        new_lines.append(line)

    content = '\n'.join(new_lines)

    # Fix 4: Ensure .glass-card:hover exists (may have been removed)
    if '.glass-card:hover' not in content:
        content = content.replace(
            '.glass-card {\n            background:',
            '.glass-card {\n            background:'
        )
        # Add after the glass-card block
        idx = content.find('.glass-card {')
        if idx >= 0:
            end_idx = content.find('}', idx) + 1
            hover_block = '\n        .glass-card:hover {\n            transform: translateY(-3px);\n            border-color: color-mix(in srgb, var(--primary) 50%, rgba(255,255,255,.08));\n            box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary) 20%, transparent), 0 20px 50px color-mix(in srgb, var(--primary) 10%, transparent);\n        }'
            content = content[:end_idx] + hover_block + content[end_idx:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed: {path}")

print("\nAll templates cleaned up.")
