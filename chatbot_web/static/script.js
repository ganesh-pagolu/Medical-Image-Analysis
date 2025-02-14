document.addEventListener('DOMContentLoaded', function () {
  const chatHistory = document.querySelector('.chat-history');
  const chatInputText = document.getElementById("prompt-input");
  const sendTextBtn = document.getElementById("send-text-btn");
  const imageInput = document.getElementById("image-input");
  const analyzeBtn = document.getElementById("analyze-btn");
  const analysisType = document.getElementById("analysis-type");

  function appendMessage(message, sender, imageUrl = null) {
      const messageDiv = document.createElement('div');
      messageDiv.classList.add('chat-message', sender);

      if (imageUrl) {
          const imgElement = document.createElement('img');
          imgElement.src = imageUrl;
          imgElement.style.maxWidth = "200px";
          imgElement.style.display = "block";
          imgElement.style.marginBottom = "5px";
          messageDiv.appendChild(imgElement);
      }

      messageDiv.innerHTML += message;
      chatHistory.appendChild(messageDiv);
      chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // Handle Gemini text input
  sendTextBtn.addEventListener('click', async function () {
      const promptText = chatInputText.value.trim();
      if (!promptText) {
          alert('Please enter a message.');
          return;
      }
      appendMessage(promptText, 'user-message');
      chatInputText.value = '';

      try {
          const response = await fetch("/gemini-text", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text_gemini: promptText })
          });

          if (!response.ok) {
              throw new Error("Failed to get response from Gemini.");
          }

          const data = await response.json();
          appendMessage(formatGeminiResponse(data.gemini_message), "bot-message");
      } catch (error) {
          appendMessage("Error connecting to Gemini API: " + error.message, "bot-message");
      }
  });

  // Handle Image Upload and Analysis
  analyzeBtn.addEventListener('click', async function () {
      const imageFile = imageInput.files[0];

      if (!imageFile) {
          alert("Please select an image file.");
          return;
      }

      appendMessage("Analyzing image...", 'user-message', URL.createObjectURL(imageFile));

      const formData = new FormData();

      if (analysisType.value === "bone") {
          formData.append('image', imageFile);  // Backend expects 'image' for bone fracture
      } else {
          formData.append('file', imageFile);  // Backend expects 'file' for CT scan
      }

      let apiUrl = analysisType.value === "bone" ? "/predict" : "/ctscan_predict";

      try {
          const response = await fetch(apiUrl, {
              method: "POST",
              body: formData
          });

          if (!response.ok) {
              const errorText = await response.text();
              throw new Error("Server response: " + errorText);
          }

          const data = await response.json();
          let message = analysisType.value === "bone"
              ? `Bone Type: ${data.bone_type} <br> Result: ${data.fracture_status}`
              : `Result: ${data.fracture_status}`;

          appendMessage(message, "bot-message");

          // ✅ Send to Gemini ONLY if a fracture or issue is detected
          if ((analysisType.value === "bone" && data.fracture_status.toLowerCase() !== "normal") ||
              (analysisType.value === "ctscan" && data.fracture_status.toLowerCase() !== "normal")) {

              let geminiPrompt = analysisType.value === "bone"
                  ? `A bone fracture has been detected. Please provide 2 immediate precautionary and safety measures in a short manner. Make sure it is not suggested that the patient should visit a hospital/doctor.`
                  : `The CT scan shows ${data.fracture_status} abnormality. Please provide 2 immediate precautionary safety measures in short related to the ${data.fracture_status} .Make sure it is not suggested that the patient should visit a hospital/doctor/monitering symptoms.`;

              sendToGemini(geminiPrompt);
          }

      } catch (error) {
          appendMessage("Error processing image: " + error.message, "bot-message");
      }

      imageInput.value = null; // Reset file input
  });

  async function sendToGemini(prompt) {
      try {
          const response = await fetch("/gemini-text", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text_gemini: prompt })
          });

          if (!response.ok) {
              throw new Error("Failed to get response from Gemini.");
          }

          const data = await response.json();
          appendMessage(`<b>Please follow the below safety steps:</b><br>${formatGeminiResponse(data.gemini_message)}`, "bot-message");
      } catch (error) {
          appendMessage("Error connecting to Gemini API: " + error.message, "bot-message");
      }
  }

  function formatGeminiResponse(geminiMessage) {
      return geminiMessage.split('\n').map(line => {
          if (line.startsWith('**')) {
              return `<b>${line.substring(2)}</b>`;
          }
          if (line.startsWith('* ')) {
              return `<li>${line.substring(2)}</li>`;
          }
          return `<p>${line}</p>`;
      }).join('');
  }
});
