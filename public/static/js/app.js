/**
 * WarrantyCheck AI - Frontend Application Controller
 * Handles tab navigation, warranty calculations, document upload & analysis,
 * autofill, and Microsoft Foundry AI chat.
 */

// Global state for document analysis
let latestAnalysisData = null;

// ============================================================
// 1. SAFE NETWORK HELPER (Prevents "Unexpected token <")
// ============================================================

async function safeFetchJson(url, options = {}) {
    let response;
    try {
        response = await fetch(url, options);
    } catch (networkErr) {
        throw new Error("Network connection error. Please check if the Flask server is running.");
    }

    const contentType = response.headers.get("content-type") || "";
    const rawText = await response.text();

    let data = null;
    if (contentType.includes("application/json") || rawText.trim().startsWith("{") || rawText.trim().startsWith("[")) {
        try {
            data = JSON.parse(rawText);
        } catch (parseErr) {
            console.error("JSON parse failure on response:", rawText);
            throw new Error("Server returned an invalid JSON response.");
        }
    } else {
        // Handle unexpected HTML (such as 404/500 default pages)
        console.error("Non-JSON response received:", rawText.substring(0, 300));
        if (response.status === 404) {
            throw new Error(`Endpoint not found (HTTP 404) at ${url}. Please verify server routes.`);
        }
        if (response.status >= 500) {
            throw new Error(`Internal server error (HTTP ${response.status}). Please check Flask logs.`);
        }
        throw new Error(`Unexpected server response (HTTP ${response.status}). Expected JSON.`);
    }

    if (!response.ok) {
        const errorMsg = data && (data.error || data.details || data.message);
        throw new Error(errorMsg || `Request failed with HTTP status ${response.status}.`);
    }

    return data;
}

// ============================================================
// 2. TAB NAVIGATION
// ============================================================

function switchTab(tabId) {
    const tabs = ["warranty", "chat", "document"];

    tabs.forEach(id => {
        const tabBtn = document.getElementById(`${id}Tab`);
        const panel = document.getElementById(`${id}Panel`);

        if (id === tabId) {
            tabBtn?.classList.add("active");
            panel?.classList.remove("hidden");
        } else {
            tabBtn?.classList.remove("active");
            panel?.classList.add("hidden");
        }
    });
}

// ============================================================
// 3. WARRANTY CALCULATOR
// ============================================================

