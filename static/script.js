/*************************
      Mobile Scenario Engine - Email, Web, SMS, Call apps
**************************/
const mobileTranslations = globalThis.mobileTranslations || {};

function mobileLabel(key, fallback = key) {
    return mobileTranslations[key] || fallback;
}

const mobileTtsLang = mobileTranslations.ttsLang || 'en';

function applySnippetTranslations(type) {
    if (type === "email") {
        const backButton = document.getElementById("emailBackBtn");
        const emailBody = document.getElementById("emailBody");
        const readAloudButton = document.getElementById("readAloudMobile");
        const scamButton = document.getElementById("markScam");
        const safeButton = document.getElementById("markSafe");

        if (backButton) backButton.textContent = `← ${mobileLabel("back", "Back")}`;
        if (emailBody) emailBody.textContent = mobileLabel("loadingEmail", "Loading email...");
        if (readAloudButton) readAloudButton.textContent = mobileLabel("readAloud", "Read aloud");
        if (scamButton) scamButton.textContent = mobileLabel("fake", "Fake");
        if (safeButton) safeButton.textContent = mobileLabel("real", "Real");
    }

    if (type === "sms") {
        const backButton = document.querySelector(".back-button");
        const smsBody = document.getElementById("smsBody");
        const scamButton = document.getElementById("markScam");
        const safeButton = document.getElementById("markSafe");

        if (backButton) backButton.textContent = `← ${mobileLabel("back", "Back")}`;
        if (smsBody) smsBody.textContent = mobileLabel("smsPlaceholder", "SMS content goes here...");
        if (scamButton) scamButton.textContent = mobileLabel("fake", "Fake");
        if (safeButton) safeButton.textContent = mobileLabel("real", "Real");
    }

    if (type === "call") {
        const callType = document.querySelector(".call-type");
        const caller = document.getElementById("call-caller");
        const controls = document.querySelectorAll(".call-controls .call-btn");
        const transcript = document.getElementById("call-transcript");
        const scamButton = document.getElementById("markScam");
        const safeButton = document.getElementById("markSafe");

        if (callType) callType.textContent = mobileLabel("audioCall", "Audio Call");
        if (caller) caller.textContent = mobileLabel("unknownCaller", "Unknown Caller");
        if (controls[0]) controls[0].textContent = mobileLabel("mute", "Mute");
        if (controls[1]) controls[1].textContent = mobileLabel("end", "End");
        if (controls[2]) controls[2].textContent = mobileLabel("speaker", "Speaker");
        if (transcript) transcript.textContent = mobileLabel("callTranscriptPlaceholder", "Call transcript will appear here...");
        if (scamButton) scamButton.textContent = mobileLabel("reportScamCall", "Report Scam Call");
        if (safeButton) safeButton.textContent = mobileLabel("looksSafe", "Looks Safe");
    }

    if (type === "web") {
        const backButton = document.querySelector(".web-toolbar .back-btn");
        const browserTitle = document.querySelector(".web-browser-title");
        const scamButton = document.getElementById("markScam");
        const safeButton = document.getElementById("markSafe");
        const footer = document.querySelector(".fake-footer");
        const searchInput = document.getElementById("fakeSearchInput");

        if (backButton) backButton.textContent = `← ${mobileLabel("back", "Back")}`;
        if (browserTitle) browserTitle.textContent = mobileLabel("chrome", "Chrome");
        if (scamButton) scamButton.textContent = mobileLabel("fake", "Fake");
        if (safeButton) safeButton.textContent = mobileLabel("real", "Real");
        if (searchInput) searchInput.value = mobileLabel("fakeSearchValue", "how to make money fast");
        if (footer) footer.textContent = mobileLabel("googleFooter", "Google © 2025");
    }
}

let currentMessage = "";
let currentType = "";
let currentDifficulty = "";
let scenarioLoadTime = null;

