import uuid
import tempfile
import threading
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify

from .jobs import jobs, update_job
from .pipeline import run_pipeline

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/summarize", methods=["POST"])
def summarize():
    url = request.form.get("url", "").strip()
    lang = request.form.get("lang", "pt")
    model_size = request.form.get("model", "small")
    tone = request.form.get("tone", "profissional")
    summary_lang = request.form.get("summary_lang", "pt")

    file_path = None
    if "file" in request.files:
        f = request.files["file"]
        if f.filename:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.filename).suffix)
            f.save(tmp.name)
            file_path = tmp.name

    if not url and not file_path:
        return jsonify({"error": "Forneça uma URL ou arquivo."}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": "Iniciando...",
        "current_step": "",
        "result": None,
        "error": None,
    }

    threading.Thread(
        target=run_pipeline,
        args=(job_id, url, file_path, lang, model_size, tone, summary_lang),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id})


@bp.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado"}), 404
    return jsonify(job)