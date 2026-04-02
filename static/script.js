/*************************
      Mobile Scenario Engine - Email, Web, SMS, Call apps
**************************/
let currentMessage = "";
let currentType = "";
let currentDifficulty = "";
let currentExpectedLabel = "";
let scenarioLoadTime = null;
const mobileLabels = globalThis.mobileLabels || {};

function applyMobileTranslations() {
    const backLabel = mobileLabels.back || "Back";
    const readAloudLabel = mobileLabels.readAloud || "Read Aloud";
    const realLabel = mobileLabels.real || "REAL";
    const fakeLabel = mobileLabels.fake || "FAKE";
    const speakLabel = mobileLabels.speak || "Speak";
    const muteLabel = mobileLabels.mute || "Mute";
    const endLabel = mobileLabels.end || "End";
    const speakerLabel = mobileLabels.speaker || "Speaker";
    const reportScamCallLabel = mobileLabels.reportScamCall || fakeLabel;
    const looksSafeLabel = mobileLabels.looksSafe || realLabel;

    document.querySelectorAll(".back-btn, .back-button").forEach(btn => {
        btn.textContent = `← ${backLabel}`;
    });

    const readBtn = document.getElementById("readAloudMobile");
    if (readBtn) {
        readBtn.textContent = document.querySelector(".call-app") ? speakerLabel : readAloudLabel;
    }

    const safeBtn = document.getElementById("markSafe");
    if (safeBtn) {
        safeBtn.textContent = document.querySelector(".call-app") ? looksSafeLabel : realLabel;
    }

    const scamBtn = document.getElementById("markScam");
    if (scamBtn) {
        scamBtn.textContent = document.querySelector(".call-app") ? reportScamCallLabel : fakeLabel;
    }

    const voiceBtn = document.getElementById("voiceAnswerBtn");
    if (voiceBtn) voiceBtn.textContent = speakLabel;

    const callButtons = document.querySelectorAll(".call-controls .call-btn");
    if (callButtons[0]) callButtons[0].textContent = muteLabel;
    if (callButtons[1]) callButtons[1].textContent = endLabel;
}

function buildWebSpeechText(sc) {
    if (!sc) return "";

    const adText = (sc.ads || [])
        .map(ad => `${ad.title || "Sponsored result"}. ${ad.snippet || ""}`)
        .join(" ");

    const resultText = (sc.results || [])
        .map(result => `${result.title || "Result"}. ${result.snippet || ""}`)
        .join(" ");

    return `${adText} ${resultText}`.replace(/\s+/g, " ").trim();
}

