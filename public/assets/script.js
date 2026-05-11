const codeInput = document.getElementById("codeInput");
const runButton = document.getElementById("runButton");
const flowchartButton = document.getElementById("flowchartButton");
const statusBadge = document.getElementById("statusBadge");
const errorOutput = document.getElementById("errorOutput");
const stdoutOutput = document.getElementById("stdoutOutput");
const tracebackOutput = document.getElementById("tracebackOutput");
const flowchartImage = document.getElementById("flowchartImage");
const imageFrame = document.getElementById("imageFrame");
const flowchartMessage = document.getElementById("flowchartMessage");
const downloadLink = document.getElementById("downloadLink");
const themeToggle = document.getElementById("themeToggle");
const styleDropdown = document.getElementById("styleDropdown");
const themeDropdown = document.getElementById("themeDropdown");
const suggestionBadge = document.getElementById("suggestionBadge");
const tabCodeMode = document.getElementById("tabCodeMode");
const tabTextMode = document.getElementById("tabTextMode");
const codeModeSection = document.getElementById("codeModeSection");
const textModeSection = document.getElementById("textModeSection");

const textInput = document.getElementById("textInput");
const textStyleDropdown = document.getElementById("textStyleDropdown");
const textThemeDropdown = document.getElementById("textThemeDropdown");
const textFlowchartButton = document.getElementById("textFlowchartButton");

const analyzeTextButton = document.getElementById("analyzeTextButton");
const extractedStepsContainer = document.getElementById("extractedStepsContainer");
const extractedStepsInput = document.getElementById("extractedStepsInput");
const analyzeTextRow = document.getElementById("analyzeTextRow");
const isFileProtocol = window.location.protocol === "file:";

if (isFileProtocol) {
    setStatus("idle", "Preview Only");
    errorOutput.textContent = "This page was opened from a local file. Styling and theme preview work here, but Run Code, Generate Flowchart, and text analysis require Flask or the deployed Vercel URL.";
    stdoutOutput.textContent = "Open the app through http://127.0.0.1:5002 or your Vercel deployment to use backend features.";
    tracebackOutput.textContent = "Direct file preview cannot call the Flask API endpoints.";
    flowchartMessage.textContent = "Preview mode: backend-generated diagrams are unavailable when opened with file://.";
    runButton.disabled = true;
    flowchartButton.disabled = true;
    analyzeTextButton.disabled = true;
    textFlowchartButton.disabled = true;
}

tabCodeMode.addEventListener("click", () => {
    tabCodeMode.classList.add("active");
    tabTextMode.classList.remove("active");
    codeModeSection.classList.remove("hidden");
    textModeSection.classList.add("hidden");
});

tabTextMode.addEventListener("click", () => {
    tabTextMode.classList.add("active");
    tabCodeMode.classList.remove("active");
    textModeSection.classList.remove("hidden");
    codeModeSection.classList.add("hidden");
});

const textSuggestionPanel = document.getElementById("textSuggestionPanel");
const textSuggestionType = document.getElementById("textSuggestionType");
const textSuggestionReason = document.getElementById("textSuggestionReason");

analyzeTextButton.addEventListener("click", () => submitTextAnalysis());

async function submitTextAnalysis() {
    if (isFileProtocol) return;
    const text = textInput.value;
    if (!text.trim()) return;

    analyzeTextButton.textContent = "Processing Text...";
    analyzeTextButton.disabled = true;

    try {
        const response = await fetch("/api/text/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await response.json();

        analyzeTextRow.classList.add("hidden");
        extractedStepsContainer.classList.remove("hidden");

        const stepsFormatted = (data.steps || []).join("\n-> ");
        extractedStepsInput.value = stepsFormatted || text;

        if (data.suggestion && data.suggestion.type) {
            textSuggestionType.textContent = data.suggestion.type;
            textSuggestionReason.textContent = `(${data.suggestion.reason})`;
            textSuggestionPanel.style.display = "block";

            const options = Array.from(textStyleDropdown.options);
            const matchingOption = options.find((opt) => opt.value === data.suggestion.type);
            if (matchingOption) {
                textStyleDropdown.value = matchingOption.value;
            }
        } else {
            textSuggestionPanel.style.display = "none";
        }
    } catch (error) {
        console.error("Text Analysis/Extraction Failed", error);
    } finally {
        analyzeTextButton.textContent = "Analyze Text & Extract Logic";
        analyzeTextButton.disabled = false;
    }
}

extractedStepsInput.addEventListener("input", () => {
});

const savedTheme = localStorage.getItem("autoflow-theme") || "dark";
if (savedTheme === "light") {
    document.documentElement.classList.add("light-theme");
}

themeToggle.addEventListener("click", () => {
    const isLight = document.documentElement.classList.toggle("light-theme");
    localStorage.setItem("autoflow-theme", isLight ? "light" : "dark");
});

let debounceTimer = null;
codeInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(analyzeCode, 600);
});

async function analyzeCode() {
    if (isFileProtocol) {
        suggestionBadge.style.opacity = "0";
        return;
    }
    const code = codeInput.value;
    if (!code.trim()) {
        suggestionBadge.style.opacity = "0";
        return;
    }
    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code })
        });
        const data = await response.json();
        if (data.suggestion) {
            suggestionBadge.textContent = data.suggestion;
            suggestionBadge.style.opacity = "1";
        } else {
            suggestionBadge.style.opacity = "0";
        }
    } catch (error) {
        console.error("Analyzer request failed", error);
    }
}

