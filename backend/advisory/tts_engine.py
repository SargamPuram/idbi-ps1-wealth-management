"""
Dhanvi — Piper TTS engine (self-hosted, CPU-only text-to-speech).

Design goal mirrors advisory/engine.py: the REST API must stay usable even if
a voice model is missing or synthesis fails. Every call is wrapped so
failures raise TTSUnavailable with a clear, actionable message instead of
bubbling up as an unhandled 500 — app/main.py catches this and returns a
graceful error payload.

Voices are Piper ONNX models (~60MB each), not checked into git — they're
downloaded at Docker build time (see backend/Dockerfile) into tts_models/,
same pattern as how other PS generate their data/model artifacts at build time.
"""
import io
import logging
import wave
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / "tts_models"

# Voice chosen per language. See backend/README.md for why these two were
# picked over the other available options on huggingface.co/rhasspy/piper-voices.
VOICE_FILES = {
    "English": "en_US-amy-medium.onnx",
    "Hindi": "hi_IN-pratham-medium.onnx",
}

# Keep synthesis snappy for a live demo — Dhanvi's replies are conversational
# (~80-160 words per the system prompt), so this is a generous ceiling that
# only kicks in for pathological inputs.
MAX_CHARS = 1200


class TTSUnavailable(Exception):
    """Raised whenever a voice can't be loaded or synthesis fails."""
    pass


class DhanviTTS:
    """Lazily loads + caches one Piper voice per language, thread-safe."""

    def __init__(self):
        self._voices = {}
        self._load_lock = Lock()
        # Piper's espeak phonemizer uses a process-global lock internally, and
        # onnxruntime sessions are fine for concurrent reads, but we keep
        # synthesis serialized per-process for simplicity/predictability —
        # a demo doesn't need to synthesize two replies at once.
        self._synth_lock = Lock()

    def _resolve_language(self, language: str | None) -> str:
        return language if language in VOICE_FILES else "English"

    def _load_voice(self, language: str):
        from piper import PiperVoice  # imported lazily so a missing package doesn't crash app import

        filename = VOICE_FILES[language]
        model_path = MODELS_DIR / filename
        config_path = MODELS_DIR / f"{filename}.json"
        if not model_path.exists() or not config_path.exists():
            raise TTSUnavailable(
                f"Voice model for '{language}' not found at {model_path}. It should be downloaded "
                f"at Docker build time (see backend/Dockerfile) or manually via the huggingface URLs "
                f"in backend/README.md."
            )
        try:
            return PiperVoice.load(str(model_path), str(config_path))
        except Exception as e:  # pragma: no cover - defensive
            raise TTSUnavailable(f"Failed to load Piper voice '{language}': {type(e).__name__}: {e}")

    def get_voice(self, language: str | None):
        key = self._resolve_language(language)
        with self._load_lock:
            voice = self._voices.get(key)
            if voice is None:
                voice = self._load_voice(key)
                self._voices[key] = voice
        return voice

    def synthesize(self, text: str, language: str | None = "English") -> bytes:
        """Synthesize `text` and return raw WAV bytes."""
        text = (text or "").strip()
        if not text:
            raise TTSUnavailable("No text provided for speech synthesis.")
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS].rsplit(" ", 1)[0] + "..."

        voice = self.get_voice(language)  # may raise TTSUnavailable — let it propagate
        try:
            with self._synth_lock:
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    voice.synthesize_wav(text, wf)
                return buf.getvalue()
        except Exception as e:
            raise TTSUnavailable(f"Piper synthesis failed ({type(e).__name__}: {e}).")

    def status(self) -> dict:
        available = {
            lang: (MODELS_DIR / fname).exists() and (MODELS_DIR / f"{fname}.json").exists()
            for lang, fname in VOICE_FILES.items()
        }
        return {
            "tts_available": any(available.values()),
            "models_dir": str(MODELS_DIR),
            "voices": available,
        }


# Module-level singleton, mirrors the `engine = DhanviEngine()` pattern in app/main.py.
tts_engine = DhanviTTS()
