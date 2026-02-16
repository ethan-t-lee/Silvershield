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
            emailWindow.style.display = "block";
            loadEmail();
        });
    }

    /* Real and Fake button */
    if (realBtn && !realBtn.dataset.bound) {
        realBtn.dataset.bound = true;
        realBtn.addEventListener("click", () => sendUserAnswer("real"));
    }

    if (fakeBtn && !fakeBtn.dataset.bound) {
        fakeBtn.dataset.bound = true;
        fakeBtn.addEventListener("click", () => sendUserAnswer("fake"));
    }

    /* Close Popup */
    document.querySelectorAll(".popup-close").forEach(btn =>
        btn.addEventListener("click", () =>
            btn.closest(".popup").style.display = "none"
        )
    );
});
