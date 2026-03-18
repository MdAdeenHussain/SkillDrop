document.addEventListener("DOMContentLoaded", () => {
    setupRevealAnimations();
    setupRippleButtons();
    setupChatbot();
    setupCompletionForms();
    setupAudioPlayback();
});

function setupRevealAnimations() {
    const items = document.querySelectorAll(".reveal");

    if (!("IntersectionObserver" in window)) {
        items.forEach((item) => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.12 }
    );

    items.forEach((item) => observer.observe(item));
}

function setupRippleButtons() {
    document.querySelectorAll(".js-ripple").forEach((button) => {
        button.addEventListener("click", () => {
            button.classList.remove("ripple-active");
            window.requestAnimationFrame(() => button.classList.add("ripple-active"));
        });
    });
}

function setupChatbot() {
    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("chatMessages");
    const languageSelect = document.getElementById("languageSelect");

    if (!form || !input || !messages || !languageSelect) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const question = input.value.trim();
        const language = languageSelect.value;

        if (!question) {
            return;
        }

        appendMessage(messages, "user", question, []);
        input.value = "";

        appendTypingMessage(messages, language);

        try {
            const response = await fetch("/chatbot", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: JSON.stringify({ question, language }),
            });

            const data = await response.json();
            removeTypingMessage(messages);
            appendMessage(messages, "assistant", data.headline, data.steps);
        } catch (error) {
            removeTypingMessage(messages);
            const fallbackText = language === "hi"
                ? "नेटवर्क में दिक्कत है। कृपया फिर से कोशिश करें।"
                : "Network issue right now. Please try again.";
            appendMessage(messages, "assistant", fallbackText, []);
        }
    });
}

function appendMessage(container, role, text, steps) {
    const card = document.createElement("div");
    card.className = `message ${role}`;

    const roleLabel = document.createElement("span");
    roleLabel.className = "message-role";
    roleLabel.textContent = role === "user" ? "You" : "SkillDrop AI";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    card.appendChild(roleLabel);
    card.appendChild(paragraph);

    if (Array.isArray(steps) && steps.length) {
        const list = document.createElement("ol");
        steps.forEach((step) => {
            const item = document.createElement("li");
            item.textContent = step;
            list.appendChild(item);
        });
        card.appendChild(list);
    }

    container.appendChild(card);
    container.scrollTop = container.scrollHeight;
}

function appendTypingMessage(container, language) {
    const card = document.createElement("div");
    card.className = "message assistant";
    card.dataset.typing = "true";

    const roleLabel = document.createElement("span");
    roleLabel.className = "message-role";
    roleLabel.textContent = "SkillDrop AI";

    const paragraph = document.createElement("p");
    paragraph.textContent = language === "hi" ? "सोच रहा है..." : "Thinking...";

    card.appendChild(roleLabel);
    card.appendChild(paragraph);
    container.appendChild(card);
    container.scrollTop = container.scrollHeight;
}

function removeTypingMessage(container) {
    const typing = container.querySelector("[data-typing='true']");
    if (typing) {
        typing.remove();
    }
}

function setupCompletionForms() {
    document.querySelectorAll(".complete-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const button = form.querySelector("[data-complete-button]");
            if (!button || button.disabled) {
                return;
            }

            button.disabled = true;
            button.textContent = "Saving...";

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                const data = await response.json();
                button.textContent = "Completed";
                updateProgressUI(data.summary);
            } catch (error) {
                button.disabled = false;
                button.textContent = "Try Again";
            }
        });
    });
}

function updateProgressUI(summary) {
    if (!summary) {
        return;
    }

    const completed = document.getElementById("completedCount");
    const percent = document.getElementById("progressPercent");
    const streak = document.getElementById("streakCount");
    const bar = document.getElementById("progressBarFill");

    if (completed) {
        completed.textContent = summary.completed_count;
    }

    if (percent) {
        percent.textContent = `${summary.percent}%`;
    }

    if (streak) {
        streak.textContent = summary.streak;
    }

    if (bar) {
        bar.style.width = `${summary.percent}%`;
    }
}

function setupAudioPlayback() {
    document.querySelectorAll(".play-audio").forEach((button) => {
        button.addEventListener("click", () => {
            const title = button.dataset.title || "Lesson";
            const steps = (button.dataset.steps || "")
                .split("||")
                .map((step) => step.trim())
                .filter(Boolean);
            const language = button.dataset.language === "hi" ? "hi-IN" : "en-IN";

            if (!("speechSynthesis" in window)) {
                window.alert("Audio playback is not supported on this browser.");
                return;
            }

            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(`${title}. ${steps.join(". ")}`);
            utterance.lang = language;
            utterance.rate = 0.95;
            window.speechSynthesis.speak(utterance);
        });
    });
}
