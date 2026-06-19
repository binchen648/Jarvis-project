# -*- coding: utf-8 -*-
import os, re
os.chdir(r"D:\Jarvis project")

with open("ai_studio_code(1).html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace sidebar links
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/5 text-white"><i class="bi bi-grid-fill" style="color: var(--secondary)"></i> Dashboard</a>',
    '<a href="/" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/5 text-white"><i class="bi bi-grid-fill" style="color: var(--secondary)"></i> Dashboard</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-stars"></i> Agent</a>',
    '<a href="/chat/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-stars"></i> Agent</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>',
    '<a href="/memory/timeline/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>')
content = content.replace('<a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>',
    '<a href="/goals/" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>')

# User name
content = content.replace("Alex", "{{ user.username|default:'Alex' }}")

# Date
content = content.replace("JUN 16, 2026", "{{ today|date:'M d, Y'|upper }}")

# Welcome + AI suggestion
content = content.replace(
    '<h1 class="text-4xl font-bold tracking-tight">Good Morning, Alex.</h1>\n                            <p class="text-sm text-[#9191A8] mt-2 italic">Jarvis \u5efa\u8bae\uff1a18:30 \u5f00\u59cb\u5b66\u4e60\uff0c\u4eca\u65e5\u7cbe\u529b\u9ad8\u5cf0</p>',
    '<h1 class="text-4xl font-bold tracking-tight greeting-morning hidden">Good Morning, {{ user.username }}.</h1>\n                            <h1 class="text-4xl font-bold tracking-tight greeting-afternoon hidden">Good Afternoon, {{ user.username }}.</h1>\n                            <h1 class="text-4xl font-bold tracking-tight greeting-evening hidden">Good Evening, {{ user.username }}.</h1>\n                            {% if top_goal %}\n                            <p class="text-sm text-[#9191A8] mt-2 italic">Jarvis \u5efa\u8bae\uff1a{{ ai_suggestion }}</p>\n                            {% else %}\n                            <p class="text-sm text-[#9191A8] mt-2 italic">\u4eca\u5929\u8fd8\u6ca1\u6709\u76ee\u6807\uff0c\u53bb\u521b\u5efa\u4e00\u4e2a\u5427 \U0001F3AF</p>\n                            {% endif %}'
)

# KPI values
content = content.replace('>82% <span class="text-[10px] text-emerald-400 ml-1 font-normal">\u25b2 5%</span>',
    '>{{ focus_pct }}% <span class="text-[10px] text-emerald-400 ml-1 font-normal">\u25b2 5%</span>')
content = content.replace('>3 <span class="text-sm font-normal text-emerald-400">\u6b63\u5e38</span>',
    '>{{ goal_health_normal }} <span class="text-sm font-normal text-emerald-400">\u6b63\u5e38</span>')
content = content.replace('>+12 <span class="text-[10px] text-[#9191A8] ml-1 font-normal">\u6761</span>',
    '>+{{ memory_growth_weekly }} <span class="text-[10px] text-[#9191A8] ml-1 font-normal">\u6761</span>')
content = content.replace('>87%</p>',
    '>{{ ai_confidence_pct }}%</p>')

# Today's Plan
content = content.replace(
    '<div class="flex justify-between items-center ml-2">\n                            <h3 class="text-lg font-semibold">Today\'s Plan</h3>\n                            <span class="text-xs text-[#9191A8]">2/3 tasks completed</span>\n                        </div>',
    '<div class="flex justify-between items-center ml-2">\n                            <h3 class="text-lg font-semibold">Today\'s Plan</h3>\n                            {% if today_plan_items %}\n                            <span class="text-xs text-[#9191A8]">{{ today_plan_items|length }}/{{ today_plan_items|length }} tasks</span>\n                            {% endif %}\n                        </div>'
)

# Replace plan items with Django loop
plan_start = '<div class="glass-card rounded-[2.5rem] overflow-hidden">'
plan_end = '</div>\n                        </div>'
plan_pattern_start = content.find(plan_start)
plan_section_start = content.find('<div class="p-8 flex items-center justify-between group hover:bg-white/[0.02] transition cursor-pointer', plan_pattern_start)
plan_section_end = content.find(plan_end, plan_section_start)

if plan_pattern_start >= 0 and plan_section_start >= 0:
    # Keep the glass-card div open, replace inner content
    before_card = content[:plan_section_start]
    after_card = content[plan_section_end + len(plan_end):]
    
    django_plan = """{% if today_plan_items %}
                                {% for item in today_plan_items %}
                                <a href="{{ item.link }}"
                                   class="p-8 flex items-center justify-between group {% if not forloop.last %}border-b border-white/5{% endif %} no-underline text-[inherit] transition hover:bg-white/[0.02] cursor-pointer">
                                    <div class="flex items-center gap-6">
                                        {% if item.done %}
                                        <div class="w-12 h-12 rounded-2xl bg-[var(--primary)] flex items-center justify-center text-white shadow-lg">
                                            <i class="bi bi-check-lg text-xl"></i>
                                        </div>
                                        {% else %}
                                        <div class="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-[var(--primary)] transition text-[var(--primary)] font-bold">{{ item.id }}</div>
                                        {% endif %}
                                        <div>
                                            <p class="font-bold {% if item.done %}line-through text-[#9191A8]{% else %}text-white{% endif %}">{{ item.title }}</p>
                                            <p class="text-xs text-[#9191A8] mt-0.5">{{ item.desc }} &middot; {{ item.minutes }}min</p>
                                        </div>
                                    </div>
                                    {% if not item.done %}
                                    <i class="bi bi-chevron-right text-white/20 group-hover:text-[var(--primary)] transition"></i>
                                    {% endif %}
                                </a>
                                {% endfor %}
                            {% else %}
                                <div class="text-center py-10 text-[#9191A8]">
                                    <div class="text-3xl mb-3 opacity-40">\U0001F916</div>
                                    <p class="text-sm">Jarvis \u6b63\u5728\u5206\u6790\u4f60\u7684\u76ee\u6807\uff0c\u7a0d\u540e\u4e3a\u4f60\u751f\u6210\u8ba1\u5212</p>
                                </div>
                            {% endif %}"""
    
    content = content[:plan_section_start] + django_plan + after_card

