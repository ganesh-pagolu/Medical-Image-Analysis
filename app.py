import os
from flask import Flask, render_template, request, jsonify
import sys

# Get the directory of the current script (app.py)
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(app_dir,'chatBot_web'))
sys.path.append(os.path.join(app_dir,'Bone_Fracture_Detection'))

from logic.model_predictor import BoneFracturePredictor
# set app template folder location to serve templates and static folders correctly at specified location
template_dir = os.path.join(app_dir,"chatBot_web","templates")
static_dir = os.path.join(app_dir,"chatBot_web", "static")

# correct Flask init using the above template_dir,static_dir to discover both templates as well as all statics file like .css .js .images , to be directly accessed with path  url_for
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# Project directory structure
project_folder = os.path.dirname(os.path.abspath(__file__))
# Initialize prediction class
predictor = BoneFracturePredictor(os.path.join(project_folder,'Bone_Fracture_Detection'))


@app.route('/')
def home():
    return render_template('index.html')  # Route specific functions

@app.route('/about')
def about():
    return render_template('about.html')  #about page
@app.route('/contact')
def contact():
  return render_template('contact.html')    #contact page


@app.route('/chatbot')
def chatbot():
   return render_template('chatbot.html')   #chatbox main path for chatbot (that we already defined routes by this function earlier )



@app.route('/predict', methods=['POST'])
def predict_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400


    try:
       # temporary store in upload file system
       image_path = os.path.join(project_folder,"temp_upload_file", image_file.filename) # root dir upload folder
       image_file.save(image_path)
       print(f"Image saved to : {image_path}")  # <--- ADD THIS LOG
       bone_type_result = predictor.predict(image_path)
       print(f"Result by Model type of {bone_type_result}") #  <--- ADD THIS LOG
       result = predictor.predict(image_path, bone_type_result)

       #delete uploaded file
       os.remove(image_path)
       response = {
                'bone_type': bone_type_result.strip(),
                 'fracture_status': result.strip()
           }

       return jsonify(response)

    except Exception as e:
        print("Error on response flask  side processing " ,str(e))

        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':

    os.makedirs(os.path.join(project_folder,"temp_upload_file"), exist_ok=True) #make it as folder not as file
    app.run(debug=True)