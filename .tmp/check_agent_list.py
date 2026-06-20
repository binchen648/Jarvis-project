import os
os.chdir(r"D:\Jarvis project")
with open("templates/chat/conversation_list.html", "r", encoding="utf-8") as f:
    c = f.read()

print("body::before gradients:", c.count("radial-gradient", 0, c.find("body::after")))
print("Has 35%:", "35%" in c[:c.find("body::after")])
print("body::after aurora:", "70% 60%" in c[c.find("body::after"):c.find("body::after")+300])
print("theme JS:", "addEventListener" in c and "themeSwitcher" in c)
print("glass header:", "backdrop-filter" in c[:600])
