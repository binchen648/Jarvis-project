# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

with open("agent_major.html", "r", encoding="utf-8") as f:
    content = f.read()

# Sidebar links
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-grid-fill"></i> Dashboard</a>',
    '<a href="/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-grid-fill"></i> Dashboard</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/10 text-white shadow-lg"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>',
    '<a href="/chat/" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/10 text-white shadow-lg"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-brain"></i> Memory</a>',
    '<a href="/memory/timeline/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5"><i class="bi bi-target"></i> Goals</a>',
    '<a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>')

# Add full sidebar (Wellness, Content, Trajectory, Settings)
old_nav_end = '<a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>'
new_nav_full = old_nav_end + """
            <a href="/wellness/suggestions/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-heart"></i> Wellness</a>
        </nav>
        <div class="h-px bg-white/5 mx-4 my-2"></div>
        <nav class="px-4 space-y-2">
            <a href="/content/feed/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-book"></i> Content</a>
            <a href="/trajectory/skills/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-diagram-3"></i> Trajectory</a>
        </nav>
        <div class="h-px bg-white/5 mx-4 my-2"></div>
        <nav class="px-4 space-y-2">
            <a href="/profile/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/40 hover:bg-white/5 transition"><i class="bi bi-gear"></i> Settings</a>
        </nav>"""
content = content.replace(old_nav_end, new_nav_full)

# Replace header search with Django form
content = content.replace('<i class="bi bi-search absolute left-3 top-2.5 text-white/20 text-xs"></i>\n                    <input type="text" placeholder="搜索对话..." class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48">',
    '<form method="get" action="/chat/" class="relative">\n                    <i class="bi bi-search absolute left-3 top-2.5 text-white/20 text-xs"></i>\n                    <input type="text" name="q" placeholder="搜索对话..." class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48">\n                    </form>')

# New conversation button link
content = content.replace('<button class="bg-[var(--primary)] text-white text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2">\n                    <i class="bi bi-plus-lg"></i> 新建对话',
    '<a href="/chat/new/" class="bg-[var(--primary)] text-white text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2">\n                    <i class="bi bi-plus-lg"></i> 新建对话')

# Replace stat counts
content = content.replace('3 \u603b\u8ba1\u5bf9\u8bdd', '{{ conversations|length }} \u603b\u8ba1\u5bf9\u8bdd')
content = content.replace('12 \u5de5\u5177\u8c03\u7528', '{{ total_tool_calls|default:"0" }} \u5de5\u5177\u8c03\u7528')

# Replace conversation cards with Django loop
card_start = '<!-- \u5361\u7247 1 (\u6700\u65b0/\u6d3b\u8dc3) -->'
card_marker = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
card_section_start = content.find(card_marker)
if card_section_start >= 0:
    # Find end of card section — the closing </div> of the grid
    after_grid = content.find('</div>', card_section_start)
    after_grid2 = content.find('</div>', after_grid + 6)  # second closing div
    
    django_cards = """<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% if conversations %}
                {% for conv in conversations %}
                <a href="/chat/{{ conv.pk }}/" class="glass-card p-6 rounded-[2rem] relative group cursor-pointer no-underline text-[inherit] block {% if forloop.first %}border-t-2 border-t-[var(--primary)]{% endif %}">
                    <div class="flex justify-between items-start mb-6">
                        <div class="w-10 h-10 rounded-2xl {% if forloop.first %}bg-[var(--primary)]/10 text-[var(--primary)]{% else %}bg-white/5 text-white/40{% endif %} flex items-center justify-center">
                            <i class="bi {% if forloop.first %}bi-chat-dots-fill{% else %}bi-chat-left-text{% endif %} text-xl"></i>
                        </div>
                        <span class="text-[10px] {% if forloop.first %}text-[var(--primary)] font-bold{% else %}text-white/20 font-bold{% endif %}">{{ conv.updated_at|timesince }}</span>
                    </div>
                    <h3 class="text-white font-bold text-lg mb-2 truncate">{{ conv.title }}</h3>
                    <p class="text-xs text-white/40 line-clamp-2 leading-relaxed mb-6">
                        {{ conv.ai_summary|default:"AI \u6458\u8981: \u5c1a\u672a\u751f\u6210\u3002\u70b9\u51fb\u7ee7\u7eed\u5bf9\u8bdd\u4ee5\u8ba9 Jarvis \u603b\u7ed3\u4e0a\u4e0b\u6587\u3002" }}
                    </p>
                    <div class="flex justify-between items-center pt-4 border-t border-white/5">
                        <div class="flex gap-3 text-[10px] text-white/20 font-mono">
                            <span>{{ conv.updated_at|date:"m/d H:i" }}</span>
                            <span>{{ conv.msg_count }} \u6d88\u606f</span>
                        </div>
                        <i class="bi bi-arrow-right-short text-xl text-white/20 group-hover:text-white group-hover:translate-x-1 transition"></i>
                    </div>
                </a>
                {% endfor %}
            {% else %}
                <div class="col-span-3 text-center py-16">
                    <div class="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-5 glass-card mx-auto">
                        <i class="bi bi-chat-dots text-3xl" style="color: var(--primary);"></i>
                    </div>
                    <p class="text-white/70 font-medium mb-1">\u8fd8\u6ca1\u6709\u5bf9\u8bdd\u8bb0\u5f55</p>
                    <p class="text-xs text-white/30">\u70b9\u51fb\u4e0a\u65b9\u201c\u65b0\u5efa\u5bf9\u8bdd\u201d\u5f00\u59cb\u7b2c\u4e00\u6b21\u4ea4\u8c08</p>
                </div>
            {% endif %}
            </div>"""
    
    content = content[:card_section_start] + django_cards + content[after_grid2 + 6:]

# Add theme switcher + forest/rose + custom-scrollbar
theme_add = """        [data-theme="forest"] { --primary: #22C55E; --secondary: #14B8A6; --accent: #84CC16; }
        [data-theme="rose"] { --primary: #EC4899; --secondary: #8B5CF6; --accent: #F472B6; }"""
content = content.replace('[data-theme="sunset"] { --primary: #F97316; --secondary: #EC4899; --accent: #FACC15; }',
    '[data-theme="sunset"] { --primary: #F97316; --secondary: #EC4899; --accent: #FACC15; }\n' + theme_add)

# Add custom-scrollbar
content = content.replace('.no-scrollbar::-webkit-scrollbar { display: none; }',
    '.no-scrollbar::-webkit-scrollbar { display: none; }\n        .custom-scrollbar::-webkit-scrollbar { width: 5px; }\n        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }')

# Add theme switcher to header
header_right = '<div class="flex items-center gap-4">'
header_new = """<div class="flex items-center gap-4">
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
                <div class="h-4 w-px bg-white/10"></div>"""
content = content.replace(header_right, header_new)

# Add theme switcher JS before closing </body>
content = content.replace('</body>',
    """<script>
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

print("Written OK, size:", len(content))
