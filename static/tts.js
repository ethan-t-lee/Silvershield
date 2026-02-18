// Simple helper to call the server-side /tts endpoint and play audio.
// Usage:
//   speak('Hello world');
//   speak('Hello', {lang:'en', slow:false}).then(audio=> audio.pause());

// Internal state to ensure a single playback at a time
window._tts_state = window._tts_state || { audio: null, utter: null };
// store preloaded audio: { text: string, audio: HTMLAudioElement, promise: Promise }
window._tts_state.preloaded = window._tts_state.preloaded || null;

function _normalizeText(raw) {
  if (!raw) return '';
  return raw.replace(/\s+/g, ' ').trim();
}

function stopTTS() {
  try {
    if (window._tts_state.audio) {
      try { window._tts_state.audio.pause(); } catch (e) {}
      try { window._tts_state.audio.currentTime = 0; } catch (e) {}
      window._tts_state.audio = null;
    }

    if (window.speechSynthesis && window._tts_state.utter) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
      window._tts_state.utter = null;
    }
    // do not clear preloaded audio here; keep it for quick replay
  } catch (e) {
    console.warn('stopTTS error', e);
  }
}

async function preloadTTS(text, options = {}) {
  if (!text) return null;
  const norm = _normalizeText(text);

  // If already preloaded the same text and audio exists, return it
  if (window._tts_state.preloaded && window._tts_state.preloaded.text === norm && window._tts_state.preloaded.audio) {
    return window._tts_state.preloaded.audio;
  }

  // If a preload is already in progress for the same text, return its promise
  if (window._tts_state.preloaded && window._tts_state.preloaded.text === norm && window._tts_state.preloaded.promise) {
    try {
      await window._tts_state.preloaded.promise;
      return window._tts_state.preloaded.audio || null;
    } catch (e) {
      return null;
    }
  }

  // Start fetch and store promise to dedupe concurrent calls
  const p = (async () => {
    try {
      const resp = await fetch('/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: norm, lang: options.lang || 'en', slow: !!options.slow })
      });
      const data = await resp.json().catch(() => null);
      if (!data || !data.success) return null;

      const b64 = data.audio;
      const mime = data.mime || 'audio/mpeg';
      const audio = new Audio(`data:${mime};base64,${b64}`);
      audio.preload = 'auto';
      audio.autoplay = false;
      audio.addEventListener('ended', () => { if (window._tts_state.audio === audio) window._tts_state.audio = null; });

      window._tts_state.preloaded = { text: norm, audio: audio, promise: null };
      return audio;
    } catch (e) {
      console.warn('preloadTTS failed', e);
      // clear preloaded on failure
      if (window._tts_state.preloaded && window._tts_state.preloaded.text === norm) {
        window._tts_state.preloaded = null;
      }
      return null;
    }
  })();

  window._tts_state.preloaded = { text: norm, audio: null, promise: p };
  const audio = await p;
  if (audio) window._tts_state.preloaded.audio = audio;
  return audio;
}

async function playPreloaded(text) {
  if (!window._tts_state.preloaded) return null;
  const norm = text ? _normalizeText(text) : window._tts_state.preloaded.text;
  if (!norm || window._tts_state.preloaded.text !== norm) return null;

  // If audio already available, play it
  if (window._tts_state.preloaded.audio) {
    const audio = window._tts_state.preloaded.audio;
    stopTTS();
    window._tts_state.audio = audio;
    try { audio.currentTime = 0; } catch (e) {}
    audio.play().catch(err => console.warn('Preloaded playback prevented', err));
    return audio;
  }

  // If a preload promise exists, await it then play
  if (window._tts_state.preloaded.promise) {
    try {
      const audio = await window._tts_state.preloaded.promise;
      if (!audio) return null;
      stopTTS();
      window._tts_state.audio = audio;
      try { audio.currentTime = 0; } catch (e) {}
      audio.play().catch(err => console.warn('Preloaded playback prevented', err));
      return audio;
    } catch (e) {
      return null;
    }
  }

  return null;
}

async function speak(text, options = {}) {
  if (!text) return null;
  // Always stop any existing playback before starting a new one
  stopTTS();

  const payload = { text: text, lang: options.lang || 'en', slow: !!options.slow };

  let resp;
  try {
    resp = await fetch('/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (networkErr) {
    console.error('TTS network error', networkErr);
    resp = null;
  }

  if (!resp) {
    // fallback to browser
    if (window.speechSynthesis) {
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = options.lang || 'en-US';
      window._tts_state.utter = utter;
      window.speechSynthesis.speak(utter);
      return null;
    }
    return null;
  }

  const data = await resp.json().catch(() => null);
  if (!data || !data.success) {
    console.error('TTS error:', data ? data.message || data : 'no data');
    // Fallback to browser TTS if available
    if (window.speechSynthesis) {
      try {
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = options.lang || 'en-US';
        window._tts_state.utter = utter;
        window.speechSynthesis.speak(utter);
        return null;
      } catch (e) {
        console.warn('Browser TTS fallback failed', e);
        return null;
      }
    }
    return null;
  }

  try {
    const b64 = data.audio;
    const mime = data.mime || 'audio/mpeg';
    // If the exact audio was preloaded, play that to avoid duplicate memory
    if (window._tts_state.preloaded && window._tts_state.preloaded.text && window._tts_state.preloaded.text === text) {
      const pre = window._tts_state.preloaded.audio;
      if (pre) {
        window._tts_state.audio = pre;
        try { pre.currentTime = 0; } catch (e) {}
        await pre.play().catch(err => console.warn('Playback prevented:', err));
        return pre;
      }
    }

    const audio = new Audio(`data:${mime};base64,${b64}`);
    // track this audio so we can stop it later
    window._tts_state.audio = audio;
    audio.addEventListener('ended', () => { if (window._tts_state.audio === audio) window._tts_state.audio = null; });
    await audio.play().catch(err => console.warn('Playback prevented:', err));
    return audio;
  } catch (e) {
    console.error('Error playing TTS audio', e);
    return null;
  }
}

// Expose globally for easy use in templates
window.speak = speak;
window.stopTTS = stopTTS;
// Expose preload/play helpers
window.preloadTTS = preloadTTS;
window.playPreloaded = playPreloaded;
