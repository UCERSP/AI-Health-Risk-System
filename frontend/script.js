const API_BASE = window.location.protocol === "file:"
    ? "https://ai-health-risk-system.onrender.com"
    : window.location.origin;

let currentUser = null;
let currentPage = "home";

const $ = (id) => document.getElementById(id);

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        credentials: "include",
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...options.headers
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed. Please try again.");
    }

    return data;
}

function showMessage(id, message, isError = false) {
    const element = $(id);
    if (!element) return;

    element.textContent = message;
    element.style.color = isError ? "#b42318" : "";
}

function showPage(pageId, updateHash = true) {
    const pageMap = {
        home: "home",
        assessment: "assessment",
        about: "about",
        account: "account",
        form: "healthFormPage",
        results: "resultsPage",
        history: "history"
    };

    const targetId = pageMap[pageId] || pageId;
    const target = $(targetId);

    if (!target) {
        console.error("Page not found:", targetId);
        return;
    }

    document.querySelectorAll(".page-section").forEach((section) => {
        section.hidden = section.id !== targetId;
    });

    currentPage = pageId;

    document.querySelectorAll(".navbar nav a").forEach((link) => {
        const active = link.dataset.page === pageId;
        link.classList.toggle("active", active);

        if (active) {
            link.setAttribute("aria-current", "page");
        } else {
            link.removeAttribute("aria-current");
        }
    });

    if (updateHash) {
        const hash = pageId === "form" ? "health-form" : pageId;
        history.replaceState(null, "", `#${hash}`);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function showAuthPanel(mode) {
    if (!$("authPanel")) return;

    $("authPanel").hidden = false;
    $("signupPanel").hidden = mode !== "signup";
    $("loginPanel").hidden = mode !== "login";

    showMessage("authMessage", "");
    showPage("account");
}

function updateLoginState(user) {
    currentUser = user || null;

    if ($("openLoginBtn")) $("openLoginBtn").hidden = !!currentUser;
    if ($("openSignupBtn")) $("openSignupBtn").hidden = !!currentUser;
    if ($("historyBtn")) $("historyBtn").hidden = !currentUser;
    if ($("logoutBtn")) $("logoutBtn").hidden = !currentUser;

    if ($("authHeading")) {
        $("authHeading").textContent = currentUser
            ? `Welcome, ${currentUser.name || "User"}`
            : "Welcome to HealthAI";
    }

    if ($("authStatus")) {
        $("authStatus").textContent = currentUser
            ? "You are logged in. Your new assessments can be saved to your account."
            : "Try a demo assessment without logging in. Log in to save and view your personal history.";
    }

    if ($("assessmentAccountNote")) {
        $("assessmentAccountNote").textContent = currentUser
            ? "Your assessment will be associated with your signed-in account."
            : "Guest mode: this assessment will not be saved to account history.";
    }

    if (currentUser && $("name")) {
        $("name").value = currentUser.name || "";
    }

    if (currentUser && $("authPanel")) {
        $("authPanel").hidden = true;
    }
}

function getNumber(id) {
    const element = $(id);
    return element ? Number(element.value) : NaN;
}

function addMetricCard(container, title, value, unit, percent) {
    const card = document.createElement("div");
    card.className = "metric-chart-card";

    const heading = document.createElement("h4");
    heading.textContent = title;

    const metricValue = document.createElement("p");
    metricValue.className = "metric-chart-value";
    metricValue.textContent = `${value} ${unit}`.trim();

    const track = document.createElement("div");
    track.className = "metric-track";
    track.setAttribute("role", "img");
    track.setAttribute("aria-label", `${title}: ${value} ${unit}`);

    const fill = document.createElement("div");
    fill.className = "metric-fill";
    fill.style.width = `${Math.max(0, Math.min(100, percent))}%`;

    track.appendChild(fill);

    card.append(heading, metricValue, track);
    container.appendChild(card);
}

function renderAssessmentGraph(data) {
    const container = $("assessmentGraph");
    const section = $("assessmentGraphSection");

    if (!container || !section) return;

    container.replaceChildren();

    const bmi = Number(data.bmi);
    const systolic = getNumber("systolic");
    const diastolic = getNumber("diastolic");
    const glucose = getNumber("glucose");

    if (Number.isFinite(bmi)) {
        addMetricCard(container, "Body Mass Index (BMI)", bmi.toFixed(1), "", bmi / 40 * 100);
    }

    if (Number.isFinite(systolic)) {
        addMetricCard(container, "Systolic Blood Pressure", systolic, "mmHg", systolic / 250 * 100);
    }

    if (Number.isFinite(diastolic)) {
        addMetricCard(container, "Diastolic Blood Pressure", diastolic, "mmHg", diastolic / 150 * 100);
    }

    if (Number.isFinite(glucose)) {
        addMetricCard(container, "Blood Glucose", glucose, "mg/dL", glucose / 500 * 100);
    }

    section.hidden = container.children.length === 0;
}

function renderHistory(records) {
    const list = $("historyList");
    const graphSection = $("historyGraphSection");
    const graph = $("historyGraph");

    if (!list || !graph || !graphSection) return;

    list.replaceChildren();
    graph.replaceChildren();

    if (!Array.isArray(records) || records.length === 0) {
        showMessage("historyMessage", "No saved assessments found in your account yet.");
        graphSection.hidden = true;
        return;
    }

    showMessage("historyMessage", `Showing ${records.length} saved assessment(s) from your account.`);

    const metrics = [
        { key: "bmi", label: "BMI" },
        { key: "systolic", label: "Systolic BP" },
        { key: "diastolic", label: "Diastolic BP" },
        { key: "glucose", label: "Glucose" }
    ];

    metrics.forEach((metric) => {
        const values = records
            .map((record) => Number(record[metric.key]))
            .filter((value) => Number.isFinite(value));

        if (!values.length) return;

        const card = document.createElement("div");
        card.className = "trend-card";

        const heading = document.createElement("h4");
        heading.textContent = `${metric.label} — saved records`;

        const latest = document.createElement("p");
        latest.className = "trend-latest";
        latest.textContent = `Latest: ${values[0]}`;

        const svgNS = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("viewBox", "0 0 320 130");
        svg.setAttribute("class", "trend-svg");
        svg.setAttribute("role", "img");
        svg.setAttribute("aria-label", `${metric.label} values across saved assessments`);

        const maxValue = Math.max(...values);
        const minValue = Math.min(...values);
        const spread = maxValue - minValue || 1;

        [25, 60, 95].forEach((y) => {
            const line = document.createElementNS(svgNS, "line");
            line.setAttribute("x1", "12");
            line.setAttribute("x2", "308");
            line.setAttribute("y1", String(y));
            line.setAttribute("y2", String(y));
            line.setAttribute("class", "chart-gridline");
            svg.appendChild(line);
        });

        const points = values.slice(0, 10).reverse().map((value, index, arr) => {
            const x = arr.length === 1 ? 160 : 15 + index * (290 / (arr.length - 1));
            const y = 100 - ((value - minValue) / spread) * 65;
            return { x, y, value };
        });

        if (points.length > 1) {
            const polyline = document.createElementNS(svgNS, "polyline");
            polyline.setAttribute("class", "chart-line");
            polyline.setAttribute("points", points.map((point) => `${point.x},${point.y}`).join(" "));
            svg.appendChild(polyline);
        }

        points.forEach((point) => {
            const circle = document.createElementNS(svgNS, "circle");
            circle.setAttribute("cx", String(point.x));
            circle.setAttribute("cy", String(point.y));
            circle.setAttribute("r", "4");
            circle.setAttribute("class", "chart-point");
            circle.setAttribute("aria-label", String(point.value));
            svg.appendChild(circle);
        });

        card.append(heading, latest, svg);
        graph.appendChild(card);
    });

    graphSection.hidden = graph.children.length === 0;

    records.forEach((record) => {
        const card = document.createElement("article");
        card.className = "history-card";

        const heading = document.createElement("h3");
        heading.textContent = `Assessment${record.created_at ? ` — ${record.created_at}` : ""}`;

        const details = [
            `BMI: ${record.bmi ?? "N/A"}`,
            `Systolic BP: ${record.systolic ?? "N/A"} mmHg`,
            `Diastolic BP: ${record.diastolic ?? "N/A"} mmHg`,
            `Glucose: ${record.glucose ?? "N/A"} mg/dL`
        ];

        card.appendChild(heading);

        details.forEach((detail) => {
            const paragraph = document.createElement("p");
            paragraph.textContent = detail;
            card.appendChild(paragraph);
        });

        list.appendChild(card);
    });
}

async function loadHistory() {
    if (!currentUser) {
        showMessage("historyMessage", "Please log in to view your personal history.", true);
        showPage("account");
        showAuthPanel("login");
        return;
    }

    showPage("history");
    showMessage("historyMessage", "Loading your saved assessments...");

    try {
        const data = await apiRequest("/api/history");
        renderHistory(data.records || []);
    } catch (error) {
        showMessage("historyMessage", error.message, true);
    }
}

async function checkLoginStatus() {
    try {
        const data = await apiRequest("/api/me");
        updateLoginState(data.user || null);
    } catch {
        updateLoginState(null);
    }
}

function setupNavigation() {
    document.querySelectorAll(".navbar nav a").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            showPage(link.dataset.page || "home");
        });
    });

    if ($("startAssessmentBtn")) {
        $("startAssessmentBtn").addEventListener("click", () => {
            showPage("form");
        });
    }

    if ($("infoStartAssessmentBtn")) {
        $("infoStartAssessmentBtn").addEventListener("click", () => {
            showPage("form");
        });
    }

    if ($("newAssessmentBtn")) {
        $("newAssessmentBtn").addEventListener("click", () => {
            $("healthForm")?.reset();

            if (currentUser && $("name")) {
                $("name").value = currentUser.name || "";
            }

            if ($("result")) {
                $("result").hidden = true;
                $("result").classList.add("hidden");
            }

            showPage("form");
        });
    }

    if ($("openLoginBtn")) {
        $("openLoginBtn").addEventListener("click", () => showAuthPanel("login"));
    }

    if ($("openSignupBtn")) {
        $("openSignupBtn").addEventListener("click", () => showAuthPanel("signup"));
    }

    if ($("switchToLoginBtn")) {
        $("switchToLoginBtn").addEventListener("click", () => showAuthPanel("login"));
    }

    if ($("switchToSignupBtn")) {
        $("switchToSignupBtn").addEventListener("click", () => showAuthPanel("signup"));
    }

    if ($("historyBtn")) {
        $("historyBtn").addEventListener("click", loadHistory);
    }

    if ($("logoutBtn")) {
        $("logoutBtn").addEventListener("click", async () => {
            try {
                await apiRequest("/api/logout", { method: "POST" });
                updateLoginState(null);
                showMessage("authMessage", "You have been logged out.");
                showPage("home");
            } catch (error) {
                showMessage("authMessage", error.message, true);
            }
        });
    }

    window.addEventListener("hashchange", () => {
        const hash = window.location.hash.slice(1);
        const pages = ["home", "assessment", "about"];

        if (pages.includes(hash)) {
            showPage(hash, false);
        } else if (hash === "health-form") {
            showPage("form", false);
        }
    });
}

