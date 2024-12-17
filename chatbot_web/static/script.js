document.addEventListener('DOMContentLoaded', function () {
  const chatHistory = document.querySelector('.chat-history');
 const imageInput = document.getElementById('image-input');
const sendBtn = document.getElementById('send-btn');
/* removed these UI elements and js event related or any dynamic property setting for slider
   const opacitySlider = document.getElementById('opacitySlider');

 const opacityValueDisplay = document.getElementById('opacityValue') // html  tag that use that dynamic display data or any slider info also from HTML
      const mainBackground = document.querySelector('main::before')
          /*   removed as well this JS codes , related to these tag event or property related operations as these specific methods related html elements are now not there with from template also this tag selector not working anymore without related element

   opacitySlider.addEventListener('input', function(){
         const  currentOpacity = opacitySlider.value; //value capture from UI
mainBackground.style.opacity = currentOpacity // set specific property, which  do css styles manipulation, using our id of div

      opacityValueDisplay.textContent = currentOpacity   //update any  HTML, that we wanted also real-time dynamically, in related area.


             })

      */

    /*other functions for only chatbot related methods are here and all are unchanged from older questions*/

    function appendMessage(message, sender, imageUrl = null) {
      // Create a container for the message
      const messageDiv = document.createElement('div');
    
      // Add the sender's class for styling
      messageDiv.classList.add('chat-message');
      messageDiv.classList.add(sender);
    
      // Check if an image URL is provided
      if (imageUrl) {
        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.style.maxWidth = "200px"; // Restrict image width
        imgElement.style.display = "block"; // Ensure image is on its own line
        imgElement.style.marginBottom = "5px"; // Add spacing between image and text
        messageDiv.appendChild(imgElement);
      }
    
      // Handle multi-line text messages
      const lines = message.split('<br>'); // Split the message by <br> tag
      lines.forEach(line => {
        const lineElement = document.createElement('div');
        lineElement.textContent = line.trim(); // Use textContent to avoid rendering HTML
        messageDiv.appendChild(lineElement);
      });
    
      // Append the entire message container to the chat history
      chatHistory.appendChild(messageDiv);
    
      // Scroll to the bottom of the chat history
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }


 sendBtn.addEventListener('click', function(){
console.log("click event for the 'send' start...");

const imageFile = imageInput.files[0];


    if(!imageFile){
console.log("no file found");


        alert("please select the file")

      return

  }

     appendMessage("Analyzing ... ", 'user-message', URL.createObjectURL(imageFile) )
const formData = new FormData();
formData.append('image', imageFile);
 console.log("formData image file is ", formData.get('image'))
fetch('/predict',{
method: "POST",

body : formData

}).then(response => {
console.log("response status ",response.status )

    return response.json();

  })
  .then(data => {

  console.log("success:",data);

  let  message = ""

  if (data.bone_type)
     {


      const message = `Bone Type: ${data.bone_type} <br> Result: ${data.fracture_status}`
      appendMessage(message,"bot-message")
    } else {

 message = 'error :' + data.error
}
// appendMessage(message,"bot-message")
imageInput.value = null;
console.log( "clicked action end " );

 })
.catch(error =>{
console.log("Error : at js", error)

  appendMessage("Something error in response","bot-message")
   imageInput.value = null;

    console.log("js side response or json parsing error" , error )
})

})

});