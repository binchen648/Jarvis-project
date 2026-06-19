# -*- coding: utf-8 -*-
import os
os.chdir(r"D:\Jarvis project")

with open("templates/dashboard/home.html", "r", encoding="utf-8") as f:
    old = f.read()

# Replace the entire file
new = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="jarvis">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <title>Jarvis OS - Dashboard</title>
</head>
<body>
<p>placeholder</p>
</body>
</html>"""

with open("templates/dashboard/home.html", "w", encoding="utf-8") as f:
    f.write(new)
print("OK")
