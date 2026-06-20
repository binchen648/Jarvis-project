import os
os.chdir(r"D:\Jarvis project")

# Shared CSS/JS components for auth pages (no user profile since not logged in)
STYLE = '''<style>
:root{--surface-bg:#08080D;--surface-card:rgba(20,20,30,0.65);--primary:#8B5CF6;--secondary:#4F8CFF;--accent:#06B6D4;--text-main:#F1F1F6;--text-secondary:#9191A8}
[data-theme="ocean"]{--primary:#2563EB;--secondary:#06B6D4;--accent:#67E8F9}
[data-theme="sunset"]{--primary:#F97316;--secondary:#EC4899;--accent:#FACC15}
[data-theme="forest"]{--primary:#22C55E;--secondary:#14B8A6;--accent:#84CC16}
[data-theme="rose"]{--primary:#EC4899;--secondary:#8B5CF6;--accent:#F472B6}
body{background:var(--surface-bg);color:var(--text-main);font-family:"Inter",sans-serif;margin:0;overflow:hidden}
body::before{content:"";position:fixed;top:-30%;left:-30%;width:160%;height:160%;pointer-events:none;background:radial-gradient(circle at 20%20%,color-mix(in srgb,var(--primary)30%,transparent),transparent 35%),radial-gradient(circle at 80%25%,color-mix(in srgb,var(--secondary)20%,transparent),transparent 35%),radial-gradient(circle at 60%80%,color-mix(in srgb,var(--accent)15%,transparent),transparent 40%);filter:blur(120px);animation:aurora-drift 30s ease-in-out infinite;z-index:-3}
@keyframes aurora-drift{0%,100%{transform:translate(0,0)scale(1)}50%{transform:translate(5%,-5%)scale(1.1)}}
.glass-card{background:linear-gradient(135deg,rgba(255,255,255,.05),rgba(255,255,255,.015));backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.06);transition:all .3s ease}
.glass-card:hover{transform:translateY(-4px);border-color:color-mix(in srgb,var(--primary)40%,transparent);box-shadow:0 0 25px color-mix(in srgb,var(--primary)10%,transparent)}
h1,h2,h3,h4{font-family:"Space Grotesk",sans-serif}.no-scrollbar::-webkit-scrollbar{display:none}
input,select{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:10px 14px;color:white;font-size:14px;outline:none;width:100%;box-sizing:border-box}
input:focus,select:focus{border-color:var(--primary)}
label{display:block;font-size:12px;margin-bottom:6px;color:#9191A8;font-weight:500}
.btn-primary{background:var(--primary);color:white;text-align:center;padding:12px 20px;border-radius:12px;font-weight:700;font-size:13px;border:none;cursor:pointer;width:100%}
.btn-primary:hover{transform:scale(1.03)}</style>'''

HEAD = '''<!DOCTYPE html>
<html lang="zh-CN" data-theme="jarvis">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
'''

THEME_JS = '''<script>
var switcher=document.getElementById("themeSwitcher");
function applyTheme(t){document.documentElement.setAttribute("data-theme",t);localStorage.setItem("jarvis-theme",t)}
if(switcher){switcher.addEventListener("change",function(e){applyTheme(e.target.value)});window.addEventListener("DOMContentLoaded",function(){var saved=localStorage.getItem("jarvis-theme")||"jarvis";applyTheme(saved);switcher.value=saved})}
</script>
</body></html>'''

