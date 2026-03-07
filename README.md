# Video Summarizer

Transcreve e resume vídeos do YouTube ou arquivos locais usando Playwright, Whisper e Groq.

## Instalação

```bash
pip install -r requirements.txt
playwright install chromium
```

FFmpeg também é necessário:
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Configuração

Crie sua chave gratuita em https://console.groq.com e exporte:

```bash
export GROQ_API_KEY="gsk_..."
```

## Uso

```bash
python run.py
```

Acesse http://localhost:5000

## Estrutura

```
video_summarizer/
├── run.py               # Ponto de entrada
├── requirements.txt
├── app/
│   ├── __init__.py      # App factory
│   ├── routes.py        # Rotas Flask
│   ├── pipeline.py      # Lógica de processamento
│   └── jobs.py          # Estado dos jobs em memória
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Modelos Whisper

| Modelo | Velocidade | Precisão |
|--------|-----------|----------|
| base   | Rápido    | Básica   |
| small  | Médio     | Boa      |
| medium | Lento     | Muito boa|
| large  | Lento     | Máxima   |