function setupAuthentication() {
    if ($("signupForm")) {
        $("signupForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            showMessage("authMessage", "Creating your account...");

            const payload = {
                name: $("signupName").value.trim(),
                email: $("signupEmail").value.trim(),
                password: $("signupPassword").value
            };

            try {
                const data = await apiRequest("/api/signup", {
                    method: "POST",
                    body: JSON.stringify(payload)
                });

                updateLoginState(data.user || null);
                $("signupForm").reset();
                showMessage("authMessage", data.message || "Account created successfully.");
                showPage("assessment");
            } catch (error) {
                showMessage("authMessage", error.message, true);
            }
        });
    }

    if ($("loginForm")) {
        $("loginForm").addEventListener("submit", async (event) => {
            event.preventDefault();
            showMessage("authMessage", "Logging in...");

            const payload = {
                email: $("loginEmail").value.trim(),
                password: $("loginPassword").value
            };

            try {
                const data = await apiRequest("/api/login", {
                    method: "POST",
                    body: JSON.stringify(payload)
                });

                updateLoginState(data.user || null);
                $("loginForm").reset();
                showMessage("authMessage", data.message || "Login successful.");
                showPage("assessment");
            } catch (error) {
                showMessage("authMessage", error.message, true);
            }
        });
    }
}

