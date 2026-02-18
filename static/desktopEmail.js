/*************************
      Email Functions
**************************/
let lastGeneratedEmail = "";

document.addEventListener("DOMContentLoaded", () => {
    const emailIcon = document.querySelector(".icon.email");
    const emailWindow = document.getElementById("emailWindow");
    const emailContent = document.getElementById("emailContent");

    const rfContainer = document.getElementById("emailButtons");
    const realBtn = document.getElementById("realBtn");
    const fakeBtn = document.getElementById("fakeBtn");

    /* Loading AI generated Email */
    async function loadEmail()
    {
        // Stop any playing audio when loading a new email
        if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
        emailContent.textContent = "Generating email...";
        rfContainer.style.display = "none";

        try
        {
            const response = await fetch("/generate-email", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({theme: "Email Scam Training"})
            });

            const data = await response.json();

            if (data.success && data.email)
            {
                emailContent.innerHTML = data.email;
                lastGeneratedEmail = data.email;
                rfContainer.style.display = "block";

                // Preload TTS immediately to reduce play delay
                try {
                    const tmp = document.createElement('div');
                    tmp.innerHTML = lastGeneratedEmail;
                    const plain = tmp.textContent || tmp.innerText || '';
                    if (window.preloadTTS) {
                        window.preloadTTS(plain, { lang: 'en', slow: false }).catch && window.preloadTTS(plain, { lang: 'en', slow: false });
                    }
                } catch (e) { console.warn('Preload TTS failed', e); }
            }
            else
            {
                emailContent.textContent = "Error generating email.";
            }

        }
        catch (err)
        {
            console.error("Email load error:", err);
            emailContent.textContent = "Server error.";
        }
    }

    /* Analyzing User Choice */
    async function sendUserAnswer(choice)
    {
        // stop audio when user makes a choice
        if (window.stopTTS) try { window.stopTTS(); } catch (e) {}

        if(!lastGeneratedEmail)
        {
            console.warn("No generated email stored for analysis.");
            return showNotification(false, "No email loaded to analyze.", "email");
        }

        try
        {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    user_choice: choice,
                    message: lastGeneratedEmail
                })
            });

            const result = await response.json();

            if (!result.success)
            {
                return showNotification(false, "Error analyzing response.", "email");
            }

            const correct = result.feedback.correct;
            const feedback = result.feedback.feedback;
            const difficulty = result.difficulty_now;

            showNotification(
                correct,
                `${feedback} (Difficulty: ${difficulty})`,
                "email"
            );

            loadEmail();
        }
        catch (err)
        {
            console.error("Email analysis error:", err);
            showNotification(false, "Server error analyzing response.", "email");
        }
    }

    /* Event Listeners */
    if (emailIcon && emailWindow)
    {
        emailIcon.addEventListener("click", () => {
            // stop any playing audio and open the window
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            emailWindow.style.display = "block";
            loadEmail();
        });
    }

    /* Read Aloud button */
    const readAloudBtn = document.getElementById('readAloudBtn');
    if (readAloudBtn && !readAloudBtn.dataset.bound) {
        readAloudBtn.dataset.bound = true;
        readAloudBtn.addEventListener('click', async () => {
            if (!lastGeneratedEmail) {
                return showNotification(false, 'No email loaded to read.', 'email');
            }

            // Convert HTML to plain text for TTS
            const tmp = document.createElement('div');
            tmp.innerHTML = lastGeneratedEmail;
            const plain = tmp.textContent || tmp.innerText || '';

            try {
                // If a preloaded audio matches, play it for near-instant playback
                if (window.playPreloaded) {
                    const played = window.playPreloaded(plain);
                    if (played) return;
                }

                if (window.speak) {
                    await window.speak(plain, { lang: 'en', slow: false });
                } else {
                    console.warn('TTS helper not available.');
                }
            } catch (err) {
                console.error('TTS playback error:', err);
            }
        });
    }

    /* Real and Fake button */
    if (realBtn && !realBtn.dataset.bound) {
        realBtn.dataset.bound = true;
        realBtn.addEventListener("click", () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            sendUserAnswer("real");
        });
    }

    if (fakeBtn && !fakeBtn.dataset.bound) {
        fakeBtn.dataset.bound = true;
        fakeBtn.addEventListener("click", () => {
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            sendUserAnswer("fake");
        });
    }

    /* Close Popup */
    document.querySelectorAll(".popup-close").forEach(btn =>
        btn.addEventListener("click", () => {
            // stop audio when popup is closed
            if (window.stopTTS) try { window.stopTTS(); } catch (e) {}
            btn.closest(".popup").style.display = "none"
        })
    );
});
