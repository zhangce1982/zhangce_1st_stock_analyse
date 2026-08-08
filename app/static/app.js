const cards = document.querySelector("#cards");
const buttons = document.querySelectorAll("button[data-horizon]");
const eventsContainer = document.querySelector("#events");

async function load(horizon) {
  cards.innerHTML = "<p>正在计算机会评分…</p>";
  const response = await fetch(`/api/opportunities?horizon=${horizon}`);
  const items = await response.json();
  cards.innerHTML = items.map(item => `
    <article class="card">
      <div class="card-top">
        <div><span class="code">${item.code}</span><h2>${item.name}</h2><span class="industry">${item.industry}</span></div>
        <div class="score">${item.score}</div>
      </div>
      <h3>主要依据</h3><ul>${item.reasons.map(x => `<li>${x}</li>`).join("")}</ul>
      <h3>风险提示</h3><ul class="risk">${item.risks.map(x => `<li>${x}</li>`).join("")}</ul>
      <p class="source">数据源：${item.source}${item.missing_fields.length ? ` · 缺失字段 ${item.missing_fields.length} 项` : ""}</p>
    </article>`).join("");
}

buttons.forEach(button => button.addEventListener("click", () => {
  buttons.forEach(x => x.classList.remove("active"));
  button.classList.add("active");
  load(button.dataset.horizon);
}));

load("short");

async function loadEvents() {
  eventsContainer.innerHTML = "<p>正在获取公告与政策…</p>";
  try {
    const response = await fetch("/api/events");
    const items = await response.json();
    eventsContainer.innerHTML = items.length ? items.slice(0, 20).map(item => `
      <a class="event" href="${item.url}" target="_blank" rel="noopener noreferrer">
        <div><span class="event-type">${item.event_type === "policy" ? "政策" : "公告"}</span><span class="event-date">${item.published_date}</span></div>
        <strong>${item.title}</strong>
        <p>${item.industries.length ? item.industries.join(" · ") : "尚未映射行业"} · 影响 ${item.impact_score}</p>
      </a>`).join("") : "<p>当前没有取得事件，可能是上游接口暂时不可用。</p>";
  } catch (error) {
    eventsContainer.innerHTML = "<p>事件接口暂时不可用。</p>";
  }
}

loadEvents();
