/*************************
  Voice Answer Helper
  Exposes: window.startVoiceAnswer(buttonEl, onReal, onFake)
    Recognises safe/fake answers based on current page language.
**************************/
(function () {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    // If browser doesn't support voice, hide all mic buttons once DOM is ready
    if (!SpeechRecognition) {
        window.startVoiceAnswer = null;
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.voice-answer-btn').forEach(b => {
                b.style.display = 'none';
            });
        });
        return;
    }

    const WORDS_BY_LANG = {
        en: {
            real: ['real', 'legitimate', 'legit', 'safe', 'okay', 'ok', 'not fake', 'not scam', 'normal'],
            fake: ['fake', 'scam', 'phishing', 'fraud', 'spam', 'suspicious', 'danger', 'dangerous', 'phish']
        },
        es: {
            real: ['real', 'verdadero', 'legitimo', 'legítimo', 'seguro', 'confiable', 'no es estafa'],
            fake: ['falso', 'estafa', 'phishing', 'fraude', 'spam', 'sospechoso', 'peligroso']
        },
        zh: {
            real: ['真实', '真的', '安全', '不是诈骗', '没问题'],
            fake: ['假的', '诈骗', '欺诈', '钓鱼', '可疑', '危险']
        }
    };

    function getVoiceLocaleConfig() {
        const raw = (document.documentElement.getAttribute('lang') || 'en').toLowerCase();
        if (raw.startsWith('es')) {
            return { recLang: 'es-ES', words: WORDS_BY_LANG.es };
        }
        if (raw.startsWith('zh')) {
            return { recLang: 'zh-CN', words: WORDS_BY_LANG.zh };
        }
        return { recLang: 'en-US', words: WORDS_BY_LANG.en };
    }

    /**
     * Start listening for a "real" or "fake" spoken answer.
     * @param {HTMLElement} buttonEl  - The mic button (used for visual feedback).
     * @param {Function}    onReal    - Called when user says a "real" word.
     * @param {Function}    onFake    - Called when user says a "fake" word.
     */
    window.startVoiceAnswer = function (buttonEl, onReal, onFake) {
        if (!buttonEl || buttonEl.dataset.listening === 'true') return;

        const localeConfig = getVoiceLocaleConfig();
        const realWords = [...WORDS_BY_LANG.en.real, ...localeConfig.words.real];
        const fakeWords = [...WORDS_BY_LANG.en.fake, ...localeConfig.words.fake];

        const rec = new SpeechRecognition();
        rec.lang = localeConfig.recLang;
        rec.interimResults = false;
        rec.maxAlternatives = 5;

        const origText = buttonEl.textContent;
        buttonEl.textContent = 'Listening...';
        buttonEl.dataset.listening = 'true';
        buttonEl.disabled = true;

        function reset(msg) {
            if (msg && msg !== origText) {
                buttonEl.textContent = msg;
                setTimeout(() => {
                    buttonEl.textContent = origText;
                    buttonEl.dataset.listening = 'false';
                    buttonEl.disabled = false;
                }, 1800);
            } else {
                buttonEl.textContent = origText;
                buttonEl.dataset.listening = 'false';
                buttonEl.disabled = false;
            }
        }

        rec.onresult = function (event) {
            const alts = [];
            for (let i = 0; i < event.results[0].length; i++) {
                alts.push(event.results[0][i].transcript.toLowerCase().trim());
            }

            for (const alt of alts) {
                if (realWords.some(w => alt.includes(w))) {
                    reset();
                    onReal();
                    return;
                }
                if (fakeWords.some(w => alt.includes(w))) {
                    reset();
                    onFake();
                    return;
                }
            }

            // Heard something but couldn't match
            reset('Say "real" or "fake"');
        };

        rec.onerror = function (e) {
            if (e.error === 'no-speech') {
                reset('No speech detected');
            } else if (e.error === 'not-allowed') {
                reset('Mic blocked');
            } else {
                reset('Mic error');
            }
        };

        rec.onend = function () {
            // onend fires after onresult / onerror — only reset if still waiting
            if (buttonEl.dataset.listening === 'true') {
                reset();
            }
        };

        rec.start();
    };
})();
