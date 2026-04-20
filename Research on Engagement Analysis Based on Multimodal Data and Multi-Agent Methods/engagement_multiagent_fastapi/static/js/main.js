document.addEventListener("DOMContentLoaded", () => {
  initCountUp();
  initFocusGroups();
  initExpandGroups();
  initTimelineChart();
  initRealtimePage();
  initStudentPage();
  initDemoMode();
});

function initCountUp() {
  document.querySelectorAll(".count-up, .count-up-decimal").forEach((el) => {
    const target = Number(el.dataset.target || 0);
    const decimals = el.classList.contains("count-up-decimal") ? 2 : 0;
    animateNumber(el, target, decimals);
  });
}

function animateNumber(el, target, decimals) {
  const start = performance.now();
  const duration = 650;
  requestAnimationFrame(function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = (target * eased).toFixed(decimals);
    if (progress < 1) requestAnimationFrame(step);
  });
}

function initFocusGroups() {
  document.querySelectorAll("[data-focus-group]").forEach((group) => {
    const panels = [...group.querySelectorAll("[data-focus-panel]")];
    const targets = [...group.querySelectorAll("[data-focus-target]")];
    if (!panels.length || !targets.length) return;
    const activate = (name) => {
      panels.forEach((p) => p.classList.toggle("is-active", p.dataset.focusPanel === name));
      targets.forEach((t) => t.classList.toggle("is-active", t.dataset.focusTarget === name));
    };
    targets.forEach((target) => target.addEventListener("click", () => activate(target.dataset.focusTarget)));
    activate(group.dataset.defaultFocus || panels[0].dataset.focusPanel);
    group._activateFocus = activate;
  });
}

function initExpandGroups() {
  document.querySelectorAll("[data-expand-group]").forEach((group) => {
    const cards = [...group.querySelectorAll("[data-expand-item]")];
    const targets = [...group.querySelectorAll("[data-expand-target]")];
    if (!cards.length || !targets.length) return;
    const activate = (name) => {
      cards.forEach((card) => card.classList.toggle("is-active", card.dataset.expandItem === name));
    };
    targets.forEach((target) => target.addEventListener("click", () => activate(target.dataset.expandTarget)));
    activate(cards[0].dataset.expandItem);
  });
}

function initTimelineChart() {
  const canvas = document.getElementById("timelineChart");
  if (!canvas || !window.timelineChartData) return;
  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: window.timelineChartData.labels,
      datasets: [{ label: "专注度得分", data: window.timelineChartData.scores, borderColor: "#4F6BED", tension: 0.35 }],
    },
  });
}

function initRealtimePage() {
  const dataset = window.realtimeDataset;
  const canvas = document.getElementById("realtimeChart");
  if (!dataset || !canvas) return;

  const labels = dataset.frames.map((f) => `${f.time_block}`);
  const values = dataset.frames.map((f) => f.avg_focus);
  const chart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: { labels, datasets: [{ label: "班级平均专注度", data: values, borderColor: "#16A34A", tension: 0.28 }] },
    options: { animation: false },
  });

  const info = document.getElementById("realtimeInfo");
  const heatmap = document.getElementById("heatmap");
  let idx = 0;
  const paint = () => {
    const frame = dataset.frames[idx];
    info.innerHTML = `
      <div class="summary-grid">
        <div class="summary-card"><div class="stat-label">课堂阶段</div><div class="stat-text mt-2">${frame.phase}</div></div>
        <div class="summary-card"><div class="stat-label">趋势状态</div><div class="stat-text mt-2">${frame.trend_state}</div></div>
        <div class="summary-card"><div class="stat-label">推荐动作</div><div class="stat-text mt-2">${frame.recommended_action}</div></div>
      </div>`;
    heatmap.innerHTML = `<h3 class="panel-title mb-2">学生专注热力矩阵（时间片 ${frame.time_block}）</h3><div class="table-responsive"><table class="table"><thead><tr><th>学生</th><th>专注度</th><th>状态</th></tr></thead><tbody>${frame.students
      .map((s) => `<tr style="background:${scoreColor(s.focus_score)}"><td>${s.student_name}</td><td>${s.focus_score}</td><td>${s.focus_state}</td></tr>`)
      .join("")}</tbody></table></div>`;
    idx = (idx + 1) % dataset.frames.length;
  };
  paint();
  setInterval(paint, 1800);

  chart.update();
}

function scoreColor(score) {
  if (score >= 75) return "rgba(22,163,74,0.14)";
  if (score >= 55) return "rgba(217,119,6,0.12)";
  return "rgba(220,38,38,0.12)";
}

function initStudentPage() {
  const data = window.studentTimeline;
  const canvas = document.getElementById("studentChart");
  if (!data || !canvas || !data.series) return;
  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: data.series.map((p) => `片段${p.time_block}`),
      datasets: [{ label: `${data.student_name} 专注度`, data: data.series.map((p) => p.focus_score), borderColor: "#4F6BED", tension: 0.3 }],
    },
  });
}

function initDemoMode() {
  const btn = document.getElementById("startDemoBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const steps = ["/dashboard", "/realtime?dataset_id=mid_drop", "/student/stu_002?dataset_id=mid_drop", "/report?dataset_id=recover_after_intervention"];
    let idx = 0;
    const jump = () => {
      if (idx >= steps.length) return;
      window.location.href = steps[idx];
      idx += 1;
      if (idx < steps.length) localStorage.setItem("efocus_demo_next", String(idx));
    };
    localStorage.setItem("efocus_demo_steps", JSON.stringify(steps));
    localStorage.setItem("efocus_demo_next", "1");
    window.location.href = steps[0];
  });

  const pendingIndex = localStorage.getItem("efocus_demo_next");
  const steps = localStorage.getItem("efocus_demo_steps");
  if (pendingIndex && steps) {
    const parsed = JSON.parse(steps);
    const i = Number(pendingIndex);
    if (parsed[i]) {
      setTimeout(() => {
        localStorage.setItem("efocus_demo_next", String(i + 1));
        window.location.href = parsed[i];
      }, 2200);
    } else {
      localStorage.removeItem("efocus_demo_next");
      localStorage.removeItem("efocus_demo_steps");
    }
  }
}