const ScenarioEngine = {
    endpoints: {
        email: "/generate-email",
        sms: "/generate-sms",
        call: "/generate-call",
        web: "/generate-web"
    },

    async load(type) {
        currentType = type;

        const scenarioBody = document.getElementById("scenarioBody");
        const appsGrid = document.querySelector(".apps");
        if (!scenarioBody || !appsGrid) return;

        scenarioBody.innerHTML = `<p class='loading'>${mobileLabel("loadingScenario", "Loading scenario...")}</p>`;
        appsGrid.style.display = "none";

        // Load snippet HTML template
        const htmlResp = await fetch(`/static/snippets/${type}.html`);
        scenarioBody.innerHTML = await htmlResp.text();
        applySnippetTranslations(type);

        // Pick appropriate endpoint
        const endpoint = this.endpoints[type];
        if (!endpoint) return;

        // Fetch scenario from backend
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme: "SilverShield training" })
        });

        const data = await res.json();
        if (!data.success) {
            scenarioBody.innerHTML = `<p>${mobileLabel("errorLoadingScenario", "Error loading scenario.")}</p>`;
            console.error("Scenario error:", data.error);
            return;
        }

        currentDifficulty = data.difficulty;

        const diffLabel = document.getElementById("difficultyLabel");
        if (diffLabel) diffLabel.innerText = `${mobileLabel("level", "Level")}: ${currentDifficulty}`;

        // Record time scenario was displayed
        scenarioLoadTime = Date.now();

        // Map returned data to scenario object for UI
        let sc = null;
        if (type === "email") sc = { email_html: data.email };
        else if (type === "sms") sc = data.sms;
        else if (type === "call") sc = data.call;
        else if (type === "web") sc = data.web;

        this.fill(type, sc);

        // After filling UI, if email was loaded, attempt to preload TTS
        if (type === 'email' && currentMessage) {
            try {
                const tmp = document.createElement('div');
                tmp.innerHTML = currentMessage;
                const plain = (tmp.textContent || tmp.innerText || '').replace(/\s+/g,' ').trim();
                if (window.preloadTTS) {
                    // fire-and-forget preload (internal dedupe prevents duplicates)
                    try { window.preloadTTS(plain, { lang: mobileTtsLang, slow: false }); } catch(e) { /* ignore */ }
                }
            } catch (e) { console.warn('Preload TTS failed', e); }
        }

        // Hook up scam/safe buttons
        const scamBtn = document.getElementById("markScam");
        const safeBtn = document.getElementById("markSafe");
        const readAloudMobile = document.getElementById('readAloudMobile');

        if (scamBtn) scamBtn.onclick = () => { if (window.stopTTS) try { window.stopTTS(); } catch(e){}; analyzeChoice("scam"); };
        if (safeBtn) safeBtn.onclick = () => { if (window.stopTTS) try { window.stopTTS(); } catch(e){}; analyzeChoice("not_scam"); };

        if (readAloudMobile) {
            readAloudMobile.onclick = async () => {
                try {
                    const tmp = document.createElement('div'); tmp.innerHTML = currentMessage;
                    const plain = (tmp.textContent || tmp.innerText || '').replace(/\s+/g,' ').trim();
                    if (window.playPreloaded) {
                        const played = await window.playPreloaded(plain);
                        if (played) return;
                    }
                    if (window.speak) await window.speak(plain, { lang: mobileTtsLang, slow: false });
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
            document.getElementById("call-caller").innerText = sc.caller_name || mobileLabel("unknownCaller", "Unknown Caller");
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
            const adBox = document.createElement("div");
            adBox.classList.add("ad-box");
            adBox.innerHTML = `
                <div class="ad-title">${ad.title || mobileLabel("sponsored", "Sponsored")}</div>
                <div class="ad-url">${ad.url}</div>
                <div class="ad-snippet">${ad.snippet}</div>
                <div class="ad-label">${mobileLabel("sponsored", "Sponsored")}</div>
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
    heading.innerText = sc.results[0].title || mobileLabel("searchResults", "Search Results");
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
    heading.innerText = mobileLabel("searchResults", "Search Results");
    container.appendChild(heading);
}

// -----------------------------
//  pagination
// -----------------------------
if (sc.pagination) {
    const nav = document.createElement("div");
    nav.classList.add("pagination-nav");

    nav.innerHTML = `
        <button id="nextPageBtn">${sc.pagination.next_page_label || mobileLabel("nextPage", "Next >")}</button>
    `;

    container.appendChild(nav);

    document.getElementById("nextPageBtn").onclick = () => {
        ScenarioEngine.load("web");
    };
}

currentMessage = JSON.stringify(sc);
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
                message: currentMessage,
                time_spent_seconds: timeSpent
            })
        });

        const data = await response.json();

        if (!data.success) {
            alert(mobileLabel("errorAnalyzingResponse", "Error analyzing response."));
            return;
        }

        alert(
            data.feedback.feedback +
            `\n\n(${mobileLabel("currentDifficulty", "Current difficulty")}: ${data.difficulty_now})`
        );

        // Reload next scenario automatically
        ScenarioEngine.load(currentType);

    } catch (err) {
        console.error("analyzeChoice() error:", err);
        alert(mobileLabel("serverErrorAnalyzingChoice", "Server error analyzing choice."));
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
