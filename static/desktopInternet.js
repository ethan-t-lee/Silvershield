/*************************
    Internet Functions
**************************/

let currentWebsiteHTML = "";
let currentWebsiteType = "";
let currentInternetDifficulty = "";

const internetContent = document.getElementById("internetContent");
const internetButtons = document.getElementById("internetButtons");
const internetRealBtn = document.getElementById("internetRealBtn");
const internetFakeBtn = document.getElementById("internetFakeBtn");


/* ========================================
   Load Search Results (List Mode)
======================================== */
async function generateDesktopFakeSites() {
    if (!internetContent) return;

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

        // Render website
        internetContent.innerHTML = `
            <div class="fake-site">
              <h2>${title}</h2>
              <p class="fake-url">${url}</p>

              <div class="fake-body">${data.html}</div>
            </div>
        `;

        // Show the REAL/FAKE buttons
        internetButtons.style.display = "flex";

    } catch (err) {
        console.error(err);
        internetContent.innerHTML = "<p>Error loading website.</p>";
    }
}


/* ========================================
   Analyze Website Response
======================================== */
async function analyzeDesktopWebsite(choice) {
    if (!currentWebsiteHTML || !currentWebsiteType) {
        showNotification(false, "Website not loaded properly.", "internet");
        return;
    }

    try {
        const response = await fetch("/api/analyze_website", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                user_choice: choice,
                ai_context: currentWebsiteHTML,
                site_type: currentWebsiteType
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
