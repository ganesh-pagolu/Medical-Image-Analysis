document.addEventListener('DOMContentLoaded', function () {
  const chatHistory = document.querySelector('.chat-history');
  const imageInput = document.getElementById('image-input');
  const sendBtn = document.getElementById('send-btn');

const chatInputText = document.getElementById("prompt-input")   // change name or from id


function appendMessage(message, sender, imageUrl = null) {
const messageDiv = document.createElement('div');
messageDiv.classList.add('chat-message');
     messageDiv.classList.add(sender);
    if (imageUrl) {
   const imgElement = document.createElement('img');
      imgElement.src = imageUrl;
    imgElement.style.maxWidth = "200px";
     imgElement.style.display = "block";
      imgElement.style.marginBottom = "5px";
   messageDiv.appendChild(imgElement);
 }
    const lines = message.split('<br>');
     lines.forEach(line => {
          const lineElement = document.createElement('div');
     lineElement.innerHTML = line.trim();
    messageDiv.appendChild(lineElement);
    });
     chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
 }


      chatInputText.addEventListener('keydown', async function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
      const promptText = chatInputText.value.trim();
           if (!promptText) {
      alert('Please Input your prompt or type your question to send');
               return;
    }
       appendMessage(promptText, 'user-message');
       chatInputText.value = '';
       try {
const geminiResponse = await fetch("/gemini-text", {
    method: "POST",
       headers: {
      "Content-Type": "application/json",
           },
        body: JSON.stringify({ text_gemini: promptText })
       });
   if (!geminiResponse.ok) {
 const messageError = await geminiResponse.json();
    appendMessage('API response : Error: ' + messageError.error, 'bot-message');
      throw new Error('Failed : Network, Google API not valid ');
         }
    const geminiData = await geminiResponse.json();
 appendMessage(formatGeminiResponse(geminiData.gemini_message), "bot-message");
 } catch (error) {
             appendMessage('Error in API Google, connection: ' + error.message, 'bot-message')
         }
      }
  });

      sendBtn.addEventListener('click', function () {
 const imageFile = imageInput.files[0];
     if (!imageFile) {
     alert("please select the file");
           return;
      }
      appendMessage("Analyzing ... ", 'user-message', URL.createObjectURL(imageFile));
  const formData = new FormData();
    formData.append('image', imageFile);
  fetch('/predict', {
   method: "POST",
      body: formData
    }).then(response => {
        return response.json();
         }).then(data => {
        let message = "";
     if (data.bone_type) {
      message = `Bone Type: ${data.bone_type} <br> Result: ${data.fracture_status}`;
           appendMessage(message, "bot-message");
           const geminiPrompt = `Given a medical image analysis, the bone type is "${data.bone_type}" and the fracture status is "${data.fracture_status}". Can you provide 2-3 precautionary and safety measures  ?`;
          sendToGemini(geminiPrompt);
  } else {
           message = 'error :' + data.error;
          appendMessage(message, "bot-message");
      }
        imageInput.value = null;
  }).catch(error => {
     appendMessage("Something error in response", "bot-message");
       imageInput.value = null;
    });
     });
    async function sendToGemini(prompt) {
  try {
     const geminiResponse = await fetch("/gemini-text", {
       method: "POST",
     headers: {
       "Content-Type": "application/json",
          },
 body: JSON.stringify({ text_gemini: prompt }),
     });
if (!geminiResponse.ok) {
          const messageError = await geminiResponse.json();
           appendMessage('API response : Error: ' + messageError.error, 'bot-message');
              throw new Error('Failed : Network, Google API not valid ');
}
      const geminiData = await geminiResponse.json();
    appendMessage(formatGeminiResponse(geminiData.gemini_message), "bot-message");
    } catch (error) {
   appendMessage('Error in API Google, connection: ' + error.message, 'bot-message');
    }
   }

   function formatGeminiResponse(geminiMessage) {
          const formattedMessage = geminiMessage.split('\n').map(line => {
      if (line.trim().startsWith('**')) {
 const content = line.trim().substring(2).trim().replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
       return  `${content} `;
}
     if (line.trim().startsWith('* ')) {
return `<li>${line.trim().substring(2).trim()}</li>`;
      }
         if (line.trim().startsWith('## ')) {
  return `<h2>${line.trim().substring(3).trim()}</h2>`;
      }
        if (line.trim().startsWith('### ')) {
      return `<h3>${line.trim().substring(4).trim()}</h3>`;
     }
         if(line.trim().length===0) return '';
             return `<p>${line.trim()}</p>`;
  }).join('');
return  `<div>${formattedMessage}</div>` ;
    }
});