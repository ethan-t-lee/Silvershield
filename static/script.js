/*************************
      Mobile Scenario Engine - Email, Web, SMS, Call apps
**************************/
let currentMessage = "";
let currentType = "";
let currentDifficulty = "";
let currentExpectedLabel = "";
let scenarioLoadTime = null;
let currentWebQuery = "";
let currentWebResults = null;
const mobileLabels = globalThis.mobileLabels || {};
const mobileLabel = (key, fallback) => mobileLabels[key] || fallback;

function applyMobileTranslations() {
    const backLabel = mobileLabel("back", "Back");
    const readAloudLabel = mobileLabel("readAloud", "Read Aloud");
    const realLabel = mobileLabel("real", "REAL");
    const fakeLabel = mobileLabel("fake", "FAKE");
    const speakLabel = mobileLabel("speak", "Speak");
    const muteLabel = mobileLabel("mute", "Mute");
    const endLabel = mobileLabel("end", "End");
    const speakerLabel = mobileLabel("speaker", "Speaker");
    const reportScamCallLabel = mobileLabel("reportScamCall", fakeLabel);
    const looksSafeLabel = mobileLabel("looksSafe", realLabel);

    const setButtonLabel = (button, text) => {
        if (!button) return;
        const label = button.querySelector(".btn-label");
        if (label) {
            label.textContent = text;
        } else {
            button.textContent = text;
        }
    };

    document.querySelectorAll(".back-btn, .back-button").forEach(btn => {
        setButtonLabel(btn, backLabel);
    });

    const readBtn = document.getElementById("readAloudMobile");
    if (readBtn) {
        setButtonLabel(readBtn, document.querySelector(".call-app") ? speakerLabel : readAloudLabel);
    }

    document.querySelectorAll(".voice-answer-btn").forEach(btn => {
        btn.title = mobileLabel("sayRealOrFake", "Say 'real' or 'fake'.");
    });

    const safeBtn = document.getElementById("markSafe");
    if (safeBtn) {
        setButtonLabel(safeBtn, document.querySelector(".call-app") ? looksSafeLabel : realLabel);
    }

    const scamBtn = document.getElementById("markScam");
    if (scamBtn) {
        setButtonLabel(scamBtn, document.querySelector(".call-app") ? reportScamCallLabel : fakeLabel);
    }

    const voiceBtn = document.getElementById("voiceAnswerBtn");
    if (voiceBtn) setButtonLabel(voiceBtn, speakLabel);

    const callButtons = document.querySelectorAll(".call-controls .call-btn");
    if (callButtons[0]) setButtonLabel(callButtons[0], muteLabel);
    if (callButtons[1]) setButtonLabel(callButtons[1], endLabel);

    const emailSearchPill = document.querySelector(".gmail-mobile-search-pill");
    if (emailSearchPill) emailSearchPill.textContent = mobileLabel("searchInMail", "Search in mail");

    const mailbox = document.querySelector(".gmail-mobile-mailbox");
    if (mailbox) mailbox.textContent = mobileLabel("primaryInbox", "Primary Inbox");

    const unread = document.querySelector(".gmail-mobile-unread");
    if (unread) unread.textContent = mobileLabel("oneNew", "1 new");

    const emailBody = document.getElementById("emailBody");
    if (emailBody && emailBody.textContent.trim() === "Loading email...") {
        emailBody.textContent = mobileLabel("loadingEmail", "Loading email...");
    }

    const smsSubtitle = document.querySelector(".ios-contact-subtitle");
    if (smsSubtitle) smsSubtitle.textContent = mobileLabel("textMessage", "Text Message");

    const smsContactName = document.getElementById("smsContactName");
    if (smsContactName && smsContactName.textContent.trim() === "Bank Alerts") {
        smsContactName.textContent = mobileLabel("bankAlerts", "Bank Alerts");
    }

    const smsTime = document.getElementById("smsTime");
    if (smsTime && smsTime.textContent.trim() === "Today 12:04 PM") {
        smsTime.textContent = mobileLabel("todayTime", "Today 12:04 PM");
    }

    const smsBody = document.getElementById("smsBody");
    if (smsBody && smsBody.textContent.trim() === "SMS content goes here...") {
        smsBody.textContent = mobileLabel("smsPlaceholder", "SMS content goes here...");
    }

    const composePill = document.querySelector(".compose-pill");
    if (composePill) composePill.textContent = mobileLabel("iMessage", "iMessage");

    const webInput = document.getElementById("fakeSearchInput");
    if (webInput) webInput.placeholder = mobileLabel("searchOrTypeWebAddress", "Search or type web address");

    const chips = document.querySelectorAll(".chrome-mobile-chip");
    if (chips[0]) chips[0].textContent = mobileLabel("all", "All");
    if (chips[1]) chips[1].textContent = mobileLabel("news", "News");
    if (chips[2]) chips[2].textContent = mobileLabel("images", "Images");

    const mobileSearchBtn = document.getElementById("mobileSearchBtn");
    if (mobileSearchBtn) setButtonLabel(mobileSearchBtn, mobileLabel("go", "Go"));

    const resultsBtn = document.getElementById("webBackToResults");
    if (resultsBtn) resultsBtn.textContent = mobileLabel("results", "Results");

    const webStatus = document.getElementById("webStatusText");
    if (webStatus && webStatus.textContent.includes("Search a topic")) {
        webStatus.textContent = mobileLabel("searchTopicInspect", "Search a topic, open a result, and inspect the site before choosing REAL or FAKE.");
    }

    const footer = document.querySelector(".fake-footer.chrome-mobile-footer");
    if (footer) footer.textContent = mobileLabel("googleFooter", "Google © 2025");

    const callType = document.querySelector(".call-type");
    if (callType) callType.textContent = mobileLabel("audioCall", "Audio Call");

    const callCaller = document.getElementById("call-caller");
    if (callCaller && callCaller.textContent.trim() === "Unknown Caller") {
        callCaller.textContent = mobileLabel("unknownCaller", "Unknown Caller");
    }

    const transcript = document.getElementById("call-transcript");
    if (transcript && transcript.textContent.trim() === "Call transcript will appear here...") {
        transcript.textContent = mobileLabel("callTranscriptPlaceholder", "Call transcript will appear here...");
    }
}