# Goal Progress
content = content.replace(
    '<div class="glass-card p-8 rounded-[2.5rem]">\n                            <h3 class="text-sm font-semibold mb-6">Goal Progress</h3>\n                            <div class="space-y-6">\n                                <div>\n                                    <div class="flex justify-between text-xs mb-2">\n                                        <span class="text-[#9191A8]">\u7cfb\u7edf\u8bbe\u8ba1</span>\n                                        <span>70%</span>\n                                    </div>\n                                    <div class="h-1 w-full bg-white/5 rounded-full">\n                                        <div class="h-full bg-[var(--primary)] rounded-full transition-all duration-1000" style="width: 70%"></div>\n                                    </div>\n                                </div>\n                                <div>\n                                    <div class="flex justify-between text-xs mb-2">\n                                        <span class="text-[#9191A8]">LeetCode 150</span>\n                                        <span>90%</span>\n                                    </div>\n                                    <div class="h-1 w-full bg-white/5 rounded-full">\n                                        <div class="h-full bg-[var(--secondary)] rounded-full transition-all duration-1000 shadow-[0_0_10px_var(--secondary)]" style="width: 90%"></div>\n                                    </div>\n                                </div>\n                            </div>\n                        </div>',
    '<div class="glass-card p-8 rounded-[2.5rem]">\n                            <h3 class="text-sm font-semibold mb-6">Goal Progress</h3>\n                            {% if goal_progress_list %}\n                            <div class="space-y-6">\n                                {% for item in goal_progress_list %}\n                                <div>\n                                    <div class="flex justify-between text-xs mb-2">\n                                        <span class="text-[#9191A8]">{{ item.title }}</span>\n                                        <span class="text-white">{{ item.pct }}%</span>\n                                    </div>\n                                    <div class="h-1 w-full bg-white/5 rounded-full">\n                                        <div class="h-full rounded-full transition-all duration-1000" style="width: {{ item.pct }}%; background: {% if item.pct < 30 %}var(--color-error){% else %}var(--primary){% endif %};"></div>\n                                    </div>\n                                </div>\n                                {% endfor %}\n                            </div>\n                            {% else %}\n                            <div class="text-center py-6 text-[#9191A8]">\n                                <div class="text-2xl mb-2 opacity-40">\U0001F4CA</div>\n                                <p class="text-xs">\u8fd8\u6ca1\u6709\u76ee\u6807\u8fdb\u5ea6\u6570\u636e</p>\n                            </div>\n                            {% endif %}\n                        </div>'
)

# Memory Timeline
mem_start = '<div class="glass-card p-8 rounded-[2.5rem] relative overflow-hidden group">'
mem_end = '</div>\n                    </div>\n                </section>'
mem_section_start = content.find(mem_start)
if mem_section_start >= 0:
    mem_inner_start = content.find('<h3 class="text-sm font-semibold mb-4">Memory Timeline</h3>', mem_section_start)
    mem_inner_end = content.find(mem_end, mem_inner_start)
    
    new_memory = """<div class="flex items-center justify-between mb-4">
                                <h3 class="text-sm font-semibold">Memory Timeline</h3>
                                <a href="/memory/timeline/" class="text-[10px] text-[var(--accent)] hover:underline">\u67e5\u770b\u5168\u90e8 \u2192</a>
                            </div>
                            {% if memory_recent_items %}
                            <div class="space-y-4 border-l border-white/10 ml-2 pl-4">
                                {% for item in memory_recent_items %}
                                <a href="/memory/timeline/" class="block relative no-underline text-[inherit] group/mem">
                                    <div class="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[var(--accent)]"></div>
                                    <p class="text-xs">{{ item.title }}</p>
                                    <p class="text-[10px] text-[#9191A8] mt-px">{{ item.description|truncatechars:60 }}</p>
                                </a>
                                {% endfor %}
                            </div>
                            {% else %}
                            <div class="space-y-4 border-l border-white/10 ml-2 pl-4">
                                <div class="relative">
                                    <div class="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-white/10"></div>
                                    <p class="text-xs text-[#9191A8]">\u8fd8\u6ca1\u6709\u8bb0\u5fc6\u8f68\u8ff9</p>
                                    <p class="text-[10px] text-[#5C5C72]">\u5f00\u59cb\u5b66\u4e60\u540e\uff0cJarvis \u4f1a\u8bb0\u5f55\u4f60\u7684\u6210\u957f\u8f68\u8ff9</p>
                                </div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </section>"""
    
    content = content[:mem_section_start] + mem_start + new_memory + content[mem_inner_end + len(mem_end):]

# Add greeting script before closing </body>
content = content.replace('</body>',
    '<script>\n        (function() {\n            var hour = new Date().getHours();\n            var el;\n            if (hour >= 6 && hour < 12) { el = document.querySelector(\'.greeting-morning\'); }\n            else if (hour >= 12 && hour < 18) { el = document.querySelector(\'.greeting-afternoon\'); }\n            else { el = document.querySelector(\'.greeting-evening\'); }\n            if (el) el.classList.remove(\'hidden\');\n        })();\n    </script>\n</body>')

with open("templates/dashboard/home.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Written OK")
print("File size:", len(content))
