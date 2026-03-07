let jobId = null;
let pollTimer = null;
let chosenFile = null;

const STEPS = ["meta", "audio", "transcribe", "gpt"];

function fileChosen(input) {
  chosenFile = input.files[0] || null;
  document.getElementById("file-name").textContent = chosenFile ? chosenFile.name : "";
  if (chosenFile) document.getElementById("url-input").value = "";
}

function setStep(id, state) {
  const el = document.getElementById("step-" + id);
  if (el) el.className = state;
}

function reset() {
  clearInterval(pollTimer);
  jobId = null;
  chosenFile = null;

  document.getElementById("file-name").textContent = "";
  document.getElementById("file-input").value = "";
  document.getElementById("url-input").value = "";
  document.getElementById("progress-bar").style.width = "0%";

  show("card-input");
  show("card-options");
  hide("card-progress");
  hide("card-error");
  hide("card-result");

  STEPS.forEach(s => setStep(s, ""));
}

function show(id) { document.getElementById(id).style.display = ""; }
function hide(id) { document.getElementById(id).style.display = "none"; }

async function startJob() {
  const url = document.getElementById("url-input").value.trim();
  if (!url && !chosenFile) {
    alert("Cole uma URL do YouTube ou selecione um arquivo.");
    return;
  }

  hide("card-input");
  hide("card-options");
  hide("card-error");
  hide("card-result");
  show("card-progress");

  const form = new FormData();
  if (url) form.append("url", url);
  if (chosenFile) form.append("file", chosenFile);
  form.append("lang", document.getElementById("lang").value);
  form.append("model", document.getElementById("model").value);
  form.append("tone", document.getElementById("tone").value);
  form.append("summary_lang", document.getElementById("summary-lang").value);

  try {
    const res = await fetch("/summarize", { method: "POST", body: form });
    const data = await res.json();
    if (data.error) { showError(data.error); return; }
    jobId = data.job_id;
    pollTimer = setInterval(poll, 1500);
  } catch (e) {
    showError("Falha ao conectar ao servidor: " + e.message);
  }
}

async function poll() {
  if (!jobId) return;
  try {
    const res = await fetch("/status/" + jobId);
    const data = await res.json();
    updateProgress(data);
    if (data.status === "done" || data.status === "error") clearInterval(pollTimer);
  } catch (_) {}
}

function updateProgress(data) {
  document.getElementById("progress-bar").style.width = (data.progress || 0) + "%";
  document.getElementById("progress-label").textContent = data.message || "";

  if (data.current_step) {
    const idx = STEPS.indexOf(data.current_step);
    STEPS.forEach((s, i) => {
      if (i < idx)      setStep(s, "done");
      else if (i === idx) setStep(s, "active");
    });
  }

  if (data.status === "done")  showResult(data.result);
  if (data.status === "error") showError(data.error);
}

function showResult(r) {
  hide("card-progress");
  show("card-result");

  document.getElementById("result-title").textContent = r.title || "Resumo";
  document.getElementById("summary-text").textContent = r.summary;
  document.getElementById("transcript-box").textContent = r.transcript || "";
  document.getElementById("badge-model").textContent = r.model || "Groq";
  document.getElementById("badge-duration").textContent = r.duration || "";
}

function showError(msg) {
  hide("card-progress");
  show("card-error");
  show("card-input");
  show("card-options");
  document.getElementById("error-msg").textContent = msg;
}

function toggleTranscript() {
  const box = document.getElementById("transcript-box");
  box.style.display = box.style.display === "block" ? "none" : "block";
}