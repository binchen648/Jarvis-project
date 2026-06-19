# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

with open("agent_major.html", "r", encoding="utf-8") as f:
    content = f.read()

# ============================================================
# 1. Sidebar links (# -> real Django paths)
# ============================================================
content = content.replace(
    '<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-grid-fill"></i> Dashboard</a>',
    '<a href="/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-grid-fill"></i> Dashboard</a>')
content = content.replace(
    '<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/10 text-white shadow-lg"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>',
    '<a href="/chat/" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/10 text-white shadow-lg"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>')
content = content.replace(
    '<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-brain"></i> Memory</a>',
    '<a href="/memory/timeline/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>')
content = content.replace(
    '<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-target"></i> Goals</a>',
    '<a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>')

# ============================================================
# 2. Add Wellness + divider + Content + Trajectory + divider + Settings
# ============================================================
goals_link = '<a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>'
full_nav = goals_link + '\n            <a href="/wellness/suggestions/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-heart"></i> Wellness</a>\n        </nav>\n        <div class="h-px bg-white/5 mx-4 my-2"></div>\n        <nav class="px-4 space-y-2">\n            <a href="/content/feed/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-book"></i> Content</a>\n            <a href="/trajectory/skills/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-diagram-3"></i> Trajectory</a>\n        </nav>\n        <div class="h-px bg-white/5 mx-4 my-2"></div>\n        <nav class="px-4 space-y-2">\n            <a href="/profile/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-gear"></i> Settings</a>'
content = content.replace(goals_link, full_nav)

# ============================================================
# 3. Header: search form + new conversation link
# ============================================================
old_search = '<i class="bi bi-search absolute left-3 top-2.5 text-white/20 text-xs"></i>\n                    <input type="text" placeholder="\u641c\u7d22\u5bf9\u8bdd..." class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48">'
new_search = '<form method="get" action="/chat/" class="relative m-0 p-0">\n                    <i class="bi bi-search absolute left-3 top-2.5 text-white/20 text-xs"></i>\n                    <input type="text" name="q" placeholder="\u641c\u7d22\u5bf9\u8bdd..." value="{{ query }}" class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48">\n                    </form>'
content = content.replace(old_search, new_search)

# New conversation button (replace button with link)
old_btn = '<button class="bg-[var(--primary)] text-white text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2">\n                    <i class="bi bi-plus-lg"></i> \u65b0\u5efa\u5bf9\u8bdd\n                </button>'
new_btn = '<a href="/chat/new/" class="bg-[var(--primary)] text-white text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2">\n                    <i class="bi bi-plus-lg"></i> \u65b0\u5efa\u5bf9\u8bdd\n                </a>'
content = content.replace(old_btn, new_btn)

# ============================================================
# 4. Stats bar with Django variables
# ============================================================
content = content.replace(
    '<span class="w-1.5 h-1.5 rounded-full bg-[var(--primary)]"></span> 3 总计对话',
    '<span class="w-1.5 h-1.5 rounded-full bg-[var(--primary)]"></span> {{ conversations|length }} 总计对话')
content = content.replace(
    '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> 12 工具调用',
    '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> {{ total_tool_calls|default:"0" }} 工具调用')

# ============================================================
# 5. Conversation cards grid -> Django loop
# ============================================================
grid_start = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
grid_end = '</div>\n        </div>\n\n        <!-- 悬浮 AI Core (右下角) -->'

# Find the grid section
start_idx = content.find(grid_start)
end_idx = content.find(grid_end, start_idx)
if start_idx >= 0 and end_idx >= 0:
    old_grid = content[start_idx:end_idx + len(grid_end)]
    new_grid = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">\n                {% if conversations %}\n                {% for conv in conversations %}\n                <a href="/chat/{{ conv.pk }}/" class="glass-card p-6 rounded-[2rem] relative group cursor-pointer no-underline text-[inherit] block{% if forloop.first %} border-t-2 border-t-[var(--primary)]{% endif %}">\n                    <div class="flex justify-between items-start mb-6">\n                        <div class="w-10 h-10 rounded-2xl flex items-center justify-center{% if forloop.first %} bg-[var(--primary)]/10 text-[var(--primary)]{% else %} bg-white/5 text-white/40{% endif %}">\n                            <i class="bi {% if forloop.first %}bi-chat-dots-fill{% else %}bi-chat-left-text{% endif %} text-xl"></i>\n                        </div>\n                        <span class="text-[10px]{% if forloop.first %} text-[var(--primary)] font-bold{% else %} text-white/20 font-bold{% endif %}">{{ conv.updated_at|timesince }}</span>\n                    </div>\n                    <h3 class="text-white font-bold text-lg mb-2 truncate">{{ conv.title }}</h3>\n                    <p class="text-xs text-white/40 line-clamp-2 leading-relaxed mb-6">\n                        {% if conv.ai_summary %}{{ conv.ai_summary }}{% else %}AI 摘要: 尚未生成。点击继续对话以让 Jarvis 总结上下文。{% endif %}\n                    </p>\n                    <div class="flex justify-between items-center pt-4 border-t border-white/5">\n                        <div class="flex gap-3 text-[10px] text-white/20 font-mono">\n                            <span>{{ conv.updated_at|date:"m/d H:i" }}</span>\n                            <span>{{ conv.msg_count }} 消息</span>\n                        </div>\n                        <i class="bi bi-arrow-right-short text-xl text-white/20 group-hover:text-white group-hover:translate-x-1 transition"></i>\n                    </div>\n                </a>\n                {% endfor %}\n                {% else %}\n                <div class="col-span-3 text-center py-16">\n                    <div class="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-5 glass-card mx-auto">\n                        <i class="bi bi-chat-dots text-3xl" style="color: var(--primary);"></i>\n                    </div>\n                    <p class="text-white/70 font-medium mb-1">还没有对话记录</p>\n                    <p class="text-xs text-white/30">点击上方"新建对话"开始第一次交谈</p>\n                </div>\n                {% endif %}\n            </div>\n        </div>\n\n        <!-- 悬浮 AI Core (右下角) -->'
    content = content.replace(old_grid, new_grid)

