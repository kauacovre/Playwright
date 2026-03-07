import os
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from .jobs import update_job


def run_pipeline(job_id, url, file_path, lang, model_size, tone, summary_lang):
    tmp_dir = tempfile.mkdtemp(prefix="videosumm_")
    try:
        if url:
            meta = extract_metadata(url, job_id)
            audio_path, duration = download_audio(url, tmp_dir, job_id)
        else:
            meta = {"title": Path(file_path).stem, "channel": ""}
            audio_path = file_path
            duration = "?"
            update_job(job_id, current_step="audio", message="Usando arquivo enviado...", progress=30)

        transcript = transcribe(audio_path, lang, model_size, job_id)
        summary, model_used = summarize(transcript, meta["title"], tone, summary_lang, job_id)

        update_job(
            job_id,
            status="done",
            progress=100,
            message="Concluído.",
            current_step="done",
            result={
                "title": meta.get("title", "Vídeo"),
                "channel": meta.get("channel", ""),
                "summary": summary,
                "transcript": transcript,
                "duration": duration,
                "model": model_used,
            },
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        update_job(job_id, status="error", error=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def extract_metadata(url, job_id):
    update_job(job_id, current_step="meta", message="Extraindo metadados...", progress=10)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)

            title = page.title().replace(" - YouTube", "").strip()

            channel_el = page.query_selector("ytd-channel-name yt-formatted-string")
            channel = channel_el.inner_text() if channel_el else ""

            browser.close()
            return {"title": title, "channel": channel}
    except Exception as e:
        print(f"[playwright] {e}")
        return {"title": url, "channel": ""}


def download_audio(url, tmp_dir, job_id):
    update_job(job_id, current_step="audio", message="Baixando áudio...", progress=25)

    import yt_dlp

    out_path = os.path.join(tmp_dir, "audio.%(ext)s")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        duration_sec = info.get("duration", 0)

    audio_file = os.path.join(tmp_dir, "audio.mp3")
    if not os.path.exists(audio_file):
        for f in Path(tmp_dir).iterdir():
            if f.suffix in (".mp3", ".m4a", ".webm", ".ogg"):
                audio_file = str(f)
                break

    duration = str(timedelta(seconds=int(duration_sec))) if duration_sec else "?"
    return audio_file, duration


def transcribe(audio_path, lang, model_size, job_id):
    update_job(job_id, current_step="transcribe", message=f"Transcrevendo com Whisper ({model_size})...", progress=50)

    import whisper

    model = whisper.load_model(model_size)
    lang_arg = None if lang == "auto" else lang
    result = model.transcribe(audio_path, language=lang_arg, fp16=False)
    return result["text"].strip()


def summarize(transcript, title, tone, summary_lang, job_id):
    update_job(job_id, current_step="gpt", message="Gerando resumo com Groq...", progress=80)

    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY não definida. Crie sua chave gratuita em https://console.groq.com "
            "e execute: export GROQ_API_KEY='gsk_...'"
        )

    lang_names = {"pt": "português brasileiro", "en": "English", "es": "español"}
    tone_prompts = {
        "profissional": "Tom profissional e objetivo.",
        "casual": "Tom casual e amigável.",
        "bullet": "Use exclusivamente bullet points organizados em seções.",
        "academico": "Tom acadêmico e formal.",
    }

    system_prompt = f"""Você é um assistente especializado em resumir vídeos.
Responda SEMPRE em {lang_names.get(summary_lang, "português brasileiro")}.
{tone_prompts.get(tone, tone_prompts["profissional"])}

Estruture o resumo com:
1. Visão Geral (2-3 frases)
2. Pontos Principais
3. Conclusão / Takeaways"""

    user_prompt = f"Título: {title}\n\nTranscrição:\n{transcript[:12000]}"

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1500,
        temperature=0.5,
    )

    return response.choices[0].message.content.strip(), response.model