async function handleCheckWarranty(event) {
    if (event) event.preventDefault();

    const productName = document.getElementById("productName").value.trim();
    const brand = document.getElementById("brand").value.trim();
    const modelNumber = document.getElementById("modelNumber").value.trim();
    const serialNumber = document.getElementById("serialNumber").value.trim();
    const purchaseDate = document.getElementById("purchaseDate").value.trim();
    const warrantyYears = document.getElementById("warrantyYears").value.trim();

    const errorBox = document.getElementById("warrantyError");
    const resultBox = document.getElementById("warrantyResult");
    const submitBtn = document.getElementById("checkWarrantyBtn");

    // Reset UI state
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
    resultBox.classList.add("hidden");

    // Client-side validation
    if (!productName) {
        showError(errorBox, "Please enter the product name.");
        document.getElementById("productName").focus();
        return;
    }

    if (!purchaseDate) {
        showError(errorBox, "Please select the purchase date.");
        document.getElementById("purchaseDate").focus();
        return;
    }

    if (!warrantyYears) {
        showError(errorBox, "Please select the warranty duration.");
        document.getElementById("warrantyYears").focus();
        return;
    }

    // Set loading state
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner"></span> Calculating Warranty...`;

    try {
        const payload = {
            product_name: productName,
            brand: brand,
            model_number: modelNumber,
            serial_number: serialNumber,
            purchase_date: purchaseDate,
            warranty_years: warrantyYears
        };

        const result = await safeFetchJson("/api/check-warranty", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        renderWarrantyResult(result);
    } catch (err) {
        console.error("Warranty check error:", err);
        showError(errorBox, err.message || "An unexpected error occurred during warranty calculation.");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

function renderWarrantyResult(data) {
    const resultBox = document.getElementById("warrantyResult");
    const statusBadge = document.getElementById("resultStatusBadge");
    const banner = document.getElementById("resultBanner");

    const isValid = data.status === "Within Warranty";

    // Set status badge
    statusBadge.textContent = data.status;
    statusBadge.className = `result-badge ${isValid ? "valid" : "expired"}`;

    // Fill in field values
    document.getElementById("resultProduct").textContent = data.product_name || "—";
    document.getElementById("resultBrand").textContent = data.brand || "—";
    document.getElementById("resultModel").textContent = data.model_number || "—";
    document.getElementById("resultSerial").textContent = data.serial_number || "—";
    document.getElementById("resultPurchaseDate").textContent = data.purchase_date || "—";
    document.getElementById("resultDuration").textContent = data.warranty_duration || `${data.warranty_years} Year(s)`;
    document.getElementById("resultExpiry").textContent = data.warranty_expiry || data.expiry_date || "—";
    document.getElementById("resultCheckedOn").textContent = data.checked_on || data.today || "—";
    document.getElementById("resultDaysRemaining").textContent = `${data.days_remaining} day(s)`;

    // Banner message
    if (isValid) {
        banner.className = "result-banner banner-valid";
        banner.innerHTML = `<strong>Coverage Active:</strong> This product has <strong>${data.days_remaining} days</strong> remaining under warranty until <strong>${data.warranty_expiry || data.expiry_date}</strong>.`;
    } else {
        banner.className = "result-banner banner-expired";
        banner.innerHTML = `<strong>Warranty Expired:</strong> Coverage ended on <strong>${data.warranty_expiry || data.expiry_date}</strong>. Consult the AI Assistant for repair and policy options.`;
    }

    resultBox.classList.remove("hidden");
    resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ============================================================
// 4. DOCUMENT UPLOAD & AI ANALYSIS
// ============================================================

let selectedFile = null;

function setupDragAndDrop() {
    const dropzone = document.getElementById("uploadDropzone");
    const fileInput = document.getElementById("documentInput");

    if (!dropzone || !fileInput) return;

    ["dragenter", "dragover"].forEach(event => {
        dropzone.addEventListener(event, e => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(event => {
        dropzone.addEventListener(event, e => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", e => {
        if (e.dataTransfer && e.dataTransfer.files.length > 0) {
            handleSelectedFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", e => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });
}

function handleSelectedFile(file) {
    const errorBox = document.getElementById("uploadError");
    const selectedFileCard = document.getElementById("selectedFileCard");
    const uploadBtn = document.getElementById("uploadBtn");

    errorBox.classList.add("hidden");
    errorBox.textContent = "";

    const allowedExtensions = ["pdf", "docx", "jpg", "jpeg", "png"];
    const ext = file.name.split(".").pop().toLowerCase();

    if (!allowedExtensions.includes(ext)) {
        showError(errorBox, `Unsupported format ('.${ext}'). Please select a PDF, DOCX, JPG, JPEG, or PNG file.`);
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError(errorBox, "The selected file exceeds the 10 MB maximum upload size limit.");
        return;
    }

    selectedFile = file;

    document.getElementById("selectedFileName").textContent = file.name;
    document.getElementById("selectedFileSize").textContent = formatFileSize(file.size);
    selectedFileCard.classList.remove("hidden");
    uploadBtn.disabled = false;
}

function clearSelectedDocument() {
    selectedFile = null;
    latestAnalysisData = null;

    const fileInput = document.getElementById("documentInput");
    if (fileInput) fileInput.value = "";

    document.getElementById("selectedFileCard")?.classList.add("hidden");
    document.getElementById("uploadBtn") && (document.getElementById("uploadBtn").disabled = true);
    document.getElementById("uploadError")?.classList.add("hidden");
    document.getElementById("uploadSuccess")?.classList.add("hidden");
    document.getElementById("documentAnalysisSection")?.classList.add("hidden");
}

async function handleUploadDocument() {
    if (!selectedFile) return;

    const errorBox = document.getElementById("uploadError");
    const successBox = document.getElementById("uploadSuccess");
    const uploadBtn = document.getElementById("uploadBtn");
    const analysisSection = document.getElementById("documentAnalysisSection");

    errorBox.classList.add("hidden");
    successBox.classList.add("hidden");
    analysisSection.classList.add("hidden");

    const originalText = uploadBtn.innerHTML;
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = `<span class="spinner"></span> Analyzing with WarrantyCheck AI...`;

    try {
        const formData = new FormData();
        formData.append("document", selectedFile);

        const data = await safeFetchJson("/api/upload-document", {
            method: "POST",
            body: formData
        });

        latestAnalysisData = data.analysis || {};

        successBox.textContent = `Document '${data.filename}' processed successfully!`;
        successBox.classList.remove("hidden");

        renderDocumentAnalysis(data);
    } catch (err) {
        console.error("Document upload/analysis error:", err);
        showError(errorBox, err.message || "Failed to analyze document.");
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = originalText;
    }
}

function renderDocumentAnalysis(data) {
    const analysis = data.analysis || {};
    const analysisSection = document.getElementById("documentAnalysisSection");

    document.getElementById("docSummary").textContent = analysis.document_summary || "Document parsed successfully.";

    document.getElementById("docProduct").textContent = analysis.product_name || "Not found";
    document.getElementById("docBrand").textContent = analysis.brand || "Not found";
    document.getElementById("docModel").textContent = analysis.model_number || "Not found";
    document.getElementById("docSerial").textContent = analysis.serial_number || "Not found";
    document.getElementById("docPurchaseDate").textContent = analysis.purchase_date || "Not found";
    document.getElementById("docWarrantyYears").textContent = analysis.warranty_years ? `${analysis.warranty_years} Year(s)` : "Not found";
    document.getElementById("docInvoiceNumber").textContent = analysis.invoice_number || "Not found";

    // Missing info badges
    const missingContainer = document.getElementById("docMissingInfo");
    missingContainer.innerHTML = "";
    if (analysis.missing_information && analysis.missing_information.length > 0) {
        analysis.missing_information.forEach(item => {
            const badge = document.createElement("span");
            badge.className = "missing-badge";
            badge.textContent = `Missing: ${item}`;
            missingContainer.appendChild(badge);
        });
    } else {
        missingContainer.innerHTML = `<span style="color: var(--success); font-size: 13px; font-weight: 600;">All primary warranty fields detected.</span>`;
    }

    // Extracted text preview
    const previewEl = document.getElementById("docRawText");
    previewEl.textContent = data.extracted_text || "(No readable text extracted)";

    analysisSection.classList.remove("hidden");
    analysisSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ============================================================
// 5. AUTO-FILL WARRANTY FORM
// ============================================================

function applyExtractedToForm() {
    if (!latestAnalysisData) {
        alert("No extracted information available to apply.");
        return;
    }

    // Populate fields
    if (latestAnalysisData.product_name) {
        document.getElementById("productName").value = latestAnalysisData.product_name;
    }
    if (latestAnalysisData.brand) {
        document.getElementById("brand").value = latestAnalysisData.brand;
    }
    if (latestAnalysisData.model_number) {
        document.getElementById("modelNumber").value = latestAnalysisData.model_number;
    }
    if (latestAnalysisData.serial_number) {
        document.getElementById("serialNumber").value = latestAnalysisData.serial_number;
    }
    if (latestAnalysisData.purchase_date) {
        // If in YYYY-MM-DD format, set directly into date input
        const dateInput = document.getElementById("purchaseDate");
        const parsed = parseDateString(latestAnalysisData.purchase_date);
        if (parsed) {
            dateInput.value = parsed;
        }
    }
    if (latestAnalysisData.warranty_years) {
        const select = document.getElementById("warrantyYears");
        const match = String(latestAnalysisData.warranty_years).match(/\d+/);
        if (match) {
            select.value = match[0];
        }
    }

    // Switch to Warranty Tab
    switchTab("warranty");

    // Show confirmation notice
    const banner = document.getElementById("autofillNotice");
    if (banner) {
        banner.classList.remove("hidden");
        setTimeout(() => banner.classList.add("hidden"), 6000);
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function parseDateString(dateStr) {
    if (!dateStr) return "";
    // If already YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;

    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd}`;
    }
    return "";
}

// ============================================================
// 6. AI WARRANTY ASSISTANT (CHAT)
// ============================================================

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const sendBtn = document.getElementById("chatSendBtn");
    const message = input.value.trim();

    if (!message) return;

    // Append user message to chat UI
    appendChatBubble(message, "user");
    input.value = "";
    input.focus();

    // Disable send button
    sendBtn.disabled = true;

    // Show temporary typing indicator
    const typingId = appendChatBubble("WarrantyCheck AI is analyzing your question...", "assistant", true);

    try {
        const data = await safeFetchJson("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        // Remove typing indicator and append response
        removeChatBubble(typingId);
        const replyText = data.reply || data.response || "I could not generate a response. Please try again.";
        appendChatBubble(replyText, "assistant");
    } catch (err) {
        console.error("Chat error:", err);
        removeChatBubble(typingId);
        appendChatBubble(`Error: ${err.message || "Failed to reach AI agent."}`, "assistant");
    } finally {
        sendBtn.disabled = false;
    }
}

function appendChatBubble(text, sender, isTyping = false) {
    const container = document.getElementById("chatMessages");
    const bubble = document.createElement("div");
    const bubbleId = "chat_msg_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);

    bubble.id = bubbleId;
    bubble.className = `chat-bubble ${sender}`;

    const avatar = document.createElement("div");
    avatar.className = "chat-avatar";
    avatar.textContent = sender === "assistant" ? "AI" : "You";

    const content = document.createElement("div");
    content.className = "chat-content";

    if (isTyping) {
        content.innerHTML = `<span class="spinner spinner-dark" style="margin-right: 8px;"></span> ${escapeHtml(text)}`;
    } else {
        content.textContent = text;
    }

    bubble.appendChild(avatar);
    bubble.appendChild(content);

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    return bubbleId;
}

function removeChatBubble(bubbleId) {
    const bubble = document.getElementById(bubbleId);
    if (bubble) bubble.remove();
}

function handleChatKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function sendQuickPrompt(promptText) {
    const input = document.getElementById("chatInput");
    if (input) {
        input.value = promptText;
        sendChatMessage();
    }
}

// ============================================================
// 7. UTILITY FUNCTIONS
// ============================================================

function showError(element, message) {
    if (!element) return;
    element.textContent = message;
    element.classList.remove("hidden");
}

function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// 8. INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    setupDragAndDrop();

    // Attach listeners
    const warrantyForm = document.getElementById("warrantyForm");
    if (warrantyForm) {
        warrantyForm.addEventListener("submit", handleCheckWarranty);
    }

    const checkBtn = document.getElementById("checkWarrantyBtn");
    if (checkBtn) {
        checkBtn.addEventListener("click", handleCheckWarranty);
    }
});