function buildWebSpeechText(sc) {
    if (!sc) return "";

    const adText = (sc.ads || [])
        .map(ad => `${ad.title || mobileLabel("sponsoredResult", "Sponsored result")}. ${ad.snippet || ""}`)
        .join(" ");

    const resultText = (sc.results || [])
        .map(result => `${result.title || mobileLabel("result", "Result")}. ${result.snippet || ""}`)
        .join(" ");

    return `${adText} ${resultText}`.replace(/\s+/g, " ").trim();
}

function htmlToPlainText(html) {
    const temp = document.createElement("div");
    temp.innerHTML = html || "";
    return (temp.textContent || temp.innerText || "").replace(/\s+/g, " ").trim();
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

        scenarioBody.innerHTML = `<p class='loading'>${mobileLabel("loadingScenario", "Loading scenario...")}</p>`;
        appsGrid.style.display = "none";

        // Load snippet HTML template
        const htmlResp = await fetch(`/static/snippets/${type}.html`);
        scenarioBody.innerHTML = await htmlResp.text();
        applyMobileTranslations();

        if (type === "web") {
            this.setupWebSearchUI();
            await this.loadWebSearch((document.getElementById("fakeSearchInput")?.value || "bank account security tips").trim());
            return;
        }

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

    setupWebSearchUI() {
        const webActions = document.getElementById("webActions");
        const searchInput = document.getElementById("fakeSearchInput");
        const searchBtn = document.getElementById("mobileSearchBtn");
        const resultsBtn = document.getElementById("webBackToResults");
        const statusText = document.getElementById("webStatusText");

        if (webActions) webActions.style.display = "none";
        if (resultsBtn) resultsBtn.style.display = "none";
        if (statusText) {
            statusText.textContent = mobileLabel("searchTopicInspect", "Search a topic, open a result, and inspect the site before choosing REAL or FAKE.");
        }

        if (searchBtn && !searchBtn.dataset.bound) {
            searchBtn.dataset.bound = "true";
            searchBtn.onclick = () => this.loadWebSearch(searchInput?.value || "bank account security tips");
        }

        if (searchInput && !searchInput.dataset.bound) {
            searchInput.dataset.bound = "true";
            searchInput.addEventListener("keydown", event => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    this.loadWebSearch(searchInput.value || "bank account security tips");
                }
            });
        }

        if (resultsBtn && !resultsBtn.dataset.bound) {
            resultsBtn.dataset.bound = "true";
            resultsBtn.onclick = () => {
                if (currentWebResults) {
                    this.renderMobileWebResults(currentWebResults);
                }
            };
        }
    },

    async loadWebSearch(query) {
        const normalizedQuery = (query || "bank account security tips").trim() || "bank account security tips";
        const container = document.getElementById("web-content");
        const statusText = document.getElementById("webStatusText");
        const webActions = document.getElementById("webActions");
        const resultsBtn = document.getElementById("webBackToResults");
        const searchInput = document.getElementById("fakeSearchInput");

        currentType = "web";
        currentWebQuery = normalizedQuery;
        currentExpectedLabel = "";
        currentMessage = "";
        scenarioLoadTime = Date.now();

        if (searchInput) searchInput.value = normalizedQuery;
        if (webActions) webActions.style.display = "none";
        if (resultsBtn) resultsBtn.style.display = "none";
        if (statusText) statusText.textContent = `${mobileLabel("searchingFor", "Searching for")} “${normalizedQuery}”...`;
        if (container) container.innerHTML = `<p class='loading'>${mobileLabel("loadingSearchResults", "Loading search results...")}</p>`;

        try {
            const response = await fetch("/generate-web", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode: "search", query: normalizedQuery })
            });

            const data = await response.json();
            if (!data.success || !data.web) {
                throw new Error(data.error || "Search results failed to load.");
            }

            currentDifficulty = data.difficulty;
            currentWebResults = data.web;
            currentMessage = buildWebSpeechText(data.web);
            this.renderMobileWebResults(data.web);

            if (window.preloadTTS && currentMessage) {
                const lang = (window.getTTSLang && window.getTTSLang()) || "en";
                try { window.preloadTTS(currentMessage, { lang, slow: false }); } catch (e) { /* ignore */ }
            }
        } catch (err) {
            console.error("loadWebSearch error:", err);
            if (container) container.innerHTML = `<p>${mobileLabel("errorLoadingSearchResults", "Error loading search results.")}</p>`;
            if (statusText) statusText.textContent = mobileLabel("unableToOpenResult", "Unable to open that result. Please try another one.");
        }
    },

    async openWebResult(site) {
        const container = document.getElementById("web-content");
        const statusText = document.getElementById("webStatusText");
        const webActions = document.getElementById("webActions");
        const resultsBtn = document.getElementById("webBackToResults");
        const searchInput = document.getElementById("fakeSearchInput");

        if (!site || !container) return;

        container.innerHTML = `<p class='loading'>${mobileLabel("loadingWebsite", "Loading website...")}</p>`;
        if (statusText) statusText.textContent = mobileLabel("loadingSelectedWebsite", "Loading the selected website...");

        try {
            const response = await fetch("/generate-web", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mode: "open",
                    query: currentWebQuery,
                    title: site.title,
                    url: site.url,
                    site_type: site.site_type
                })
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || "Unable to open site.");
            }

            currentExpectedLabel = site.site_type === "phishing" ? "scam" : "not_scam";
            currentMessage = `${site.title}. ${site.url}. ${htmlToPlainText(data.html)}`;
            scenarioLoadTime = Date.now();

            if (searchInput) searchInput.value = site.url;
            if (resultsBtn) resultsBtn.style.display = "inline-flex";
            if (webActions) webActions.style.display = "grid";
            if (statusText) {
                statusText.textContent = mobileLabel("inspectWebsiteCarefully", "Inspect the website carefully, then choose REAL or FAKE.");
            }

            container.innerHTML = `
                <div class="mobile-site-page">
                    <div class="mobile-site-header">
                        <div class="search-result-title">${site.title}</div>
                        <div class="search-result-link">${site.url}</div>
                    </div>
                    <div class="web-content-body">${data.html}</div>
                </div>
            `;

            if (window.preloadTTS && currentMessage) {
                const lang = (window.getTTSLang && window.getTTSLang()) || "en";
                try { window.preloadTTS(currentMessage, { lang, slow: false }); } catch (e) { /* ignore */ }
            }
        } catch (err) {
            console.error("openWebResult error:", err);
            container.innerHTML = `<p>${mobileLabel("errorLoadingWebsite", "Error loading website.")}</p>`;
            if (statusText) statusText.textContent = mobileLabel("unableToOpenResult", "Unable to open that result. Please try another one.");
        }
    },

    renderMobileWebResults(sc) {
        const container = document.getElementById("web-content");
        const statusText = document.getElementById("webStatusText");
        const webActions = document.getElementById("webActions");
        const resultsBtn = document.getElementById("webBackToResults");
        const pagination = document.getElementById("pagination");
        const searchInput = document.getElementById("fakeSearchInput");

        if (!container || !sc) return;

        currentExpectedLabel = "";
        currentMessage = buildWebSpeechText(sc);
        if (webActions) webActions.style.display = "none";
        if (resultsBtn) resultsBtn.style.display = "none";
        if (pagination) pagination.innerHTML = "";
        if (searchInput) searchInput.value = currentWebQuery;
        if (statusText) {
            statusText.textContent = `${mobileLabel("showingResultsFor", "Showing results for")} “${currentWebQuery}”. ${mobileLabel("openSiteInspect", "Open a site and inspect it before answering.")}`;
        }

        container.innerHTML = "";

        const stats = document.createElement("div");
        stats.className = "search-results-stats";
        stats.textContent = `${mobileLabel("about", "About")} ${((sc.results || []).length + (sc.ads || []).length) * 142000} ${mobileLabel("resultsWord", "results")} (0.38 ${mobileLabel("seconds", "seconds")})`;
        container.appendChild(stats);

        const renderCard = (item, sponsored = false) => {
            const card = document.createElement("button");
            card.type = "button";
            card.className = `search-result ${sponsored ? "sponsored" : ""}`;
            card.innerHTML = `
                ${sponsored ? `<div class="sponsored-label">${mobileLabel("sponsored", "Sponsored")}</div>` : ''}
                <div class="search-result-title">${item.title}</div>
                <div class="search-result-link">${item.url}</div>
                <div class="search-result-snippet">${item.snippet}</div>
            `;
            card.onclick = () => this.openWebResult(item);
            container.appendChild(card);
        };

        (sc.ads || []).forEach(ad => renderCard(ad, true));
        (sc.results || []).forEach(result => renderCard(result, false));

        if (pagination) {
            pagination.innerHTML = `<button id="nextPageBtn">${sc.pagination?.next_page_label || mobileLabel("nextPage", "Next >")}</button>`;
            const nextPageBtn = document.getElementById("nextPageBtn");
            if (nextPageBtn) {
                nextPageBtn.onclick = () => this.loadWebSearch(currentWebQuery);
            }
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
            document.getElementById("smsTime").innerText = sc.time || mobileLabel("todayTime", "Today 12:04 PM");

            const smsContactName = document.getElementById("smsContactName");
            const smsAvatar = document.getElementById("smsAvatar");
            const senderLabel = sc.sender_name || mobileLabel("bankAlerts", "Bank Alerts");

            if (smsContactName) smsContactName.innerText = senderLabel;
            if (smsAvatar) smsAvatar.innerText = senderLabel.charAt(0).toUpperCase();

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
            this.renderMobileWebResults(sc);
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
        if (currentType === "web" && !currentExpectedLabel) {
            alert(mobileLabel("openResultFirst", "Open a search result and inspect the site before answering."));
            return;
        }

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
