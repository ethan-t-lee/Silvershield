function t(s) {
    return (window.roleplayI18n && window.roleplayI18n[s]) || s;
}

const scenarios = {
    bank_fraud: {
        callerName: "Bank Fraud Dept.",
        callerNumber: "(800) 555-2319",
        avatar: "B",
        hint: "Tip: Real banks do not ask for one-time codes, PINs, or full card details over the phone.",
        difficulty: 1,
        criticalIndicatorsTotal: 3,
        start: "node1",
        nodes: {
            node1: {
                prompt_key: "opening",
                choices: [
                    { text: "Give them your card number", next: "node2_bad" },
                    { text: "Ask them to verify who they are", next: "node2_verify" },
                    { text: "Hang up and call the bank directly", next: "end_best" },
                    { text: "Tell them to call later", next: "node2_later" }
                ]
            },
            node2_bad: {
                prompt_key: "ask_for_code",
                choices: [
                    { text: "Give the code", next: "end_unsafe" },
                    { text: "Refuse and ask why they need it", next: "node3_pressure" },
                    { text: "Hang up", next: "end_recovery" }
                ]
            },
            node2_verify: {
                prompt_key: "push_for_account_number",
                choices: [
                    { text: "Give account number", next: "node2_bad" },
                    { text: "Ask for their name and department", next: "node3_title" },
                    { text: "Hang up and call the bank directly", next: "end_best" }
                ]
            },
            node2_later: {
                prompt_key: "urgency_if_call_later",
                choices: [
                    { text: "Stay on the call", next: "end_risky" },
                    { text: "Hang up and call the bank directly", next: "end_best" }
                ]
            },
            node3_pressure: {
                prompt_key: "freeze_account_pressure",
                choices: [
                    { text: "Give the code because it sounds urgent", next: "end_unsafe" },
                    { text: "Hang up and call the bank directly", next: "end_best" }
                ]
            },
            node3_title: {
                prompt_key: "fake_name_and_department",
                choices: [
                    { text: "Continue the call", next: "end_risky" },
                    { text: "Hang up and call the bank directly", next: "end_best" }
                ]
            },
            end_unsafe: {
                ending: true,
                title: "Unsafe choice",
                feedback: "The caller now has enough information to try to access your account. Real banks do not ask for one-time codes or security codes over the phone like this.",
                consequence: "Your account could be compromised or drained."
            },
            end_recovery: {
                ending: true,
                title: "Better recovery choice",
                feedback: "Hanging up stopped the scam from continuing. Even if you already shared some information, ending the call was safer than continuing.",
                consequence: "You reduced the risk, but some information may already have been exposed."
            },
            end_risky: {
                ending: true,
                title: "Risky choice",
                feedback: "Scammers often sound professional and use urgency to pressure people into trusting them. A name or title is not proof they are real.",
                consequence: "Continuing the call could lead to stolen information."
            },
            end_best: {
                ending: true,
                title: "Best choice",
                feedback: "Excellent decision. Hanging up and calling the bank directly using the number on your card is the safest response.",
                consequence: "You protected your account and avoided the scam."
            }
        }
    },

    tech_support: {
        callerName: "Microsoft Support",
        callerNumber: "(888) 555-4402",
        avatar: "T",
        hint: "Tip: Real tech companies do not cold-call people to fix viruses or ask for remote access unexpectedly.",
        difficulty: 1,
        criticalIndicatorsTotal: 3,
        start: "node1",
        nodes: {
            node1: {
                prompt_key: "opening",
                choices: [
                    { text: "Let them help fix it", next: "node2_remote" },
                    { text: "Ask how they got your number", next: "node2_question" },
                    { text: "Hang up", next: "end_best" },
                    { text: "Tell them to call later", next: "end_risky" }
                ]
            },
            node2_remote: {
                prompt_key: "remote_access_request",
                choices: [
                    { text: "Download it", next: "end_unsafe" },
                    { text: "Refuse and ask for proof", next: "end_risky" },
                    { text: "Hang up", next: "end_best" }
                ]
            },
            node2_question: {
                prompt_key: "fake_system_alert",
                choices: [
                    { text: "Continue listening", next: "end_risky" },
                    { text: "Hang up", next: "end_best" }
                ]
            },
            end_unsafe: {
                ending: true,
                title: "Unsafe choice",
                feedback: "Remote access scams can give attackers full control of your computer, files, and passwords.",
                consequence: "Your device and accounts could be compromised."
            },
            end_risky: {
                ending: true,
                title: "Risky choice",
                feedback: "Scammers often invent technical explanations and use urgency to sound believable.",
                consequence: "Staying on the call increases the chance of being manipulated."
            },
            end_best: {
                ending: true,
                title: "Best choice",
                feedback: "Good job. Unsolicited tech support calls are a major scam tactic. Hanging up is the safest response.",
                consequence: "You kept control of your device and information."
            }
        }
    },

    grandparent: {
        callerName: "Unknown Family Member",
        callerNumber: "(619) 555-7802",
        avatar: "G",
        hint: "Tip: If a caller claims to be family and asks for urgent money, slow down and verify with another trusted relative.",
        difficulty: 1,
        criticalIndicatorsTotal: 3,
        start: "node1",
        nodes: {
            node1: {
                prompt_key: "family_emergency_opening",
                choices: [
                    { text: "Send money immediately", next: "end_unsafe" },
                    { text: "Ask who is calling", next: "node2_verify" },
                    { text: "Call another family member first", next: "end_best" },
                    { text: "Stay on the line and listen", next: "end_risky" }
                ]
            },
            node2_verify: {
                prompt_key: "family_pressure",
                choices: [
                    { text: "Send the money", next: "end_unsafe" },
                    { text: "Call another relative to verify", next: "end_best" },
                    { text: "Hang up", next: "end_best" }
                ]
            },
            end_unsafe: {
                ending: true,
                title: "Unsafe choice",
                feedback: "The grandparent scam relies on emotion, secrecy, and urgency to pressure victims into sending money.",
                consequence: "Money sent to scammers is often impossible to recover."
            },
            end_risky: {
                ending: true,
                title: "Risky choice",
                feedback: "Staying engaged without verifying the caller can make it easier for the scammer to pressure you emotionally.",
                consequence: "You may be manipulated into sending money or sharing personal information."
            },
            end_best: {
                ending: true,
                title: "Best choice",
                feedback: "Excellent choice. Verifying through another family member is the safest response in an emergency-money call.",
                consequence: "You protected yourself from a very common impersonation scam."
            }
        }
    },

    government: {
        callerName: "Government Office",
        callerNumber: "(877) 555-9021",
        avatar: "G",
        hint: "Tip: Government agencies do not demand payment by phone using gift cards, wire transfers, or threats.",
        difficulty: 1,
        criticalIndicatorsTotal: 3,
        start: "node1",
        nodes: {
            node1: {
                prompt_key: "government_threat_opening",
                choices: [
                    { text: "Ask what payment they need", next: "node2_payment" },
                    { text: "Ask for official mail or documentation", next: "node2_docs" },
                    { text: "Hang up", next: "end_best" },
                    { text: "Give your Social Security number", next: "end_unsafe" }
                ]
            },
            node2_payment: {
                prompt_key: "gift_card_payment",
                choices: [
                    { text: "Pay now", next: "end_unsafe" },
                    { text: "Refuse and hang up", next: "end_best" }
                ]
            },
            node2_docs: {
                prompt_key: "refuse_documentation",
                choices: [
                    { text: "Stay on the call", next: "end_risky" },
                    { text: "Hang up", next: "end_best" }
                ]
            },
            end_unsafe: {
                ending: true,
                title: "Unsafe choice",
                feedback: "Government impersonation scams often use fear and legal threats. Real agencies do not demand immediate payment like this by phone.",
                consequence: "You could lose money and expose personal identity information."
            },
            end_risky: {
                ending: true,
                title: "Risky choice",
                feedback: "Threats and urgent legal language are common tools used by impersonation scammers.",
                consequence: "Remaining engaged increases the chance of pressure and deception."
            },
            end_best: {
                ending: true,
                title: "Best choice",
                feedback: "Good decision. Hanging up protects you from threat-based scams. Real government matters are handled through official channels and documented communication.",
                consequence: "You avoided a high-pressure impersonation scam."
            }
        }
    }
};

