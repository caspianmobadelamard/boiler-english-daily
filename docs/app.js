// ============ Load Data ============
async function loadJSON(path) {
  try {
    const res = await fetch(path);
    return await res.json();
  } catch (e) {
    console.warn("Failed to load", path, e);
    return null;
  }
}

// ============ Stats ============
function renderStats(stats) {
  document.getElementById("stat-total").textContent    = stats.total || 0;
  document.getElementById("stat-mastered").textContent = stats.mastered || 0;
  document.getElementById("stat-learning").textContent = stats.learning || 0;
  const summary = window.__progress__ || {};
  document.getElementById("stat-sessions").textContent = summary.total_sessions || 0;
  document.getElementById("streak").textContent = summary.streak || 0;
}

// ============ Today ============
function renderToday(today) {
  if (!today) return;
  document.getElementById("today-topic").textContent    = today.topic || "—";
  document.getElementById("today-newwords").textContent = today.new_words || 0;
  document.getElementById("today-due").textContent      = (today.due_words || []).length;
  document.getElementById("today-avg").textContent      = Math.round(today.summary?.average_score || 0);
}

// ============ Listening ============
function renderListening(listening) {
  if (!listening) return;
  document.getElementById("listening-title").textContent = listening.title || "—";
  document.getElementById("listening-summary").textContent = listening.persian_summary || "";
  document.getElementById("listening-text").textContent = listening.text || "";

  const audio = document.getElementById("listening-audio");
  if (listening.audio_file) {
    const date = listening.date || new Date().toISOString().slice(0, 10);
    audio.src = `../output/listening_${date}.mp3`;
    audio.style.display = "block";
  } else {
    audio.style.display = "none";
  }

  const qBox = document.getElementById("listening-questions");
  qBox.innerHTML = "";
  (listening.questions || []).forEach((q, i) => {
    const div = document.createElement("div");
    div.style.margin = "10px 0";
    div.innerHTML = `<strong style="color:var(--neon-cyan)">Q${i + 1}.</strong> ${q.question}
                     <details><summary>Answer</summary>${q.answer}</details>`;
    qBox.appendChild(div);
  });
}

// ============ Scenario ============
function renderScenario(scenario) {
  if (!scenario) return;
  document.getElementById("scenario-title").textContent = scenario.title || "—";
  document.getElementById("scenario-context").textContent = scenario.context_persian || "";
  document.getElementById("scenario-opening").textContent = scenario.opening_line || "";

  const phrases = document.getElementById("scenario-phrases");
  phrases.innerHTML = "";
  (scenario.key_phrases || []).forEach(p => {
    const li = document.createElement("li");
    li.textContent = typeof p === "string" ? p : `${p.phrase || ""} — ${p.persian || ""}`;
    phrases.appendChild(li);
  });

  const vocab = document.getElementById("scenario-vocab");
  vocab.innerHTML = "";
  (scenario.vocabulary || []).forEach(v => {
    const li = document.createElement("li");
    li.textContent = typeof v === "string" ? v : `${v.word || ""} — ${v.persian || ""}`;
    vocab.appendChild(li);
  });
}

// ============ Vocabulary ============
function renderVocab(words) {
  const list = document.getElementById("vocab-list");
  const due  = document.getElementById("due-list");
  list.innerHTML = "";
  due.innerHTML = "";

  words.forEach(w => {
    const card = document.createElement("div");
    card.className = "vocab-card";
    card.innerHTML = `
      <div class="vocab-word">${w.word}</div>
      <div class="vocab-ipa">${w.ipa || ""}</div>
      <div class="vocab-persian">${w.persian || ""}</div>
      <div class="vocab-example">${w.example_technical || w.example_daily || ""}</div>
      <div class="mastery-bar">
        <div class="mastery-fill" style="width:${w.mastery || 0}%"></div>
      </div>
    `;
    list.appendChild(card);
  });
}

function renderDue(dueWords) {
  const due = document.getElementById("due-list");
  due.innerHTML = "";
  if (!dueWords || dueWords.length === 0) {
    due.innerHTML = `<p class="muted">✨ No words due for review. Great job!</p>`;
    return;
  }
  dueWords.forEach(w => {
    const card = document.createElement("div");
    card.className = "vocab-card";
    card.innerHTML = `
      <div class="vocab-word">${w.word}</div>
      <div class="vocab-persian">${w.persian || ""}</div>
      <div class="vocab-example">${w.definition || ""}</div>
    `;
    due.appendChild(card);
  });
}

// ============ Search ============
function setupSearch(allWords) {
  const input = document.getElementById("search");
  input.addEventListener("input", e => {
    const q = e.target.value.toLowerCase();
    const filtered = allWords.filter(w =>
      (w.word || "").toLowerCase().includes(q) ||
      (w.persian || "").includes(q) ||
      (w.topic || "").toLowerCase().includes(q)
    );
    renderVocab(filtered);
  });
}

// ============ Weekly Chart ============
function renderChart(weekly) {
  const ctx = document.getElementById("weeklyChart");
  if (!ctx) return;
  const labels = weekly.map(w => w.date.slice(5));
  const data = weekly.map(w => w.score);

  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Score",
        data,
        borderColor: "#00fff9",
        backgroundColor: "rgba(0, 255, 249, 0.15)",
        borderWidth: 3,
        tension: 0.4,
        fill: true,
        pointBackgroundColor: "#ff00e5",
        pointBorderColor: "#fff",
        pointRadius: 5,
        pointHoverRadius: 8,
        pointBorderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#e5e7eb" } },
      },
      scales: {
        x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(0, 255, 249, 0.08)" } },
        y: {
          ticks: { color: "#94a3b8" },
          grid: { color: "rgba(0, 255, 249, 0.08)" },
          beginAtZero: true, max: 100,
        }
      }
    }
  });
}

// ============ Boot ============
(async function init() {
  const today    = await loadJSON("data/today.json");
  const vocab    = await loadJSON("data/vocabulary.json");
  const progress = await loadJSON("data/progress.json");

  window.__progress__ = progress || {};

  if (today) {
    renderToday(today);
    renderListening(today.listening);
    renderScenario(today.scenario);
    renderDue(today.due_words);
    renderChart(today.weekly || []);
  }

  if (vocab) {
    renderStats({ ...(today?.stats || {}), total_sessions: progress?.total_sessions });
    renderVocab(vocab.words || []);
    setupSearch(vocab.words || []);
  }
})();