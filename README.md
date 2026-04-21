# 📞 Call Intelligence — Streamlit App

> Transcribe call recordings and summarise key points — **no API key, no cost**.  
> Built with Python + Streamlit. Deploy free on Streamlit Cloud.

## ✨ Features

- **⬆ Upload Audio** — MP3, WAV, M4A, MP4, WEBM, OGG, FLAC
- **✎ Paste Transcript** — from Zoom, Teams, Meet, Otter.ai, etc.
- **📝 Full Transcript** — auto-transcribed via Google Speech (free tier)
- **🎯 Key Points** — top sentences via TF-IDF scoring
- **✅ Action Items** — auto-detected from intent keywords
- **😊 Sentiment** — positive / neutral / negative with score
- **🏷 Topics** — key themes extracted from the call
- **📊 Stats** — word count, duration estimate, read time
- **⬇ Download** — transcript and full summary as `.txt`

---

## 🚀 Run Locally

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/call-intelligence.git
cd call-intelligence

# 2. Install system dependency (for audio conversion)
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg

# 3. Install Python packages
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Open http://localhost:8501

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set **Main file:** `app.py`
4. Click **Deploy** — live in ~2 minutes!

> `packages.txt` automatically installs `ffmpeg` on Streamlit Cloud.

---

## 📁 Project Structure

```
call-intelligence/
├── app.py            # Main Streamlit app
├── requirements.txt  # Python dependencies
├── packages.txt      # System packages (ffmpeg for Streamlit Cloud)
└── README.md
```

---

## 🧠 How It Works

| Feature | Method |
|---|---|
| Transcription | `SpeechRecognition` + Google Speech free API |
| Key Points | TF-IDF sentence scoring |
| Action Items | Regex on action-intent keywords |
| Sentiment | Positive/negative word lexicon |
| Topics | Top-N frequent content words |

---

## 🔒 Privacy

- Audio is sent to Google's free Speech-to-Text only for transcription
- No data is stored anywhere
- No account or API key required

---

## 📄 License

MIT
