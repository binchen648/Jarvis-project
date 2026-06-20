# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

with open("agent.html", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Sidebar href
c = c.replace('href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-grid-fill"></i> Dashboard</a>',
    'href="/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-grid-fill"></i> Dashboard</a>')
c = c.replace('href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl nav-active"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>',
    'href="/chat/" class="flex items-center gap-3 px-4 py-3 rounded-2xl nav-active"><i class="bi bi-stars" style="color: var(--primary)"></i> Agent</a>')
c = c.replace('href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>',
    'href="/memory/timeline/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>')
c = c.replace('href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>',
    'href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>')

# 2. Full sidebar (Wellness, Content, Trajectory, Settings, user profile)
c = c.replace('href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>\n            <a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-heart"></i> Wellness</a>',
    'href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>\n            <a href="/wellness/suggestions/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-heart"></i> Wellness</a>\n        </nav>\n        <div class="h-px bg-white/5 mx-4 my-2"></div>\n        <nav class="px-4 space-y-2">\n            <a href="/content/feed/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-book"></i> Content</a>\n            <a href="/trajectory/skills/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-diagram-3"></i> Trajectory</a>\n        </nav>\n        <div class="h-px bg-white/5 mx-4 my-2"></div>\n        <nav class="px-4 space-y-2">\n            <a href="/profile/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-[#9191A8] hover:bg-white/5 transition"><i class="bi bi-gear"></i> Settings</a>')

# 3. User profile in sidebar
c = c.replace('<div class="p-6">\n             <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-[var(--primary)] to-[var(--secondary)] animate-pulse shadow-[0_0_15px_var(--primary)]"></div>\n        </div>',
    '<div class="p-6 border-t border-white/5 flex items-center gap-3">\n            <div class="w-8 h-8 rounded-full bg-zinc-800 border border-white/10"></div>\n            <span class="text-xs text-[#C8C8D8] font-medium">{{ user.username|default:"Alex" }} OS</span>\n        </div>')

# 4. Stats bar
c = c.replace('3 总计对话', '{{ conversations|length }} 总计对话')
c = c.replace('12 工具调用', '{{ total_tool_calls|default:"0" }} 工具调用')

# 5. Search input -> form
c = c.replace('<input type="text" placeholder="搜索对话..." class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48 text-white">',
    '<form method="get" action="/chat/" class="relative inline-block">\n                            <i class="bi bi-search absolute left-3 top-2.5 text-[#5C5C72] text-xs"></i>\n                            <input type="text" name="q" placeholder="搜索对话..." value="{{ query }}" class="bg-white/5 border border-white/10 rounded-lg px-8 py-2 text-xs focus:outline-none focus:border-[var(--primary)] transition w-48 text-white">\n                        </form>')

# Remove the old search icon that's now inside the form
c = c.replace('<i class="bi bi-search absolute left-3 top-2.5 text-[#5C5C72] text-xs"></i>\n                        <form', '<form')

# 6. New conversation button -> link
c = c.replace('<button class="text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2" style="background: var(--primary); color: white;">\n                    <i class="bi bi-plus-lg"></i> 新建对话\n                </button>',
    '<a href="/chat/new/" class="text-xs px-4 py-2 rounded-lg font-bold shadow-lg hover:scale-105 transition flex items-center gap-2" style="background: var(--primary); color: white;">\n                    <i class="bi bi-plus-lg"></i> 新建对话\n                </a>')

# 7. Replace static cards with Django template loop
card_start = '<!-- 对话卡片 1 -->'
card_end = '            </div>\n        </div>\n\n        <!-- 悬浮 AI Core -->'
start_idx = c.find(card_start)
end_idx = c.find(card_end, start_idx)

if start_idx >= 0 and end_idx >= 0:
    django_cards = """{% if conversations %}
                {% for conv in conversations %}
                <a href="/chat/{{ conv.pk }}/" class="glass-card p-6 rounded-[2.5rem] group cursor-pointer no-underline text-[inherit] block"{% if forloop.first %} style="border-top: 2px solid var(--primary)"{% endif %}>
                    <div class="flex justify-between items-start mb-6">
                        <div class="w-10 h-10 rounded-2xl flex items-center justify-center"{% if forloop.first %} style="background: color-mix(in srgb, var(--primary) 15%, transparent); color: var(--primary)"{% else %} style="background: rgba(255,255,255,0.05); color: #5C5C72"{% endif %}>
                            <i class="bi {% if forloop.first %}bi-chat-dots-fill{% else %}bi-chat-left-text{% endif %} text-xl"></i>
                        </div>
                        <span class="text-[10px] font-bold"{% if forloop.first %} style="color: var(--primary)"{% else %} style="color: #5C5C72"{% endif %}>{{ conv.updated_at|timesince }}</span>
                    </div>
                    <h3 class="text-white font-bold text-lg mb-2 truncate">{{ conv.title }}</h3>
                    <p class="text-xs text-[#9191A8] line-clamp-2 leading-relaxed mb-6">
                        {% if conv.ai_summary %}{{ conv.ai_summary }}{% else %}AI 摘要: 尚未生成。点击继续对话以让 Jarvis 总结上下文。{% endif %}
                    </p>
                    <div class="flex justify-between items-center pt-4 border-t border-white/5 text-[10px] text-[#5C5C72]">
                        <span>{{ conv.updated_at|date:"m/d H:i" }}</span>
                        <span>{{ conv.msg_count }} 消息</span>
                    </div>
                </a>
                {% endfor %}
                {% else %}
                <div class="col-span-3 text-center py-16">
                    <div class="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-5 glass-card mx-auto">
                        <i class="bi bi-chat-dots text-3xl" style="color: var(--primary);"></i>
                    </div>
                    <p class="text-[#C8C8D8] font-medium mb-1">还没有对话记录</p>
                    <p class="text-xs text-[#808098]">点击上方"新建对话"开始第一次交谈</p>
                </div>
                {% endif %}"""
    
    before = c[:start_idx]
    after = c[end_idx + len(card_end):]
    c = before + django_cards + after

with open("templates/chat/conversation_list.html", "w", encoding="utf-8") as f:
    f.write(c)

print("Done!")