const ScenarioEngine = {
    endpoints: {
        email: "/generate-email",
        sms: "/generate-sms",
        call: "/generate-call",
        web: "/generate-web"
    },

    async load(type) {
        currentType = type;
        currentExpectedLabel = "";

        const scenarioBody = document.getElementById("scenarioBody");
        const appsGrid = document.querySelector(".apps");
        if (!scenarioBody || !appsGrid) return;

        scenarioBody.innerHTML = "<p class='loading'>Loading scenario...</p>";
        appsGrid.style.display = "none";

        // Load snippet HTML template
        const htmlResp = await fetch(`/static/snippets/${type}.html`);
        scenarioBody.innerHTML = await htmlResp.text();
        applyMobileTranslations();

        // Pick appropriate endpoint
        const endpoint = this.endpoints[type];
        if (!endpoint) return;

        // Fetch scenario from backend
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                theme: "SilverShield training",
                platform: type === "email" ? "mobile" : undefined
            })
        });

        const data = await res.json();
        if (!data.success) {
            scenarioBody.innerHTML = "<p>Error loading scenario.</p>";
            console.error("Scenario error:", data.error);
            return;
        }

        currentDifficulty = data.difficulty;

        const diffLabel = document.getElementById("difficultyLabel");
        if (diffLabel) diffLabel.innerText = "Level: " + currentDifficulty;

        // Record time scenario was displayed
        scenarioLoadTime = Date.now();

        // Map returned data to scenario object for UI
        let sc = null;
        if (type === "email") sc = { email_html: data.email };
        else if (type === "sms") sc = data.sms;
        else if (type === "call") sc = data.call;
        else if (type === "web") sc = data.web;

        // Capture server-provided ground truth label for grading.
        if (type === "email" || type === "sms" || type === "call" || type === "web") {
            const raw = (data.expected_label || sc?.expected_label || sc?.label || "").toLowerCase();
            if (raw === "scam" || raw === "fake") {
                currentExpectedLabel = "scam";
            } else if (raw === "not_scam" || raw === "real") {
                currentExpectedLabel = "not_scam";
            } else {
                currentExpectedLabel = "";
            }
        }

        this.fill(type, sc);

        // After filling UI, if email was loaded, attempt to preload TTS
        if (currentMessage && (type === 'email' || type === 'sms' || type === 'call' || type === 'web')) {
            try {
                const tmp = document.createElement('div');
                tmp.innerHTML = currentMessage;
                const plain = (tmp.textContent || tmp.innerText || '').replace(/\s+/g,' ').trim();
                if (window.preloadTTS) {
                    const lang = (window.getTTSLang && window.getTTSLang()) || 'en';
                    // fire-and-forget preload (internal dedupe prevents duplicates)
                    try { window.preloadTTS(plain, { lang, slow: false }); } catch(e) { /* ignore */ }
                }
            } catch (e) { console.warn('Preload TTS failed', e); }
        }

        // Hook up scam/safe buttons
        const scamBtn = document.getElementById("markScam");
        const safeBtn = document.getElementById("markSafe");
        const readAloudMobile = document.getElementById('readAloudMobile');

        if (scamBtn) scamBtn.onclick = () => { if (window.stopTTS) try { window.stopTTS(); } catch(e){}; analyzeChoice("scam"); };
        if (safeBtn) safeBtn.onclick = () => { if (window.stopTTS) try { window.stopTTS(); } catch(e){}; analyzeChoice("not_scam"); };

        const voiceBtn = document.getElementById("voiceAnswerBtn");
        if (voiceBtn && window.startVoiceAnswer) {
            voiceBtn.onclick = () => {
                if (window.stopTTS) try { window.stopTTS(); } catch(e) {}
                window.startVoiceAnswer(
                    voiceBtn,
                    () => analyzeChoice("not_scam"),
                    () => analyzeChoice("scam")
                );
            };
        }

        if (readAloudMobile) {
            readAloudMobile.onclick = async () => {
                try {
                    const tmp = document.createElement('div'); tmp.innerHTML = currentMessage;
                    const plain = (tmp.textContent || tmp.innerText || '').replace(/\s+/g,' ').trim();
                    if (window.playPreloaded) {
                        const played = await window.playPreloaded(plain);
                        if (played) return;
                    }
                    if (window.speak) {
                        const lang = (window.getTTSLang && window.getTTSLang()) || 'en';
                        await window.speak(plain, { lang, slow: false });
                    }
                } catch (e) { console.warn('Mobile TTS play failed', e); }
            };
        }
    },

    fill(type, sc) {
        if (!sc) return;

        // EMAIL
        if (type === "email") {
            const emailBody = document.getElementById("emailBody");
           // const emailSubject = document.getElementById("emailSubject");
            //const fromName = document.getElementById("from-name");
            //const fromEmail = document.getElementById("from-email");


            const htmlEmail = sc.email_html;
            currentMessage = htmlEmail;

            emailBody.innerHTML = htmlEmail;

          //  const fromMatch = htmlEmail.match(/<b>From:<\/b>\s*(.*?)<br>/i);
            //const dateMatch = htmlEmail.match(/<b>Date:<\/b>\s*(.*?)<br>/i);

            //const senderString = fromMatch ? fromMatch[1] : "Unknown";

            // parsed metadata
            //emailSubject.innerText = subjectMatch ? subjectMatch[1] : "No Subject";
            //metaFrom.innerText = senderString;
            //metaDate.innerText = dateMatch ? dateMatch[1] : "";

            //avatar - 1st letter of sender's name
            //const initial = senderString.charAt(0).toUpperCase();
            //senderAvatar.innerText = initial;

            //fromEmail.innerText = fromMatch ? fromMatch[1] : "unknown@sender.com";
            //fromName.innerText = "Sender";
            return;
        }

        // SMS
        if (type === "sms") {
            document.getElementById("smsBody").innerText = sc.text;
            document.getElementById("smsNumber").innerText = sc.number;
            document.getElementById("smsTime").innerText = sc.time || "12:04 PM";
            currentMessage = sc.text;
            return;
        }

        // CALL
        if (type === "call") {
            document.getElementById("call-number").innerText = sc.number;
            document.getElementById("call-caller").innerText = sc.caller_name || "Unknown Caller";
            document.getElementById("call-transcript").innerText = sc.transcript;
            currentMessage = sc.transcript;
            return;
        }

        // WEB
        if (type === "web") {
              const container = document.getElementById("web-content");


    // Clear container
    container.innerHTML = "";

    // -----------------------------
    // if ads exist, render ads
    // -----------------------------
    if (sc.ads && sc.ads.length > 0) {
        const adSection = document.createElement("div");
        adSection.classList.add("ads-section");

        sc.ads.forEach(ad => {
            const adTitle = (ad && ad.title) ? ad.title : "Sponsored result";
            const adUrl = (ad && ad.url) ? ad.url : "";
            const adSnippet = (ad && ad.snippet) ? ad.snippet : "";
            const adBox = document.createElement("div");
            adBox.classList.add("ad-box");
            adBox.innerHTML = `
                <div class="ad-title">${adTitle}</div>
                <div class="ad-url">${adUrl}</div>
                <div class="ad-snippet">${adSnippet}</div>
                <div class="ad-label">Sponsored</div>
            `;
            adSection.appendChild(adBox);
        });

        container.appendChild(adSection);
    }

  // -----------------------------
//  render actual search results
// -----------------------------
if (sc.results && sc.results.length > 0) {

    // Render top title INSIDE container (like Google does)
    const heading = document.createElement("div");
    heading.classList.add("search-main-title");
    heading.innerText = sc.results[0].title || "Search Results";
    container.appendChild(heading);

    sc.results.forEach(result => {
        const resultBox = document.createElement("div");
        resultBox.classList.add("search-result");

        resultBox.innerHTML = `
            <div class="search-result-title">${result.title}</div>
            <div class="search-result-link">${result.url}</div>
            <div class="search-result-snippet">${result.snippet}</div>
        `;

        container.appendChild(resultBox);
    });
} else {
    const heading = document.createElement("div");
    heading.classList.add("search-main-title");
    heading.innerText = "Search Results";
    container.appendChild(heading);
}

// -----------------------------
//  pagination
// -----------------------------
if (sc.pagination) {
    const nav = document.createElement("div");
    nav.classList.add("pagination-nav");

    nav.innerHTML = `
        <button id="nextPageBtn">${sc.pagination.next_page_label || "Next >"}</button>
    `;

    container.appendChild(nav);

    document.getElementById("nextPageBtn").onclick = () => {
        ScenarioEngine.load("web");
    };
}

currentMessage = buildWebSpeechText(sc);
return;
        }
    }
};