let currentScenarioKey = null;
let currentScenario = null;
let currentNodeKey = null;

let currentSessionId = null;
let sessionStartTime = null;
let attemptCount = 0;
let usedHint = 0;
let criticalIndicatorsFound = 0;
let criticalIndicatorsTotal = 0;

const scenarioMessage = document.getElementById("scenarioMessage");
const choiceGrid = document.getElementById("choiceGrid");
const feedbackBox = document.getElementById("feedbackBox");
const restartBtn = document.getElementById("restartBtn");
const callerNameEl = document.getElementById("callerName");
const callerNumberEl = document.getElementById("callerNumber");
const callerAvatarEl = document.getElementById("callerAvatar");
const hintTextEl = document.getElementById("hintText");
const scenarioButtons = document.querySelectorAll(".scenarioBtn");
const speakBtn = document.getElementById("speakBtn");
let currentAudio = null;

async function postJSON(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    return response.json();
}

async function startRoleplaySession(scenarioKey) {
    sessionStartTime = Date.now();
    attemptCount = 0;
    usedHint = 0;
    criticalIndicatorsFound = 0;
    criticalIndicatorsTotal = currentScenario.criticalIndicatorsTotal || 0;

    const data = await postJSON("/phone-roleplay/start-session", {
        scenario_type: scenarioKey,
        difficulty_level: currentScenario.difficulty || 1
    });

    if (data.success) {
        currentSessionId = data.session_id;
    } else {
        currentSessionId = null;
    }
}

