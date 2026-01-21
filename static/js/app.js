const BASE_URL = window.location.origin;

// Store last prediction (for reporting)
let lastPrediction = {
    sourceType: null,   // "url" or "upload"
    imageUrl: null,
    imageFile: null,
    prediction: null
};

// ----------------------
// Image preview (upload)
// ----------------------
document.getElementById("imageFile").addEventListener("change", e => {
    const preview = document.getElementById("preview");
    if (!e.target.files.length) return;

    preview.src = URL.createObjectURL(e.target.files[0]);
    preview.style.display = "block";

    document.getElementById("reportBtn").style.display = "none";
});

// Hide report button when URL changes
document.getElementById("imageUrl").addEventListener("input", () => {
    document.getElementById("reportBtn").style.display = "none";
});


// ----------------------
// Predict from URL
// ----------------------
async function predictURL() {
    const url = document.getElementById("imageUrl").value;
    const resBox = document.getElementById("result");

    if (!url) {
        alert("Please enter an image URL");
        return;
    }

    resBox.innerHTML = "Analyzing image...";

    const res = await fetch(`${BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_url: url })
    });

    const data = await res.json();

    if (data.error) {
        resBox.innerHTML = `<b>Error:</b> ${data.error}`;
        return;
    }

    lastPrediction = {
        sourceType: "url",
        imageUrl: url,
        prediction: data.prediction,
        confidence: data.confidence,
        sfw_confidence: data.sfw_confidence,
        nsfw_confidence: data.nsfw_confidence
    };

    resBox.innerHTML = `
        <b>Prediction:</b> ${data.prediction}<br>
        <b>SFW Confidence:</b> ${data.sfw_confidence}<br>
        <b>NSFW Confidence:</b> ${data.nsfw_confidence}
    `;

    document.getElementById("reportBtn").style.display = "block";
}


// ----------------------
// Predict from Upload
// ----------------------
async function predictUpload() {
    const fileInput = document.getElementById("imageFile");
    const resBox = document.getElementById("result");

    if (!fileInput.files.length) {
        alert("Please select an image file");
        return;
    }

    resBox.innerHTML = "Analyzing image...";

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch(`${BASE_URL}/predict-upload`, {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    if (data.error) {
        resBox.innerHTML = `<b>Error:</b> ${data.error}`;
        return;
    }

    lastPrediction = {
        sourceType: "upload",
        prediction: data.prediction,
        confidence: data.confidence,
        sfw_confidence: data.sfw_confidence,
        nsfw_confidence: data.nsfw_confidence
    };

    resBox.innerHTML = `
        <b>Prediction:</b> ${data.prediction}<br>
        <b>SFW Confidence:</b> ${data.sfw_confidence}<br>
        <b>NSFW Confidence:</b> ${data.nsfw_confidence}
    `;

    document.getElementById("reportBtn").style.display = "block";
}


// ----------------------
// Report Incorrect Prediction
// ----------------------
async function reportPrediction() {
    if (!lastPrediction.sourceType) {
        alert("No prediction to report");
        return;
    }

    const formData = new FormData();
    formData.append("prediction", lastPrediction.prediction);
    formData.append("source_type", lastPrediction.sourceType);
    formData.append("confidence", lastPrediction.confidence);
    formData.append("sfw_confidence", lastPrediction.sfw_confidence);
    formData.append("nsfw_confidence", lastPrediction.nsfw_confidence);


    if (lastPrediction.sourceType === "url") {
        formData.append("image_url", lastPrediction.imageUrl);
    }

    const res = await fetch(`${BASE_URL}/report`, {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    alert(data.message || "Reported successfully");

    document.getElementById("reportBtn").style.display = "none";
}