runButton.addEventListener("click", () => submitCode("run"));
flowchartButton.addEventListener("click", () => submitCode("flowchart"));

async function submitCode(mode) {
    if (isFileProtocol) return;
    const code = codeInput.value;

    if (!code.trim()) {
        setStatus("error", "Missing Code");
        errorOutput.textContent = "Please paste Python code before running AUTOFLOW AI.";
        stdoutOutput.textContent = "Program output will appear here.";
        tracebackOutput.textContent = "Detailed traceback information will appear here when available.";
        hideFlowchart("Flowchart preview is unavailable until code is provided.");
        return;
    }

    setLoadingState(true, mode);
    setStatus("idle", "Processing");
    flowchartMessage.textContent = "Analyzing code and generating flowchart...";

    try {
        const languageDropdown = document.getElementById("languageDropdown");
        const language = languageDropdown ? languageDropdown.value : "Python";

        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                code,
                mode,
                language,
                style: styleDropdown.value,
                theme: themeDropdown.value,
                detail_mode: document.querySelector('input[name="codeDetailMode"]:checked').value
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "The request could not be completed.");
        }

        renderResponse(data);
    } catch (error) {
        setStatus("error", "Request Failed");
        errorOutput.textContent = error.message;
        stdoutOutput.textContent = "Program output is unavailable.";
        tracebackOutput.textContent = "A network or server error prevented execution.";
        hideFlowchart("Flowchart preview could not be updated.");
    } finally {
        setLoadingState(false, mode);
    }
}

function renderResponse(data) {
    const hasError = Boolean(data.error);

    if (hasError) {
        setStatus("error", "Issues Found");
        errorOutput.textContent = data.error;
        tracebackOutput.textContent = data.traceback || "No traceback details were returned.";
    } else {
        setStatus("success", "Code Executed");
        errorOutput.textContent = "No syntax or runtime errors detected.";
        tracebackOutput.textContent = "No traceback generated.";
    }

    stdoutOutput.textContent = data.stdout || "Program ran without producing stdout output.";

    if (data.flowchart_path) {
        const cacheBustedPath = `${data.flowchart_path}?v=${Date.now()}`;
        flowchartImage.src = cacheBustedPath;
        imageFrame.classList.remove("hidden");
        flowchartMessage.textContent = data.flowchart_error || "Flowchart generated successfully.";

        const filename = data.flowchart_path.split("/").pop().split("?")[0];
        downloadLink.href = `/download/${filename}`;

        downloadLink.classList.remove("disabled");
        downloadLink.setAttribute("aria-disabled", "false");
    } else {
        hideFlowchart(data.flowchart_error || "Flowchart preview is unavailable for this code.");
    }
}

function hideFlowchart(message) {
    imageFrame.classList.add("hidden");
    flowchartImage.removeAttribute("src");
    flowchartMessage.textContent = message;
    downloadLink.href = "#";
    downloadLink.classList.add("disabled");
    downloadLink.setAttribute("aria-disabled", "true");
}

function setStatus(type, label) {
    statusBadge.className = `status-badge ${type}`;
    statusBadge.textContent = label;
}

function setLoadingState(isLoading, mode) {
    runButton.disabled = isLoading;
    flowchartButton.disabled = isLoading;
    textFlowchartButton.disabled = isLoading;

    if (!isLoading) {
        runButton.textContent = "Run Code";
        flowchartButton.textContent = "Generate Flowchart";
        textFlowchartButton.textContent = "Generate Infographic";
        return;
    }

    runButton.textContent = mode === "run" ? "Running..." : "Run Code";
    flowchartButton.textContent = mode === "flowchart" ? "Generating..." : "Generate Flowchart";
    textFlowchartButton.textContent = mode === "textFlowchart" ? "Processing Text..." : "Generate Infographic";
}

textFlowchartButton.addEventListener("click", () => submitTextDiagram());

async function submitTextDiagram() {
    if (isFileProtocol) return;
    const text = extractedStepsInput.value;

    if (!text.trim()) {
        setStatus("error", "Missing Text");
        errorOutput.textContent = "Please type a workflow plan first.";
        stdoutOutput.textContent = "Program output will appear here.";
        tracebackOutput.textContent = "Detailed traceback information will appear here when available.";
        hideFlowchart("Diagram preview is unavailable until text is provided.");
        return;
    }

    const steps = text.split(/(?:\n|->)+/).map((s) => s.trim()).filter((s) => s.length > 0);

    setLoadingState(true, "textFlowchart");
    setStatus("idle", "Generating Diagram");
    flowchartMessage.textContent = "Analyzing structure and rendering graphic...";

    try {
        const response = await fetch("/api/text/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                steps,
                type: textStyleDropdown.value,
                theme: textThemeDropdown.value,
                detail_mode: document.querySelector('input[name="textDetailMode"]:checked').value
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "The request could not be completed.");
        }

        renderResponse(data);
    } catch (error) {
        setStatus("error", "Request Failed");
        errorOutput.textContent = error.message;
        stdoutOutput.textContent = "Traceback engine not applicable to text models.";
        hideFlowchart("Graphic preview could not be generated.");
    } finally {
        setLoadingState(false, "textFlowchart");
    }
}