function setupHealthAssessment() {
    if (!$("healthForm")) return;

    $("healthForm").addEventListener("submit", async (event) => {
        event.preventDefault();

        const button = $("healthForm").querySelector('button[type="submit"]');
        const originalText = button ? button.textContent : "";

        if (button) {
            button.disabled = true;
            button.textContent = "Analyzing...";
        }

        const payload = {
            name: $("name").value.trim(),
            age: getNumber("age"),
            gender: $("gender").value,
            height: getNumber("height"),
            weight: getNumber("weight"),
            systolic: getNumber("systolic"),
            diastolic: getNumber("diastolic"),
            glucose: getNumber("glucose")
        };

        try {
            const data = await apiRequest("/analyze", {
                method: "POST",
                body: JSON.stringify(payload)
            });

            if ($("result")) {
                $("result").hidden = false;
                $("result").classList.remove("hidden");
            }

            const bmi = Number(data.bmi);

            if ($("resultTitle")) {
                $("resultTitle").textContent = "Your Health Assessment";
            }

            if ($("riskScore")) {
                $("riskScore").textContent = Number.isFinite(bmi)
                    ? bmi.toFixed(1)
                    : (data.bmi ?? "N/A");
            }

            if ($("predictionResult")) {
                $("predictionResult").textContent =
                    data.risk || data.bmi_category || "Assessment complete";
            }

            
if ($("resultMessage")) {
    $("resultMessage").textContent =
        data.explanation || "Your assessment explanation will appear here.";
}

if ($("precautionsList")) {
    const list = $("precautionsList");
    list.replaceChildren();

    let precautions = data.precautions;

    if (typeof precautions === "string") {
        precautions = [precautions];
    }

    if (!Array.isArray(precautions) || precautions.length === 0) {
        precautions = ["Please consult a qualified healthcare professional for personal medical advice."];
    }

    precautions.forEach((precaution) => {
        const item = document.createElement("li");
        item.textContent = precaution;
        list.appendChild(item);
    });
}

if ($("resultNote")) {
    $("resultNote").textContent =
        data.note || "This is an educational prototype and not a medical diagnosis.";
}


            renderAssessmentGraph(data);
            showPage("results");

            if (currentUser && data.saved_to_history) {
                showMessage("authMessage", "Assessment saved to your account history.");
            }
        } catch (error) {
            alert(error.message || "Could not analyze your details. Please try again.");
        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    setupNavigation();
    setupAuthentication();
    setupHealthAssessment();

    await checkLoginStatus();

    const hash = window.location.hash.slice(1);

    if (hash === "assessment" || hash === "about" || hash === "home") {
        showPage(hash, false);
    } else {
        showPage("home", false);
    }
});