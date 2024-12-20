import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sys
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re  # regural expression
import google.generativeai as genai

# Get the directory of the current script (app.py)
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(app_dir, 'chatBot_web'))
sys.path.append(os.path.join(app_dir, 'Bone_Fracture_Detection'))

from logic.model_predictor import BoneFracturePredictor

# Set up Google API key
GOOGLE_API_KEY = "AIzaSyB4ddlSw_AGLu40IyuPzZ9ij4DkYD6RthE"  # Replace with real API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-8b")

# set app template folder location to serve templates and static folders correctly at specified location
template_dir = os.path.join(app_dir, "chatBot_web", "templates")
static_dir = os.path.join(app_dir, "chatBot_web", "static")

# correct Flask init using the above template_dir,static_dir to discover both templates as well as all statics file like .css .js .images , to be directly accessed with path  url_for
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Secret Key for sessions
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key

# Database Configuration - Use SQLite for simplicity
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Password Hashing
bcrypt = Bcrypt(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # the page if  un authorized trying to access restricted resource


# Project directory structure
project_folder = os.path.dirname(os.path.abspath(__file__))

# Initialize prediction class
predictor = BoneFracturePredictor(os.path.join(project_folder, 'Bone_Fracture_Detection'))

# User Model for Database (SQLAlchemy Model)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # unique by email also, in our form and db
    password = db.Column(db.String(80), nullable=False)


# User loader function - load user object on every request if exist from DB
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Define the new routes for the gemini text example and text+image calls
@app.route("/gemini-text", methods=["POST"])  # new route,  for handling  any POST action and calls for the api.
def gemini_text():
    try:
        prompt_text = request.get_json().get('text_gemini')  # read or extract content from  request as json and `key`
        print('getting message for the gemini prompt from fetch :  ', prompt_text);
        response = model.generate_content(prompt_text)  # make external api google Gemini  request
        # Process response
        if response and response.text:  # check first the response value.
            print(f"success Gemini Api text : {response.text}")
            return jsonify({"gemini_message": response.text})  # send response as json, with the proper property names of keys that will handle also json.
        return jsonify({"error": "API error or No response"}), 500  # Return json response and return code 500 in that json if issue
    except Exception as e:
        print("Internal Error Gemini API Request text:" + str(e))  # debug reason
        return jsonify({'error': "Error with gemini API connection request : " + str(e)}), 500  # return all exceptions
# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/chatbot')
@login_required  # Protected Route by @login_required wrapper check if logged user
def chatbot():
    return render_template('chatbot.html')


@app.route('/predict', methods=['POST'])
@login_required
def predict_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    try:
        # temporary store in upload file system
        image_path = os.path.join(project_folder, "temp_upload_file", image_file.filename)  # root dir upload folder
        image_file.save(image_path)
        print(f"Image saved to : {image_path}")
        bone_type_result = predictor.predict(image_path)
        print(f"Result by Model type of {bone_type_result}")
        result = predictor.predict(image_path, bone_type_result)

        # delete uploaded file
        os.remove(image_path)
        response = {
            'bone_type': bone_type_result.strip(),
            'fracture_status': result.strip()
        }
        return jsonify(response)

    except Exception as e:
        print("Error on response flask  side processing ", str(e))
        return jsonify({'error': str(e)}), 500
# --- Login, Logout & Register ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']  # email to validate and username by unique constrants on model table
        password = request.form['password']
        confirm_password = request.form['confirm_password']  # check confirm pasword match also

        # Validation email by using Regex
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address.')
            return redirect(url_for('register'))
        # Validation that confirms matching password
        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # generate hash from text password
        # Check if username is already registered , changed username by email field by constraints on User class
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist ,Please chose another One..")
            return redirect(url_for('register'))  # re render register again

        new_user = User(email=email, password=hashed_password)  # model user changed by username as email here as unique field for form and validation for checking db entry for all forms ,and also in table user db as unique
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has been registered. Please Login Now.")
        return redirect(url_for('login'))  # login after registering succesfully
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']  # change for email login in our app instead of username ,form field also needs changed
        password = request.form['password']
        user = User.query.filter_by(email=email).first()  # find email user id on current text credential from form user , to check further condition
        if user and bcrypt.check_password_hash(user.password, password):  # hash checking while logging by current entered plain text  with saved hash text
            login_user(user)
            return redirect(url_for('chatbot'))  # redirect to the main chatbot route path,protected using login required decorater, after login
        else:
            flash('Login failed. Please check username and password.')
    return render_template('login.html')
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(os.path.join(project_folder, "temp_upload_file"), exist_ok=True)  # make it as folder not as file
    app.run(debug=True)