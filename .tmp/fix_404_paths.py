import os
os.chdir(r"D:\Jarvis project")

# Fix 1: /goals/new/ -> /goals/create/
with open("templates/goals/goal_list.html", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace('/goals/new/', '/goals/create/')
with open("templates/goals/goal_list.html", "w", encoding="utf-8") as f:
    f.write(c)
print("Fixed goal_list.html")

# Fix 2: /goals/session/ -> /goals/session/log/
with open("templates/goals/goal_detail.html", "r", encoding="utf-8") as f:
    c = f.read()
count = c.count('/goals/session/')
if count:
    c = c.replace('/goals/session/', '/goals/session/log/')
    with open("templates/goals/goal_detail.html", "w", encoding="utf-8") as f:
        f.write(c)
    print(f"Fixed goal_detail.html ({count} occurrences)")
else:
    print("goal_detail.html: no /goals/session/ found")