// Make openApp globally available
window.openApp = type => ScenarioEngine.load(type);

// back button module ui app
function backToApps(){
    const scenarioBody = document.getElementById("scenarioBody");
    const appsGrid = document.querySelector(".apps");

    if(scenarioBody) scenarioBody.innerHTML = "";
    if(appsGrid) appsGrid.style.display = "block"; //restore grid

    // Stop any playing TTS when user navigates back
    if (window.stopTTS) try { window.stopTTS(); } catch (e) {}

    console.log("Back button clicked --> Returning to app menu.")
}

// stop any TTS when leaving the scenario
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && window.stopTTS) {
        try { window.stopTTS(); } catch (e) {}
    }
});

async function analyzeChoice(choice) {
    try {
        // Calculate time spent on scenario (in seconds)
        const timeSpent = scenarioLoadTime ? Math.round((Date.now() - scenarioLoadTime) / 1000) : 0;

        const response = await fetch("/api/analyze_any", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: currentType,
                platform: "mobile",
                user_choice: choice,
                expected_label: currentExpectedLabel || undefined,
                message: currentMessage,
                time_spent_seconds: timeSpent
            })
        });

        const data = await response.json();

        if (!data.success) {
            alert("Error analyzing response.");
            return;
        }

        alert(
            data.feedback.feedback +
            `\n\n(Current difficulty: ${data.difficulty_now})`
        );

        // Reload next scenario automatically
        ScenarioEngine.load(currentType);

    } catch (err) {
        console.error("analyzeChoice() error:", err);
        alert("Server error analyzing choice.");
    }
}

/*************************
   BUTTON HANDLERS
   (for mobile + desktop)
**************************/

document.addEventListener("click", () => {
    const realBtn = document.getElementById("markSafe"); //mobile real
    const fakeBtn = document.getElementById("markScam"); //mobile fake
    const desktopReal = document.getElementById("realBtn");
    const desktopFake = document.getElementById("fakeBtn");
    // Bind handlers once and ensure TTS is stopped before submitting
    if (realBtn && !realBtn.dataset.bound) {
        realBtn.dataset.bound = true;
        realBtn.onclick = () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            analyzeChoice("not_scam");
        };
    }

    if (fakeBtn && !fakeBtn.dataset.bound) {
        fakeBtn.dataset.bound = true;
        fakeBtn.onclick = () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            analyzeChoice("scam");
        };
    }

    if (desktopReal && !desktopReal.dataset.bound) {
        desktopReal.dataset.bound = true;
        desktopReal.onclick = () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            analyzeChoice("not_scam");
        };
    }

    if (desktopFake && !desktopFake.dataset.bound) {
        desktopFake.dataset.bound = true;
        desktopFake.onclick = () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            analyzeChoice("scam");
        };
    }
});

window.analyzeChoice = analyzeChoice;

window.backToApps = backToApps;