# ============================================================
# 6. Aurora background: full unified (body::before + body::after)
# ============================================================
old_aurora = """        /* Aurora 背景 */
        body::before {
            content: ""; position: fixed; inset: -30%; pointer-events: none;
            background: radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 15%, transparent), transparent 30%),
                        radial-gradient(circle at 80% 80%, color-mix(in srgb, var(--secondary) 10%, transparent), transparent 40%);
            filter: blur(120px); z-index: -1; animation: drift 30s infinite alternate;
        }
        @keyframes drift { from { transform: translate(0,0); } to { transform: translate(5%, 5%); } }"""

new_aurora = """        /* Aurora 背景 */
        body::before {
            content: ""; position: fixed; top: -30%; left: -30%; width: 160%; height: 160%; pointer-events: none;
            background: radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 25%, transparent), transparent 30%),
                        radial-gradient(circle at 80% 25%, color-mix(in srgb, var(--secondary) 20%, transparent), transparent 35%),
                        radial-gradient(circle at 60% 80%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 40%);
            filter: blur(120px); animation: aurora-drift 35s ease-in-out infinite; z-index: -3;
        }
        body::after {
            content: ""; position: fixed; inset: 0; pointer-events: none;
            background: radial-gradient(circle at 70% 60%, color-mix(in srgb, var(--primary) 12%, transparent), transparent 30%),
                        radial-gradient(circle at 30% 70%, color-mix(in srgb, var(--secondary) 10%, transparent), transparent 35%);
            filter: blur(150px); animation: aurora-reverse 60s ease-in-out infinite; z-index: -2;
        }
        @keyframes aurora-drift { 0%,100% { transform: translate(0,0) scale(1); } 25% { transform: translate(-5%,4%) scale(1.08); } 50% { transform: translate(5%,-5%) scale(1.15); } 75% { transform: translate(-3%,-4%) scale(1.08); } }
        @keyframes aurora-reverse { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(6%,5%) scale(1.2); } }"""

content = content.replace(old_aurora, new_aurora)

# ============================================================
# 7. Add forest + rose themes
# ============================================================
if "[data-theme=\"forest\"]" not in content:
    content = content.replace(
        '[data-theme="sunset"] { --primary: #F97316; --secondary: #EC4899; --accent: #FACC15; }',
        '[data-theme="sunset"] { --primary: #F97316; --secondary: #EC4899; --accent: #FACC15; }\n        [data-theme="forest"] { --primary: #22C55E; --secondary: #14B8A6; --accent: #84CC16; }\n        [data-theme="rose"] { --primary: #EC4899; --secondary: #8B5CF6; --accent: #F472B6; }')

# ============================================================
# 8. Glass-card: unify hover
# ============================================================
old_glass_hover = """.glass-card:hover { 
            transform: translateY(-4px); 
            border-color: color-mix(in srgb, var(--primary) 40%, transparent);
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }"""
new_glass_hover = """.glass-card:hover {
            transform: translateY(-2px);
            border-color: color-mix(in srgb, var(--primary) 40%, rgba(255,255,255,.05));
            box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary) 15%, transparent), 0 15px 40px color-mix(in srgb, var(--primary) 8%, transparent);
        }"""
content = content.replace(old_glass_hover, new_glass_hover)

# ============================================================
# 9. Add glass-card box-shadow base (match Dashboard)
# ============================================================
old_glass_base = """.glass-card {
            background: linear-gradient(135deg, rgba(255,255,255,.05), rgba(255,255,255,.015));
            backdrop-filter: blur(18px); border: 1px solid rgba(255,255,255,.06); transition: .3s;
        }"""
new_glass_base = """.glass-card {
            background: linear-gradient(135deg, rgba(255,255,255,.05), rgba(255,255,255,.015));
            backdrop-filter: blur(18px); border: 1px solid rgba(255,255,255,.06);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 10px 30px rgba(0,0,0,.25);
            transition: all .3s ease;
        }"""
content = content.replace(old_glass_base, new_glass_base)

# ============================================================
# 10. Theme switcher in header + JS
# ============================================================
# Add theme switcher before the search bar
old_header_right = """<div class="flex items-center gap-4">
                <div class="relative">"""
new_header_right = """<div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                    <i class="bi bi-palette2 text-xs text-white/40"></i>
                    <select id="themeSwitcher" class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-[10px] text-white outline-none cursor-pointer">
                        <option value="jarvis" class="bg-[#08080D]">Jarvis</option>
                        <option value="ocean" class="bg-[#08080D]">Ocean</option>
                        <option value="sunset" class="bg-[#08080D]">Sunset</option>
                        <option value="forest" class="bg-[#08080D]">Forest</option>
                        <option value="rose" class="bg-[#08080D]">Rose</option>
                    </select>
                </div>
                <div class="h-4 w-px bg-white/10"></div>
                <div class="relative">"""
content = content.replace(old_header_right, new_header_right)

# Add theme switcher JS before </body>
if "themeSwitcher" not in content:
    content = content.replace('</body>',
        """    <script>
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
    </script>
</body>""")

with open("templates/chat/conversation_list.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Done, size:", len(content))
