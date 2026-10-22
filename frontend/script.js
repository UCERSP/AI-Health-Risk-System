const healthForm = document.getElementById("healthForm");

const result = document.getElementById("result");
const resultTitle = document.getElementById("resultTitle");
const riskScore = document.getElementById("riskScore");
const resultMessage = document.getElementById("resultMessage");
const predictionResult = document.getElementById("predictionResult");


healthForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const age = document.getElementById("age").value;
    const height = document.getElementById("height").value;
    const weight = document.getElementById("weight").value;
    const systolic = document.getElementById("systolic").value;
    const diastolic = document.getElementById("diastolic").value;
    const glucose = document.getElementById("glucose").value;


    const data = {
        name: name,
        age: age,
        height: height,
        weight: weight,
        systolic: systolic,
        diastolic: diastolic,
        glucose: glucose
    };


    try {
        const response = await fetch(
            "/analyze",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            }
        );


        const output = await response.json();


        if (!response.ok) {
            alert(output.error || "Something went wrong.");
            return;
        }


        // ------------------------------------------------
        // Overall risk
        // ------------------------------------------------

        resultTitle.textContent =
            "Assessment for " + output.name;

        // Short text keeps the risk inside the circle
        if (output.risk === "Low Risk") {
            riskScore.textContent = "LOW";
        } else if (output.risk === "Moderate Risk") {
            riskScore.textContent = "MODERATE";
        } else {
            riskScore.textContent = "HIGH";
        }

        predictionResult.textContent =
            "Overall Risk: " + output.risk;


        // ------------------------------------------------
        // Precautions list
        // ------------------------------------------------

        let precautionsHTML = "";

        if (
            Array.isArray(output.precautions) &&
            output.precautions.length > 0
        ) {
            precautionsHTML = output.precautions
                .map(function (item) {
                    return "<li>" + item + "</li>";
                })
                .join("");
        } else {
            precautionsHTML =
                "<li>Continue healthy lifestyle habits and routine health monitoring.</li>";
        }


        // ------------------------------------------------
        // Readable result layout
        // ------------------------------------------------

        resultMessage.innerHTML = `

            <div class="assessment-details">

                <div class="health-detail">
                    <div class="detail-label">BMI</div>
                    <div class="detail-value">
                        ${output.bmi}
                    </div>
                    <div class="detail-category">
                        ${output.bmi_category}
                    </div>
                </div>


                <div class="health-detail">
                    <div class="detail-label">Blood Pressure</div>
                    <div class="detail-value">
                        ${output.blood_pressure}
                    </div>
                    <div class="detail-category">
                        ${output.bp_category}
                    </div>
                </div>


                <div class="health-detail">
                    <div class="detail-label">Glucose</div>
                    <div class="detail-value">
                        ${output.glucose} mg/dL
                    </div>
                    <div class="detail-category">
                        ${output.glucose_category}
                    </div>
                </div>

            </div>


            <div class="assessment-section">
                <h3>Why this assessment?</h3>

                <p>
                    ${output.explanation}
                </p>
            </div>


            <div class="assessment-section">
                <h3>Precautions</h3>

                <ul class="precautions-list">
                    ${precautionsHTML}
                </ul>
            </div>


            <div class="assessment-note">
                ${output.note}
            </div>

        `;


        // ------------------------------------------------
        // Show result card
        // ------------------------------------------------

        result.classList.remove("hidden");

        result.scrollIntoView({
            behavior: "smooth"
        });

    } catch (error) {

        alert(
            "Backend se connection nahi ho pa raha. " +
            "Please check that Flask is running."
        );

        console.error(error);
    }
});
