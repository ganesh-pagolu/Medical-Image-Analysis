document.addEventListener('DOMContentLoaded', function () {
    const chatHistory = document.querySelector('.chat-history');
    const imageInput = document.getElementById('image-input');
    const sendBtn = document.getElementById('send-btn');
    const imageInputContainer = document.querySelector('.chat-input-area');
    /* removing escapeHTML  due logical and unecessary process after proper flask steps or format */
    /*
   const escapeHTML = (str) => str.replace(/[&<>"']/g, (match) => {
        switch(match) {
            case '&': return '&';
            case '<': return '<';
            case '>': return '>';
            case '"': return '"';
            case '\'': return ''';
            default: return match;
          }
       });
    */
    function appendMessage(message, sender, imageUrl = null){
        const messageDiv = document.createElement('div')

        if (imageUrl)
        {
            const imgElement=document.createElement('img')
            imgElement.src = imageUrl;
           imgElement.style.maxWidth="200px"
            messageDiv.appendChild(imgElement)

        }
          messageDiv.innerHTML +=message //also text format is used (removed logic part from  output)


          messageDiv.classList.add("chat-message")
           messageDiv.classList.add(sender)
           chatHistory.appendChild(messageDiv);
           chatHistory.scrollTop= chatHistory.scrollHeight

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
                         //removed here escape as a main logic error and bug also check it console
                       message = `Bone Type: ${data.bone_type} <br> Result: ${data.fracture_status}` // also no value cleaning parts now directly used for js part after removing code

                    } else {
                        message = 'error :' + data.error
                       }

                appendMessage(message,"bot-message")
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