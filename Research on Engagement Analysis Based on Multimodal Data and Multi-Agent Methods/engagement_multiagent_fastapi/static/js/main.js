document.addEventListener("DOMContentLoaded", () => {
  initCountUp();
  initFocusGroups();
  initExpandGroups();
  initTimelineChart();
  initDashboardChart();
  initRealtimePage();
  initStudentPage();
  initReportChart();
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
  const duration = 700;
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
    const activate = (name) => cards.forEach((card) => card.classList.toggle("is-active", card.dataset.expandItem === name));
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

function initDashboardChart() {
  const canvas = document.getElementById("dashboardChart");
  if (!canvas || !window.dashboardCurve) return;
  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: window.dashboardCurve.labels,
      datasets: [
        { label: "实际专注度", data: window.dashboardCurve.actual, borderColor: "#4F6BED", tension: 0.3 },
        { label: "下一片段预测", data: window.dashboardCurve.predict, borderColor: "#D97706", borderDash: [6, 5], tension: 0.3 },
      ],
    },
  });
}

function initRealtimePage() {
  const dataset = window.realtimeDataset;
  const canvas = document.getElementById("realtimeChart");
  if (!dataset || !canvas) return;

  const labels = dataset.frames.map((f) => `片段${f.time_block}`);
  const values = dataset.frames.map((f) => f.avg_focus);
  const predicts = dataset.frames.map((f) => f.predicted_next_focus);
  new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "实时专注度", data: values, borderColor: "#16A34A", tension: 0.28 },
        { label: "动态预测", data: predicts, borderColor: "#D97706", borderDash: [5, 4], tension: 0.28 },
      ],
    },
    options: { animation: false },
  });

  const info = document.getElementById("realtimeInfo");
  const heatmap = document.getElementById("heatmap");
  const evidencePanel = document.getElementById("evidencePanel");
  let idx = 0;

  const paint = () => {
    const frame = dataset.frames[idx];
    info.innerHTML = `
      <div class="summary-grid">
        <div class="summary-card"><div class="stat-label">课堂阶段</div><div class="stat-text mt-2">${frame.phase}</div></div>
        <div class="summary-card"><div class="stat-label">最佳时机判断</div><div class="stat-text mt-2">${frame.intervention_needed ? "建议立即干预" : "建议轻干预"}</div></div>
        <div class="summary-card"><div class="stat-label">推荐动作</div><div class="stat-text mt-2">${frame.recommended_action}</div></div>
      </div>`;

    heatmap.innerHTML = `<h3 class="panel-title mb-2">学生专注热力矩阵（时间片 ${frame.time_block}）</h3><div class="table-responsive"><table class="table"><thead><tr><th>学生</th><th>专注度</th><th>状态</th></tr></thead><tbody>${frame.students
      .map((s) => `<tr style="background:${scoreColor(s.focus_score)}"><td>${s.student_name}</td><td>${s.focus_score}</td><td>${s.focus_state}</td></tr>`)
      .join("")}</tbody></table></div>`;

    evidencePanel.innerHTML = `
      <div class="panel-card">
        <h3 class="panel-title">解释依据（时间片 ${frame.time_block}）</h3>
        <p class="panel-description mt-2">触发原因：${frame.intervention_reason}</p>
        <div class="tag-group mt-2">
          ${Object.entries(frame.evidence)
            .map(([key, value]) => `<span class="soft-tag">${key}: ${value}</span>`)
            .join("")}
        </div>
      </div>`;

    idx = (idx + 1) % dataset.frames.length;
  };

  paint();
  setInterval(paint, 1800);
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

function initReportChart() {
  const series = window.reportSeries;
  const canvas = document.getElementById("reportChart");
  if (!series || !canvas) return;
  new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: { labels: series.labels, datasets: [{ label: "课堂片段专注度", data: series.scores, backgroundColor: "rgba(79,107,237,0.55)" }] },
  });
}

function initDemoMode() {
  const btn = document.getElementById("startDemoBtn");
  if (btn) {
    btn.addEventListener("click", () => {
      const steps = ["/dashboard", "/realtime?dataset_id=mid_drop", "/student/stu_002?dataset_id=mid_drop", "/report?dataset_id=recover_after_intervention"];
      localStorage.setItem("efocus_demo_steps", JSON.stringify(steps));
      localStorage.setItem("efocus_demo_next", "1");
      window.location.href = steps[0];
    });
  }

  const pendingIndex = localStorage.getItem("efocus_demo_next");
  const steps = localStorage.getItem("efocus_demo_steps");
  if (!pendingIndex || !steps) return;

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
