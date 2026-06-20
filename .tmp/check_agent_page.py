import os
os.chdir(r"D:\Jarvis project")
with open("templates/chat/conversation_list.html", "r", encoding="utf-8") as f:
    c = f.read()

opens = c.count("<script>")
closes = c.count("</script>")
print(f"script tags: {opens} open, {closes} close")

if opens != closes:
    print("ISSUE: mismatched script tags!")

# Check for common issues
if "<script><script>" in c:
    print("ISSUE: nested script tags!")
if "</script></script>" in c:
    print("ISSUE: double script close!")
if "const switcher" in c:
    print("Theme JS: uses const")
if "applyTheme" in c:
    print("Theme JS: has applyTheme()")
if "DOMContentLoaded" in c:
    print("Theme JS: has DOMContentLoaded")
