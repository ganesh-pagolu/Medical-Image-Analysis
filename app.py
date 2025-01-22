import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re
import google.generativeai as genai
import uuid
import json  
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(app_dir, 'chatBot_web'))
#remove if exist since no longer is used here in your models on this classes folder /Bone_Fracture_Detection or /logic

#sys.path.append(os.path.join(app_dir, 'Bone_Fracture_Detection')) #not here
# add path import since you are reusing all logic prediction now and using only 1 module not 2 separate of Bone type from /logic  . This old path module with class we remove
sys.path.append(os.path.join(app_dir, 'CTimage')) # import project model

# Remove old logic model.
#from logic.model_predictor import BoneFracturePredictor

#import the model here instead of using it before and  now this single one do type+fracture or what models has been defined before. This will ensure only use one instead of another method  .
from predict import api_predict # the function of other prediction

# Set up Google API key
GOOGLE_API_KEY = "AIzaSyB4ddlSw_AGLu40IyuPzZ9ij4DkYD6RthE"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-8b")

# Template and Static directories
template_dir = os.path.join(app_dir, "chatBot_web", "templates")
static_dir = os.path.join(app_dir, "chatBot_web", "static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# App Configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize SQLAlchemy, Bcrypt, LoginManager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Project directory structure and temporary uploads
project_folder = os.path.dirname(os.path.abspath(__file__))
temp_upload_dir = os.path.join(project_folder, "temp_upload_file")

# Remove here since not being called and this way is unique and only logic of one file

# Initialize Bone Fracture Prediction model #  REMOVE OLD MODEL
#predictor = BoneFracturePredictor(os.path.join(project_folder, 'Bone_Fracture_Detection'))


# User model for DB
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


# User loader function for login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Gemini text route
@app.route("/gemini-text", methods=["POST"])
def gemini_text():
    try:
        prompt_text = request.get_json().get('text_gemini')
        print('getting message for the gemini prompt from fetch :  ', prompt_text);
        response = model.generate_content(prompt_text)
        if response and response.text:
            print(f"success Gemini Api text : {response.text}")
            return jsonify({"gemini_message": response.text})
        return jsonify({"error": "API error or No response"}), 500
    except Exception as e:
        print("Internal Error Gemini API Request text:" + str(e))
        return jsonify({'error': "Error with gemini API connection request : " + str(e)}), 500


# Basic Routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# Ctscan route for user that are logged in
@app.route('/ctscan')
@login_required
def ctscan():
    return render_template('ctscan.html')

#Chat bot for authenticated users.
@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')


# Handle POST request by forms by `ctscan.html` to invoke predictions.
@app.route('/ctscan_predict', methods=['POST'])
@login_required
def ctscan_predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['file']
    patient_name = request.form.get('patient_name')

    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    try:
        file_extension = os.path.splitext(image_file.filename)[1]
        unique_file_name = f"{uuid.uuid4()}{file_extension}"
        image_path = os.path.join(temp_upload_dir, unique_file_name)

        image_file.save(image_path)
        print(f"Image saved to : {image_path}")

         # old  double methods not here # we use new API imported logic methods to call to replace it

         # bone_type_result = predictor.predict(image_path)
         #   print(f"Result by Model type of {bone_type_result}")
         # result = predictor.predict(image_path, bone_type_result)

         #Call api_predict method function directly now and remove class methods to do predictions .
       #  prediction = json.loads(api_predict(image_path))  # api response is string need parsed as json since this old logic do response string
        prediction  = api_predict(image_path)  # call only response to this since return is also json with  key .  remove conversion here since it is json by string no conversion here to another JSON objet needed in that Flask code
        #  prediction = api_predict(image_path).replace('"', '').replace('\'','')
       #  remove above conversion . since you are getting text output  no need replace character with this way of JSON , since this JSON output, will send automatically string property values

        # delete image when it was consumed from process api_prediction

        os.remove(image_path)
        # build correct  response of same type. from your api of old models format to your page view

        response = {
           'patient_name': patient_name,
           'result_status': json.loads(prediction)['predicted_class'] # ensure use your name property from returned data response  'predicted_class'

         }
        return jsonify(response) #  Return from this part ,since all works
    except Exception as e:
         print("Error on response flask  side processing ", str(e))
         return jsonify({'error': str(e)}), 500

# Registration Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist ,Please chose another One..")
            return redirect(url_for('register'))

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been registered. Please Login Now.")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('chatbot'))
        else:
            flash('Login failed. Please check username and password.')
    return render_template('login.html')

# Logout route for the user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Main App Start Point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(os.path.join(project_folder, "temp_upload_file"), exist_ok=True)
    app.run(debug=True)