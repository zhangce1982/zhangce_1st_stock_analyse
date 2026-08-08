const cards = document.querySelector("#cards");
const buttons = document.querySelectorAll("button[data-horizon]");

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