async function logRoleplayEvent(eventType, eventValue = "") {
    if (!currentSessionId || !sessionStartTime) return;

    const timeOffsetSeconds = (Date.now() - sessionStartTime) / 1000;

    await postJSON("/phone-roleplay/log-event", {
        session_id: currentSessionId,
        event_type: eventType,
        event_value: eventValue,
        time_offset_seconds: timeOffsetSeconds
    });
}

async function finishRoleplaySession(node) {
    if (!currentSessionId) return;

    let score = 0;
    let behaviorPattern = "uncertain";

    if (node.title.toLowerCase().includes("best")) {
        score = 100;
        behaviorPattern = "safe_decision";
        criticalIndicatorsFound = criticalIndicatorsTotal;
    } else if (node.title.toLowerCase().includes("better")) {
        score = 70;
        behaviorPattern = "recovered_after_risk";
        criticalIndicatorsFound = Math.max(1, criticalIndicatorsTotal - 1);
    } else if (node.title.toLowerCase().includes("risky")) {
        score = 45;
        behaviorPattern = "uncertain";
        criticalIndicatorsFound = Math.max(1, criticalIndicatorsTotal - 2);
    } else if (node.title.toLowerCase().includes("unsafe")) {
        score = 20;
        behaviorPattern = "high_risk";
        criticalIndicatorsFound = 0;
    }

    await postJSON("/phone-roleplay/finish-session", {
        session_id: currentSessionId,
        final_outcome: node.title,
        score: score,
        attempt_count: attemptCount,
        critical_indicators_found: criticalIndicatorsFound,
        critical_indicators_total: criticalIndicatorsTotal,
        used_hint: usedHint,
        behavior_pattern: behaviorPattern,
        feedback_shown: node.feedback
    });
}

