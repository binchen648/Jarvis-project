<!DOCTYPE html>
<html lang="zh-CN" data-theme="jarvis">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <title>Jarvis OS - Aurora V2</title>
    <style>
        /* 1. 核心变量与主题系统 */
        :root {
            --surface-bg: #08080D;
            --surface-card: rgba(20, 20, 30, 0.65);
            --primary: #8B5CF6;
            --secondary: #4F8CFF;
            --accent: #06B6D4;
            --text-main: #F1F1F6;
            --text-secondary: #9191A8;
        }

        [data-theme="ocean"] {
            --primary: #2563EB;
            --secondary: #06B6D4;
            --accent: #67E8F9;
        }

        [data-theme="sunset"] {
            --primary: #F97316;
            --secondary: #EC4899;
            --accent: #FACC15;
        }

        [data-theme="forest"] {
            --primary: #22C55E;
            --secondary: #14B8A6;
            --accent: #84CC16;
        }

        [data-theme="rose"] {
            --primary: #EC4899;
            --secondary: #8B5CF6;
            --accent: #F472B6;
        }

        /* 2. 基础布局 */
        body {
            background: var(--surface-bg);
            color: var(--text-main);
            font-family: Inter, system-ui, sans-serif;
            overflow-x: hidden;
            position: relative;
            margin: 0;
            height: 100vh;
        }

        /* 3. Aurora 背景系统 */
        body::before {
            content: "";
            position: fixed;
            top: -30%; left: -30%;
            width: 160%; height: 160%;
            pointer-events: none;
            background: 
                radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--primary) 25%, transparent), transparent 30%),
                radial-gradient(circle at 80% 25%, color-mix(in srgb, var(--secondary) 20%, transparent), transparent 35%),
                radial-gradient(circle at 60% 80%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 40%);
            filter: blur(120px);
            animation: aurora-drift 35s ease-in-out infinite;
            z-index: -3;
        }

        body::after {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background: 
                radial-gradient(circle at 70% 60%, color-mix(in srgb, var(--primary) 12%, transparent), transparent 30%),
                radial-gradient(circle at 30% 70%, color-mix(in srgb, var(--secondary) 10%, transparent), transparent 35%);
            filter: blur(150px);
            animation: aurora-reverse 60s ease-in-out infinite;
            z-index: -2;
        }

        @keyframes aurora-drift {
            0% { transform: translate(0,0) scale(1); }
            25% { transform: translate(-5%,4%) scale(1.08); }
            50% { transform: translate(5%,-5%) scale(1.15); }
            75% { transform: translate(-3%,-4%) scale(1.08); }
            100% { transform: translate(0,0) scale(1); }
        }

        @keyframes aurora-reverse {
            0% { transform: translate(0,0) scale(1); }
            50% { transform: translate(6%,5%) scale(1.2); }
            100% { transform: translate(0,0) scale(1); }
        }

        /* 4. Glass Card 升级版 */
        .glass-card {
            background: linear-gradient(135deg, rgba(255,255,255,.05), rgba(255,255,255,.015));
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,.06);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.04), 0 10px 30px rgba(0,0,0,.25);
            transition: all .3s ease;
        }

        .glass-card:hover {
            transform: translateY(-2px);
            border-color: color-mix(in srgb, var(--primary) 40%, rgba(255,255,255,.05));
            box-shadow: 0 0 0 1px color-mix(in srgb, var(--primary) 15%, transparent), 0 15px 40px color-mix(in srgb, var(--primary) 8%, transparent);
        }

        /* 5. Jarvis Core 动画 */
        .jarvis-core {
            width: 32px; height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 0 15px color-mix(in srgb, var(--primary) 50%, transparent);
            animation: spin 8s linear infinite;
        }

        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    </style>
