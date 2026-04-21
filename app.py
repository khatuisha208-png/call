import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile, os, re, math
from collections import Counter

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="Call Intelligence",
    page_icon="📞",
    layout="centered"
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.main { background: #0a0a0f; }
.block-container { max-width: 800px; padding-top: 2rem; }

h1 { 
    background: linear-gradient(135deg, #fff 0%, #43e8d8 50%, #6c63ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-size: 2.5rem !important; font-weight: 700 !important;
}

.tag {
    display: inline-block; padding: 4px 14px;
    border: 1px solid rgba(67,232,216,.4); border-radius: 20px;
    color: #43e8d8; font-size: 11px; letter-spacing: 3px;
    text-transform: uppercase; margin-bottom: 8px;
}

.chip {
    background: #12121a; border: 1px solid #2a2a3e;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
}
.chip-title {
    font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    margin-bottom: 10px;
}

.stat-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.stat { 
    background: #1a1a26; border: 1px solid #2a2a3e;
    border-radius: 8px; padding: 10px 16px; text-align: center; flex: 1;
}
.stat-val { font-size: 22px; font-weight: 600; color: #e8e8f0; }
.stat-lbl { font-size: 10px; color: #7a7a9a; letter-spacing: 1px; }

.kp { 
    border-left: 3px solid #6c63ff; padding: 6px 12px;
    margin: 6px 0; background: #0f0f18; border-radius: 0 8px 8px 0;
    font-size: 13px; line-height: 1.6; color: #e8e8f0;
}
.ai { 
    border-left: 3px solid #43e8a0; padding: 6px 12px;
    margin: 6px 0; background: #0f0f18; border-radius: 0 8px 8px 0;
    font-size: 13px; line-height: 1.6; color: #e8e8f0;
}
.topic-tag {
    display: inline-block; padding: 3px 12px;
    background: rgba(108,99,255,.12); border: 1px solid rgba(108,99,255,.25);
    border-radius: 20px; font-size: 12px; color: #6c63ff; margin: 3px;
}
.transcript-box {
    background: #0a0a0f; border: 1px solid #2a2a3e; border-radius: 10px;
    padding: 16px; font-size: 13px; line-height: 1.8;
    color: #e8e8f0; max-height: 300px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown('<div class="tag">◉ No API Required</div>', unsafe_allow_html=True)
st.title("Call Intelligence")
st.markdown("**Transcribe · Analyse · Summarise** — 100% free, runs locally")
st.divider()

# ── NLP Engine ─────────────────────────────────────────────
STOP_WORDS = set("""
i me my we our you your he she it they them the a an and or but in on at
to for of with is was are were be been being have has had do does did will
would could should may might shall that this these those which who what when
where how not no so if as by from up out about into just can also its their
there than then very more some all any each both few other such same own too
now here only over after before again further during while
""".split())

ACTION_KW = re.compile(
    r"\b(will|shall|going to|need to|should|must|have to|plan to|"
    r"follow up|schedule|send|share|review|update|complete|finish|"
    r"implement|create|build|draft|prepare|confirm|discuss|"
    r"coordinate|reach out|contact|arrange|assign)\b", re.I
)

POS_WORDS = set("great good excellent perfect wonderful amazing fantastic happy "
    "pleased agree positive success successful achieved accomplish approved "
    "confirm definitely absolutely love appreciate thank thanks helpful "
    "useful productive benefit opportunity exciting confident clear resolved".split())

NEG_WORDS = set("bad poor terrible awful wrong fail failed failure problem issue "
    "concern worried difficult hard challenge unable cannot cant wont delayed "
    "behind missed reject rejected disagree no not never unfortunately sorry "
    "risk block stuck unclear confusing confused frustrated".split())


def tokenise_sentences(text):
    text = re.sub(r'\n+', ' ', text)
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 15]


def tokenise_words(text):
    return re.findall(r"\b[a-z']{2,}\b", text.lower())


def word_freq(words):
    return Counter(w for w in words if w not in STOP_WORDS and len(w) > 2)


def score_sentence(sentence, freq):
    words = [w for w in tokenise_words(sentence) if w not in STOP_WORDS]
    if not words:
        return 0
    return sum(freq.get(w, 0) for w in words) / len(words)


def extract_key_points(sentences, freq, n=5):
    if not sentences:
        return ["No content detected."]
    scored = sorted(enumerate(sentences), key=lambda x: score_sentence(x[1], freq), reverse=True)
    top = sorted(scored[:n], key=lambda x: x[0])
    return [s for _, s in top] or [sentences[0]]


def extract_action_items(sentences, n=5):
    items = [s.strip() for s in sentences if ACTION_KW.search(s) and len(s) < 250]
    return items[:n] or ["No explicit action items detected."]


def compute_sentiment(words):
    pos = sum(1 for w in words if w in POS_WORDS)
    neg = sum(1 for w in words if w in NEG_WORDS)
    total = pos + neg or 1
    score = round((pos / total) * 100)
    label = "Positive 😊" if score >= 60 else "Negative 😟" if score <= 40 else "Neutral 😐"
    return label, score


def extract_topics(freq, n=8):
    return [w.capitalize() for w, _ in freq.most_common(20) if len(w) > 4][:n]


def compute_stats(text, sentences, words):
    wc   = len(words)
    mins = max(1, math.ceil(wc / 130))
    return {
        "Words": wc,
        "Sentences": len(sentences),
        "Est. Duration": f"~{mins} min",
        "Read Time": f"{max(1, math.ceil(wc/200))} min",
    }


def analyse(text):
    sentences = tokenise_sentences(text)
    words     = tokenise_words(text)
    freq      = word_freq(words)
    return {
        "key_points"  : extract_key_points(sentences, freq),
        "action_items": extract_action_items(sentences),
        "sentiment"   : compute_sentiment(words),
        "topics"      : extract_topics(freq),
        "stats"       : compute_stats(text, sentences, words),
    }


# ── Transcription helpers ───────────────────────────────────
def transcribe_audio(file_bytes, ext):
    """Convert uploaded audio → text using SpeechRecognition + Google (free tier)."""
    recogniser = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    wav_path = tmp_path + ".wav"
    try:
        audio = AudioSegment.from_file(tmp_path)
        audio.export(wav_path, format="wav")
        with sr.AudioFile(wav_path) as source:
            audio_data = recogniser.record(source)
        text = recogniser.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = ""
        st.warning("Could not recognise speech in the audio. Try a clearer recording.")
    except sr.RequestError as e:
        text = ""
        st.error(f"Speech recognition service error: {e}")
    finally:
        os.unlink(tmp_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)
    return text


# ── UI ─────────────────────────────────────────────────────
tab_upload, tab_text = st.tabs(["⬆ Upload Audio / Video", "✎ Paste Transcript"])

transcript = ""

with tab_upload:
    st.markdown("Upload a call recording (MP3, WAV, M4A, MP4, WEBM, OGG).")
    uploaded = st.file_uploader("Choose file", type=["mp3","wav","m4a","mp4","webm","ogg","flac"])
    if uploaded:
        st.audio(uploaded)
        if st.button("▶ Transcribe & Analyse", key="btn_upload"):
            with st.spinner("Transcribing audio... (uses Google Speech free tier)"):
                ext = "." + uploaded.name.rsplit(".", 1)[-1].lower()
                transcript = transcribe_audio(uploaded.read(), ext)
            if not transcript:
                st.error("No speech detected. Try the Paste Transcript tab.")

with tab_text:
    pasted = st.text_area(
        "Paste transcript here",
        placeholder="Paste your call transcript from Zoom, Teams, Meet, Otter.ai...",
        height=220
    )
    if st.button("▶ Analyse Transcript", key="btn_text"):
        if pasted.strip():
            transcript = pasted.strip()
        else:
            st.warning("Please paste some text first.")

# ── Results ─────────────────────────────────────────────────
if transcript:
    result = analyse(transcript)
    st.divider()
    st.subheader("📋 Full Transcript")
    st.markdown(f'<div class="transcript-box">{transcript}</div>', unsafe_allow_html=True)
    st.download_button("⬇ Download Transcript", transcript, file_name="transcript.txt")

    st.divider()
    st.subheader("🧠 Intelligence Summary")

    # Stats
    stats = result["stats"]
    cols  = st.columns(len(stats))
    for col, (label, val) in zip(cols, stats.items()):
        with col:
            st.metric(label, val)

    st.markdown("---")

    # Key points
    st.markdown("**🎯 Key Points**")
    for i, kp in enumerate(result["key_points"], 1):
        st.markdown(f'<div class="kp"><b>{str(i).zfill(2)}</b> &nbsp; {kp}</div>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**✅ Action Items**")
        for ai in result["action_items"]:
            st.markdown(f'<div class="ai">✓ &nbsp; {ai}</div>', unsafe_allow_html=True)

    with col2:
        label, score = result["sentiment"]
        st.markdown("**😊 Sentiment**")
        st.markdown(f"**{label}**")
        st.progress(score / 100)
        st.caption(f"Positive score: {score}%")

    st.markdown("---")

    st.markdown("**🏷 Key Topics**")
    topics_html = " ".join(f'<span class="topic-tag">{t}</span>' for t in result["topics"])
    st.markdown(topics_html, unsafe_allow_html=True)

    st.markdown("---")

    # Download summary
    summary_text = f"""CALL INTELLIGENCE SUMMARY
=========================

TRANSCRIPT
----------
{transcript}

KEY POINTS
----------
{chr(10).join(f'{i+1}. {kp}' for i, kp in enumerate(result['key_points']))}

ACTION ITEMS
------------
{chr(10).join(f'• {ai}' for ai in result['action_items'])}

SENTIMENT
---------
{label} ({score}% positive)

TOPICS
------
{', '.join(result['topics'])}

STATS
-----
{chr(10).join(f'{k}: {v}' for k, v in stats.items())}
"""
    st.download_button("⬇ Download Full Summary", summary_text, file_name="call_summary.txt")