async function getRoleplayLine(scenarioType, promptKey, difficulty = 1) {
    const data = await postJSON("/generate-roleplay-line", {
        scenario_type: scenarioType,
        prompt_key: promptKey,
        difficulty: difficulty
    });

    if (!data.success || !data.line) {
        return t("The caller says something suspicious and urgent, trying to pressure you into acting quickly.");
    }

    return data.line;
}

function getRoleplayTTSLang() {
    const raw = (document.documentElement.getAttribute("lang") || "en").toLowerCase();
    if (raw.startsWith("zh")) return "zh-CN";
    return raw.startsWith("es") ? "es" : "en";
}

async function speakText(text, lang = getRoleplayTTSLang(), slow = false) {
    if (!text || !text.trim()) return;

    try {
        const response = await fetch("/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, lang, slow })
        });

        const data = await response.json();

        if (!data.success || !data.audio) {
            console.error("TTS failed:", data.message || "Unknown error");
            return;
        }

        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        currentAudio = new Audio(`data:${data.mime};base64,${data.audio}`);
        await currentAudio.play();
    } catch (error) {
        console.error("Error playing TTS:", error);
    }
}

async function loadScenario(key) {
    currentScenarioKey = key;
    currentScenario = scenarios[key];
    currentNodeKey = currentScenario.start;

    callerNameEl.textContent = t(currentScenario.callerName);
    callerNumberEl.textContent = currentScenario.callerNumber;
    callerAvatarEl.textContent = currentScenario.avatar;
    hintTextEl.textContent = t(currentScenario.hint);

    await startRoleplaySession(key);
    await logRoleplayEvent("scenario_started", key);

    renderNode(currentNodeKey);
}

async function renderNode(nodeKey) {
    if (!currentScenario) return;

    const node = currentScenario.nodes[nodeKey];
    currentNodeKey = nodeKey;

    feedbackBox.style.display = "none";
    feedbackBox.innerHTML = "";
    choiceGrid.innerHTML = "";

    if (node.ending) {
        scenarioMessage.textContent = t(node.title);

        feedbackBox.style.display = "block";
        feedbackBox.innerHTML = `
            <strong>${t(node.title)}</strong><br><br>
            ${t(node.feedback)}<br><br>
            <strong>${t("Real-world consequence:")}</strong> ${t(node.consequence)}
        `;

            speakText(`${t(node.title)}. ${t(node.feedback)} ${t("Real world consequence:")} ${t(node.consequence)}`);


        await logRoleplayEvent("scenario_completed", node.title);
        await finishRoleplaySession(node);
        return;
    }

    scenarioMessage.textContent = t("Loading dialogue...");

    const line = await getRoleplayLine(
        currentScenarioKey,
        node.prompt_key,
        currentScenario.difficulty || 1
    );

    scenarioMessage.textContent = line;
    speakText(line);

    await logRoleplayEvent("dialogue_loaded", node.prompt_key);

    node.choices.forEach(choice => {
        const btn = document.createElement("button");
        btn.className = "choiceBtn";
        btn.textContent = t(choice.text);
        btn.addEventListener("click", async () => {
            attemptCount += 1;
            await logRoleplayEvent("option_selected", choice.text);
            renderNode(choice.next);
        });
        choiceGrid.appendChild(btn);
    });
}

scenarioButtons.forEach(button => {
    button.addEventListener("click", () => {
        const scenarioKey = button.getAttribute("data-scenario");
        loadScenario(scenarioKey);
    });
});

if (speakBtn) {
    speakBtn.addEventListener("click", () => {
        const text = scenarioMessage.textContent.trim();
        if (text && text !== t("Loading dialogue...")) {
            speakText(text);
        }
    });
}

restartBtn.addEventListener("click", async () => {
    if (currentScenario) {
        await logRoleplayEvent("restart_clicked", currentScenarioKey);
        await startRoleplaySession(currentScenarioKey);
        renderNode(currentScenario.start);
    }
});
