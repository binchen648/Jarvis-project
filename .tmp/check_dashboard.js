const http = require("http");
http.get("http://localhost:8001/", (res) => {
  let data = "";
  res.on("data", c => data += c);
  res.on("end", () => {
    // Check KPI card accents
    const accents = data.match(/data-accent="([^"]+)"/g);
    console.log("Accents:", accents);
    // Check active nav
    const activeNav = data.match(/class="[^"]*nav-item active[^"]*"/g);
    console.log("Active nav:", activeNav);
    // Check topbar title
    const topbarTitle = data.match(/<h1 class="topbar-title">([^<]+)<\/h1>/);
    console.log("Topbar title:", topbarTitle ? topbarTitle[1] : "missing");
    // Check Jarvis Core
    console.log("Jarvis Core:", data.includes("jarvis-core") ? "exists" : "missing");
    // Check AI Surface
    console.log("AI Surface:", data.includes("ai-surface-fab") ? "exists" : "missing");
    // Check greeting
    const greeting = data.match(/greeting-(morning|afternoon|evening)/);
    console.log("Greeting:", greeting ? greeting[1] : "none shown");
  });
});