document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById("upload-form");
    const imageUpload = document.getElementById("imageUpload");
    const resultDiv = document.getElementById("result");
    const loadingDiv = document.getElementById("loading");
    const errorDiv = document.getElementById("error-message");
    const nameInput = document.getElementById("name");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        loadingDiv.style.display = "block";
        resultDiv.innerText = "";
        errorDiv.style.display = "none";

        const file = imageUpload.files[0];
        const patientName = nameInput.value;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("patient_name", patientName);

        try {
            const response = await fetch("/ctscan_predict", {   //changed call from `predict` to `ctscan_predict`
                method: "POST",
                body: formData
            });

            loadingDiv.style.display = "none";

            if (!response.ok) {
                console.log("Error response form Server  : ", response);
                const errorResponse = await response.json();

                throw new Error(errorResponse.error || "An unknown error occurred during upload.");
            }
            const data = await response.json();
            console.log("Response Success From server JSON response :  ",data );

             resultDiv.innerHTML = `
                 <p><b>Patient Name:</b> ${data.patient_name}</p>
                  <p><b>Result:</b> ${data.fracture_status}</p>
              `;
        } catch (error) {
            loadingDiv.style.display = "none";
             errorDiv.style.display = "block";
             console.error("There has been an error with this fetch : " , error);
            errorDiv.innerText = `Error: ${error.message} , please make sure all requirment are satisfied for the image size, and correct file`;
        }
    });
});