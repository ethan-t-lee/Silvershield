"""
Multimodal helper blueprint: Text-to-Speech (TTS) endpoint.

Usage:
  1) In `app.py` (no changes required here, but to enable):
       from multimodal import multimodal_bp
       app.register_blueprint(multimodal_bp)

  2) Client-side: POST JSON {"text":"...","lang":"en","slow":false} to `/tts`.
     The endpoint returns JSON {"success":true, "audio":"<base64>", "mime":"audio/mpeg"}.
     The client can create an `Audio('data:audio/mpeg;base64,'+audio)` and play it.

This file intentionally keeps server-side TTS separate to avoid lengthening `app.py`.
"""
from flask import Blueprint, request, jsonify
import io
import base64

try:
    from gtts import gTTS
except Exception as e:
    gTTS = None

multimodal_bp = Blueprint('multimodal', __name__)


@multimodal_bp.route('/tts', methods=['POST'])
def tts():
    """Generate speech (MP3) from posted text and return base64 audio.

    Request JSON: { "text": "...", "lang": "en", "slow": false }
    Response JSON: { "success": true, "audio": "<base64>", "mime": "audio/mpeg" }
    """
    if gTTS is None:
        return jsonify(success=False, message='gTTS not installed on server'), 500

    data = request.get_json() or {}
    text = (data.get('text') or '').strip()
    lang = data.get('lang', 'en')
    slow = bool(data.get('slow', False))

    if not text:
        return jsonify(success=False, message='No text provided'), 400

    try:
        buf = io.BytesIO()
        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.write_to_fp(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        return jsonify(success=True, audio=b64, mime='audio/mpeg')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