</head>
<body class="flex h-screen overflow-hidden">

    <!-- 侧边栏 (微调以匹配新主题) -->
    <aside class="w-64 bg-black/20 backdrop-blur-2xl border-r border-white/5 flex flex-col z-10">
        <div class="p-8">
            <h1 class="text-2xl font-bold tracking-tighter italic text-white">JARVIS</h1>
        </div>
        <nav class="flex-1 px-4 space-y-2">
            <a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/5 text-white"><i class="bi bi-grid-fill" style="color: var(--secondary)"></i> Dashboard</a>
            <a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-stars"></i> Agent</a>
            <a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-brain"></i> Memory</a>
            <a href="#" class="flex items-center gap-3 px-4 py-3 rounded-2xl text-white/50 hover:bg-white/5 transition"><i class="bi bi-target"></i> Goals</a>
        </nav>
        <div class="p-6">
            <div class="flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/10">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-zinc-700 to-zinc-900 border border-white/10"></div>
                <div>
                    <p class="text-sm font-bold">Alex</p>
                    <p class="text-[10px] text-white/40">v2.0 Aurora</p>
                </div>
            </div>
        </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col z-10">
        
        <!-- Header -->
        <header class="h-20 flex items-center justify-between px-10">
            <div class="flex flex-col">
                <h2 class="text-xs font-medium uppercase tracking-widest text-[#9191A8]">System Status</h2>
                <p class="text-[10px] text-emerald-400">● Operational / Optimal</p>
            </div>
            
            <div class="flex items-center gap-6">
                <!-- 主题切换器 -->
                <div class="flex items-center gap-2">
                    <i class="bi bi-palette2 text-xs text-white/40"></i>
                    <select id="themeSwitcher" class="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-white/20 transition cursor-pointer">
                        <option value="jarvis" class="bg-[#08080D]">Jarvis</option>
                        <option value="ocean" class="bg-[#08080D]">Ocean</option>
                        <option value="sunset" class="bg-[#08080D]">Sunset</option>
                        <option value="forest" class="bg-[#08080D]">Forest</option>
                        <option value="rose" class="bg-[#08080D]">Rose</option>
                    </select>
                </div>

                <div class="h-8 w-px bg-white/10 mx-2"></div>
                <div class="jarvis-core"></div>
            </div>
        </header>

        <!-- 内容区 -->
        <div class="flex-1 overflow-y-auto px-10 pb-10 custom-scrollbar">
            <div class="max-w-6xl mx-auto space-y-10 pt-4">
                
                <!-- Welcome Section -->
                <section>
                    <div class="flex justify-between items-end">
                        <div>
                            <h1 class="text-4xl font-bold tracking-tight">Good Morning, Alex.</h1>
                            <p class="text-sm text-[#9191A8] mt-2 italic">Jarvis 建议：18:30 开始学习，今日精力高峰</p>
                        </div>
                        <span class="text-xs font-mono text-white/30">JUN 16, 2026</span>
                    </div>
                </section>

                <!-- KPI Grid -->
                <section class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="glass-card p-6 rounded-[2rem]">
                        <p class="text-[10px] uppercase tracking-[0.2em] text-[#9191A8]">Today Focus</p>
                        <p class="text-3xl font-bold mt-2">82% <span class="text-[10px] text-emerald-400 ml-1 font-normal">▲ 5%</span></p>
                    </div>
                    <div class="glass-card p-6 rounded-[2rem]">
                        <p class="text-[10px] uppercase tracking-[0.2em] text-[#9191A8]">Goal Health</p>
                        <p class="text-3xl font-bold mt-2">3 <span class="text-sm font-normal text-emerald-400">正常</span></p>
                    </div>
                    <div class="glass-card p-6 rounded-[2rem]">
                        <p class="text-[10px] uppercase tracking-[0.2em] text-[#9191A8]">Memory Growth</p>
                        <p class="text-3xl font-bold mt-2">+12 <span class="text-[10px] text-[#9191A8] ml-1 font-normal">条</span></p>
                    </div>
                    <div class="glass-card p-6 rounded-[2rem]">
                        <p class="text-[10px] uppercase tracking-[0.2em] text-[#9191A8]">AI Confidence</p>
                        <p class="text-3xl font-bold mt-2">87%</p>
                    </div>
                </section>

                <!-- Main Grid -->
                <section class="grid grid-cols-12 gap-8">
                    <!-- Today's Plan -->
                    <div class="col-span-12 lg:col-span-8 space-y-4">
                        <div class="flex justify-between items-center ml-2">
                            <h3 class="text-lg font-semibold">Today's Plan</h3>
                            <span class="text-xs text-[#9191A8]">2/3 tasks completed</span>
                        </div>
                        <div class="glass-card rounded-[2.5rem] overflow-hidden">
                            <div class="p-8 flex items-center justify-between group hover:bg-white/[0.02] transition cursor-pointer border-b border-white/5">
                                <div class="flex items-center gap-6">
                                    <div class="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-[var(--primary)] transition text-[var(--primary)] font-bold">01</div>
                                    <div>
                                        <p class="font-bold">LeetCode 92 — 两数之和</p>
                                        <p class="text-xs text-[#9191A8]">Goal · 35min · 🎯 今日必完成</p>
                                    </div>
                                </div>
                                <i class="bi bi-chevron-right text-white/20 group-hover:text-[var(--primary)]"></i>
                            </div>
                            <div class="p-8 flex items-center justify-between bg-white/[0.01] opacity-50">
                                <div class="flex items-center gap-6">
                                    <div class="w-12 h-12 rounded-2xl bg-[var(--primary)] flex items-center justify-center text-white shadow-lg">
                                        <i class="bi bi-check-lg text-xl"></i>
                                    </div>
                                    <div>
                                        <p class="font-bold line-through">阅读 ReAct Agent 笔记</p>
                                        <p class="text-xs">Memory · 20min · 🧠 已复习</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Progress & Timeline -->
                    <div class="col-span-12 lg:col-span-4 space-y-8">
                        <div class="glass-card p-8 rounded-[2.5rem]">
                            <h3 class="text-sm font-semibold mb-6">Goal Progress</h3>
                            <div class="space-y-6">
                                <div>
                                    <div class="flex justify-between text-xs mb-2">
                                        <span class="text-[#9191A8]">系统设计</span>
                                        <span>70%</span>
                                    </div>
                                    <div class="h-1 w-full bg-white/5 rounded-full">
                                        <div class="h-full bg-[var(--primary)] rounded-full transition-all duration-1000" style="width: 70%"></div>
                                    </div>
                                </div>
                                <div>
                                    <div class="flex justify-between text-xs mb-2">
                                        <span class="text-[#9191A8]">LeetCode 150</span>
                                        <span>90%</span>
                                    </div>
                                    <div class="h-1 w-full bg-white/5 rounded-full">
                                        <div class="h-full bg-[var(--secondary)] rounded-full transition-all duration-1000 shadow-[0_0_10px_var(--secondary)]" style="width: 90%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="glass-card p-8 rounded-[2.5rem] relative overflow-hidden group">
                            <!-- 背景微光 -->
                            <div class="absolute -right-10 -top-10 w-32 h-32 bg-[var(--accent)] opacity-10 blur-3xl group-hover:opacity-20 transition"></div>
                            
                            <h3 class="text-sm font-semibold mb-4">Memory Timeline</h3>
                            <div class="space-y-4 border-l border-white/10 ml-2 pl-4">
                                <div class="relative">
                                    <div class="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-[var(--accent)]"></div>
                                    <p class="text-xs">复习 ReAct Agent 笔记</p>
                                    <p class="text-[10px] text-[#9191A8]">1h ago</p>
                                </div>
                                <div class="relative">
                                    <div class="absolute -left-[21px] top-1 w-2 h-2 rounded-full bg-white/10"></div>
                                    <p class="text-xs text-[#9191A8]">学习 Python 异步编程</p>
                                    <p class="text-[10px] text-[#5C5C72]">2h ago</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    </main>

    <!-- AI Surface 底部入口 -->
    <div class="fixed bottom-8 right-8 z-50">
        <div class="w-14 h-14 bg-[var(--primary)] rounded-full flex items-center justify-center text-white shadow-[0_0_30px_rgba(0,0,0,0.5)] cursor-pointer hover:scale-110 transition shadow-glow relative">
            <div class="absolute inset-0 rounded-full bg-[var(--primary)] opacity-20 animate-ping"></div>
            <i class="bi bi-stars text-xl"></i>
        </div>
    </div>

    <!-- JS 逻辑 -->
    <script>
        const switcher = document.getElementById("themeSwitcher");

        // 主题切换监听
        switcher.addEventListener("change", e => {
            const theme = e.target.value;
            document.documentElement.setAttribute("data-theme", theme);
            localStorage.setItem("jarvis-theme", theme);
        });

        // 初始化加载已存主题
        const saved = localStorage.getItem("jarvis-theme");
        if (saved) {
            document.documentElement.setAttribute("data-theme", saved);
            switcher.value = saved;
        }

        // 简单的鼠标悬停互动背景
        document.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 20;
            const y = (e.clientY / window.innerHeight - 0.5) * 20;
            document.body.style.setProperty('--mouse-x', `${x}px`);
            document.body.style.setProperty('--mouse-y', `${y}px`);
        });
    </script>
</body>
</html>