def write_auth_page(filename, title, content_body):
    html = HEAD + f'<title>{title}</title>\n' + STYLE + '</head>\n<body class="flex h-screen">\n'
    html += '<div class="flex-1 flex items-center justify-center relative overflow-hidden">\n'
    html += '<div class="max-w-md w-full px-6 z-10">\n'
    html += '<div class="text-center mb-8"><h1 class="text-3xl font-bold italic tracking-tighter" style="color:var(--primary);">JARVIS</h1><p class="text-xs mt-2" style="color:#9191A8;">Personal AI Operating System</p></div>\n'
    html += content_body
    html += '</div></div>\n'
    html += '<div class="absolute bottom-8 right-8 z-50"><div class="w-14 h-14 rounded-full flex items-center justify-center text-white cursor-pointer hover:scale-110 transition shadow-2xl relative" style="background:var(--primary)"><div class="absolute inset-0 rounded-full animate-ping opacity-20" style="background:var(--primary)"></div><i class="bi bi-stars text-xl"></i></div></div>\n'
    # Theme switcher for auth pages
    html += '<div class="absolute top-6 right-6 z-50"><div class="flex items-center gap-2"><i class="bi bi-palette2 text-xs text-[#9191A8]"></i><select id="themeSwitcher" class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-[10px] text-white outline-none cursor-pointer focus:border-[var(--primary)] transition"><option value="jarvis">Jarvis</option><option value="ocean">Ocean</option><option value="sunset">Sunset</option><option value="forest">Forest</option><option value="rose">Rose</option></select></div></div>\n'
    html += THEME_JS
    
    with open(f"templates/{filename}", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written: templates/{filename}")

# Login page
login_body = '''<div class="glass-card p-8 rounded-[2.5rem]">
<h2 class="text-xl font-bold mb-6 text-center">登录</h2>
{% if form.non_field_errors %}<div class="p-3 rounded-xl mb-4 text-xs" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#EF4444;">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
<form method="post" action="{% url 'account_login' %}">{% csrf_token %}
{% for field in form %}<div class="mb-4"><label for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% if field.errors %}<p class="text-xs mt-1" style="color:#EF4444;">{% for e in field.errors %}{{ e }}{% endfor %}</p>{% endif %}</div>{% endfor %}
<button type="submit" class="btn-primary mt-4">登录</button>
</form>
<p class="text-xs text-center mt-6" style="color:#9191A8;">还没有账号？<a href="{% url 'account_signup' %}" style="color:var(--primary);">注册</a></p>
<p class="text-xs text-center mt-2" style="color:#9191A8;"><a href="{% url 'account_reset_password' %}" style="color:var(--primary);">忘记密码？</a></p>
</div>'''
write_auth_page("account/login.html", "登录 - Jarvis", login_body)

# Signup page
signup_body = '''<div class="glass-card p-8 rounded-[2.5rem]">
<h2 class="text-xl font-bold mb-6 text-center">注册</h2>
{% if form.non_field_errors %}<div class="p-3 rounded-xl mb-4 text-xs" style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:#EF4444;">{% for e in form.non_field_errors %}{{ e }}{% endfor %}</div>{% endif %}
<form method="post" action="{% url 'account_signup' %}">{% csrf_token %}
{% for field in form %}<div class="mb-4"><label for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% if field.errors %}<p class="text-xs mt-1" style="color:#EF4444;">{% for e in field.errors %}{{ e }}{% endfor %}</p>{% endif %}</div>{% endfor %}
<button type="submit" class="btn-primary mt-4">注册</button>
</form>
<p class="text-xs text-center mt-6" style="color:#9191A8;">已有账号？<a href="{% url 'account_login' %}" style="color:var(--primary);">登录</a></p>
</div>'''
write_auth_page("account/signup.html", "注册 - Jarvis", signup_body)

# Logout page
logout_body = '''<div class="glass-card p-8 rounded-[2.5rem] text-center">
<h2 class="text-xl font-bold mb-4">退出登录</h2>
<p class="text-sm mb-6" style="color:#9191A8;">确定要退出登录吗？</p>
<form method="post" action="{% url 'account_logout' %}">{% csrf_token %}
<button type="submit" class="btn-primary mt-2">确认退出</button>
</form>
<p class="text-xs text-center mt-6" style="color:#9191A8;"><a href="/" style="color:var(--primary);">返回首页</a></p>
</div>'''
write_auth_page("account/logout.html", "退出 - Jarvis", logout_body)

# Password reset
pr_body = '''<div class="glass-card p-8 rounded-[2.5rem]">
<h2 class="text-xl font-bold mb-6 text-center">重置密码</h2>
<p class="text-sm mb-6 text-center" style="color:#9191A8;">输入注册邮箱，我们会发送重置链接。</p>
<form method="post" action="{% url 'account_reset_password' %}">{% csrf_token %}
{% for field in form %}<div class="mb-4"><label for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% if field.errors %}<p class="text-xs mt-1" style="color:#EF4444;">{% for e in field.errors %}{{ e }}{% endfor %}</p>{% endif %}</div>{% endfor %}
<button type="submit" class="btn-primary mt-4">发送重置邮件</button>
</form>
<p class="text-xs text-center mt-6" style="color:#9191A8;"><a href="{% url 'account_login' %}" style="color:var(--primary);">返回登录</a></p>
</div>'''
write_auth_page("account/password_reset.html", "重置密码 - Jarvis", pr_body)

# Password reset done
pr_done_body = '''<div class="glass-card p-8 rounded-[2.5rem] text-center">
<h2 class="text-xl font-bold mb-4">邮件已发送</h2>
<p class="text-sm" style="color:#9191A8;">如果该邮箱已注册，你将收到一封密码重置邮件。</p>
<p class="text-xs mt-6" style="color:#9191A8;"><a href="{% url 'account_login' %}" style="color:var(--primary);">返回登录</a></p>
</div>'''
write_auth_page("account/password_reset_done.html", "邮件已发送 - Jarvis", pr_done_body)

# Password reset from key
pr_key_body = '''<div class="glass-card p-8 rounded-[2.5rem]">
<h2 class="text-xl font-bold mb-6 text-center">设置新密码</h2>
<form method="post" action="">{% csrf_token %}
{% for field in form %}<div class="mb-4"><label for="{{ field.id_for_label }}">{{ field.label }}</label>{{ field }}{% if field.errors %}<p class="text-xs mt-1" style="color:#EF4444;">{% for e in field.errors %}{{ e }}{% endfor %}</p>{% endif %}</div>{% endfor %}
<button type="submit" class="btn-primary mt-4">重置密码</button>
</form></div>'''
write_auth_page("account/password_reset_from_key.html", "设置新密码 - Jarvis", pr_key_body)

# Password reset from key done
pr_key_done_body = '''<div class="glass-card p-8 rounded-[2.5rem] text-center">
<h2 class="text-xl font-bold mb-4">密码已重置</h2>
<p class="text-sm mb-6" style="color:#9191A8;">你的密码已成功更改。</p>
<a href="{% url 'account_login' %}" class="btn-primary inline-block mt-2" style="text-decoration:none;">去登录</a>
</div>'''
write_auth_page("account/password_reset_from_key_done.html", "密码已重置 - Jarvis", pr_key_done_body)

# Error pages
ERROR_STYLE = STYLE + '<style>.error-code{font-size:120px;font-weight:700;background:linear-gradient(135deg,var(--primary),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1}</style>'

def write_error_page(filename, code, title, msg):
    html = HEAD + f'<title>{code} - Jarvis</title>\n' + ERROR_STYLE + '</head>\n<body class="flex h-screen">\n'
    html += '<div class="flex-1 flex items-center justify-center relative overflow-hidden">\n'
    html += '<div class="text-center z-10">\n'
    html += f'<div class="error-code">{code}</div>\n'
    html += f'<h2 class="text-xl font-bold mt-4 mb-2">{title}</h2>\n'
    html += f'<p class="text-sm mb-8" style="color:#9191A8;">{msg}</p>\n'
    html += f'<a href="/" class="inline-flex text-xs px-6 py-3 rounded-xl font-bold shadow-lg hover:scale-105 transition" style="background:var(--primary);color:white;text-decoration:none;">返回首页</a>\n'
    html += '</div></div>\n</body></html>'
    
    with open(f"templates/{filename}", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Written: templates/{filename}")

write_error_page("403.html", "403", "禁止访问", "你没有权限访问此页面。")
write_error_page("404.html", "404", "页面未找到", "你访问的页面不存在或已被移除。")
write_error_page("500.html", "500", "服务器错误", "服务器遇到错误，请稍后重试。")

print("\nAll auth and error pages written!")
