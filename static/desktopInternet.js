/*************************
    Internet Functions
**************************/

let currentWebsiteHTML = "";
let currentWebsiteType = "";
let currentInternetDifficulty = "";
let websiteLoadTime = null;
let currentInternetSpeechText = "";

const internetContent = document.getElementById("internetContent");
const internetButtons = document.getElementById("internetButtons");
const internetRealBtn = document.getElementById("internetRealBtn");
const internetFakeBtn = document.getElementById("internetFakeBtn");
const internetReadAloudBtn = document.getElementById("internetReadAloudBtn");

function stopCurrentTTS() {
    if (typeof globalThis.stopTTS === "function") {
        globalThis.stopTTS();
    }
}

function htmlToPlainText(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html || "";
    return (tmp.textContent || tmp.innerText || "").replaceAll(/\s+/g, " ").trim();
}


/* ========================================
   Load Search Results (List Mode)
======================================== */
async function generateDesktopFakeSites() {
    if (!internetContent) return;

    stopCurrentTTS();

    internetContent.innerHTML = "<p>Loading search results...</p>";
    internetButtons.style.display = "none";   // hide buttons here

    try {
        const response = await fetch("/api/generate_sites", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ mode: "list" })
        });

        const data = await response.json();

        if (!data.success || !data.results) {
            internetContent.innerHTML = "<p>Error loading search results.</p>";
            return;
        }

        internetContent.innerHTML = "";

        data.results.forEach(site => {
            internetContent.innerHTML += `
                <div class="search-results site-link"
                     data-title="${site.title}"
                     data-url="${site.url}"
                     data-type="${site.site_type}">
                    <div class="search-result-title">${site.title}</div>
                    <div class="search-result-link">${site.url}</div>
                    <div class="search-result-description">${site.description}</div>
                </div>
            `;
        });

        document.querySelectorAll(".site-link").forEach(link => {
            link.addEventListener("click", () => openDesktopWebsite(link));
        });

        currentInternetSpeechText = data.results
            .map(site => `${site.title}. ${site.description}.`) 
            .join(" ");

        if (typeof globalThis.preloadTTS === "function" && currentInternetSpeechText) {
            globalThis.preloadTTS(currentInternetSpeechText, { lang: "en", slow: false }).catch(() => {});
        }

    } catch (err) {
        console.error(err);
        internetContent.innerHTML = "<p>Error loading search results.</p>";
    }
}


/* ========================================
   Open a Website (Open Mode)
======================================== */
async function openDesktopWebsite(linkElement) {
    const title = linkElement.dataset.title;
    const url = linkElement.dataset.url;
    const type = linkElement.dataset.type;

    internetContent.innerHTML = "<p>Loading website...</p>";
    stopCurrentTTS();

    try {
        const response = await fetch("/api/generate_sites", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                mode: "open",
                title,
                url,
                site_type: type
            })
        });

        const data = await response.json();

        if (!data.success) {
            internetContent.innerHTML = "<p>Error loading website.</p>";
            return;
        }

        // Save current website info for analysis
        currentWebsiteHTML = data.html;
        currentWebsiteType = type;
        currentInternetDifficulty = data.difficulty;
        currentInternetSpeechText = `${title}. ${url}. ${htmlToPlainText(data.html)}`;

        // Render website
        internetContent.innerHTML = `
            <div class="fake-site">
              <h2>${title}</h2>
              <p class="fake-url">${url}</p>

              <div class="fake-body">${data.html}</div>
            </div>
        `;

        // Record time website was displayed
        websiteLoadTime = Date.now();

        // Show the REAL/FAKE buttons
        internetButtons.style.display = "flex";

        if (typeof globalThis.preloadTTS === "function" && currentInternetSpeechText) {
            globalThis.preloadTTS(currentInternetSpeechText, { lang: "en", slow: false }).catch(() => {});
        }

    } catch (err) {
        console.error(err);
        internetContent.innerHTML = "<p>Error loading website.</p>";
    }
}


/* ========================================
   Analyze Website Response
======================================== */
async function analyzeDesktopWebsite(choice) {
    stopCurrentTTS();

    if (!currentWebsiteHTML || !currentWebsiteType) {
        showNotification(false, "Website not loaded properly.", "internet");
        return;
    }

    // Calculate time spent on website (in seconds)
    const timeSpent = websiteLoadTime ? Math.round((Date.now() - websiteLoadTime) / 1000) : 0;

    try {
        const response = await fetch("/api/analyze_website", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                user_choice: choice,
                ai_context: currentWebsiteHTML,
                site_type: currentWebsiteType,
                time_spent_seconds: timeSpent
            })
        });

        const data = await response.json();

        if (!data.success) {
            showNotification(false, "Error analyzing website.", "internet");
            return;
        }

        const fb = data.feedback;
        const message = `${fb.explanation} (Difficulty: ${data.difficulty_now})`;

        showNotification(fb.correct, message, "internet");

    } catch (err) {
        console.error(err);
        showNotification(false, "Server error analyzing website.", "internet");
    }
}


/* ========================================
   Button Event Listeners
======================================== */
if (internetRealBtn) {
    internetRealBtn.addEventListener("click", () =>
        analyzeDesktopWebsite("real")
    );
}

if (internetFakeBtn) {
    internetFakeBtn.addEventListener("click", () =>
        analyzeDesktopWebsite("fake")
    );
}

const internetVoiceBtn = document.getElementById("internetVoiceBtn");
if (internetVoiceBtn && window.startVoiceAnswer) {
    internetVoiceBtn.addEventListener("click", () => {
        stopCurrentTTS();
        window.startVoiceAnswer(
            internetVoiceBtn,
            () => analyzeDesktopWebsite("real"),
            () => analyzeDesktopWebsite("fake")
        );
    });
}

if (internetReadAloudBtn) {
    internetReadAloudBtn.addEventListener("click", async () => {
        if (!currentInternetSpeechText) {
            return;
        }

        try {
            if (typeof globalThis.playPreloaded === "function") {
                const played = await globalThis.playPreloaded(currentInternetSpeechText);
                if (played) return;
            }

            if (typeof globalThis.speak === "function") {
                await globalThis.speak(currentInternetSpeechText, { lang: "en", slow: false });
            }
        } catch (err) {
            console.error("Internet TTS playback error:", err);
        }
    });
}


/* ========================================
   Internet Icon Opens the Module
======================================== */
document.addEventListener("DOMContentLoaded", () => {
    const internetIcon = document.querySelector(".icon.internet");
    const internetWindow = document.getElementById("internetWindow");

    if (internetIcon && internetWindow) {
        internetIcon.addEventListener("click", () => {
            internetWindow.style.display = "block";
            generateDesktopFakeSites();
        });
    }
});
