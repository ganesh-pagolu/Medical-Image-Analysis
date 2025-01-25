import os
import sys
import uuid
import json
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import google.generativeai as genai

# Get the directory of the current script
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([
    os.path.join(app_dir, 'chatBot_web'),
    os.path.join(app_dir, 'Bone_Fracture_Detection'),
    os.path.join(app_dir, 'MRIimage')
])

from logic.model_predictor import BoneFracturePredictor
from MRIimage.predict import api_predict

# Set up Google API key
GOOGLE_API_KEY = "AIzaSyB4ddlSw_AGLu40IyuPzZ9ij4DkYD6RthE"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-8b")

# Set up Flask application
template_dir = os.path.join(app_dir, "chatBot_web", "templates")
static_dir = os.path.join(app_dir, "chatBot_web", "static")
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# App configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize SQLAlchemy, Bcrypt, and LoginManager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Project directory structure
project_folder = os.path.dirname(os.path.abspath(__file__))
temp_upload_dir = os.path.join(project_folder, "temp_upload_file")
os.makedirs(temp_upload_dir, exist_ok=True)

# Initialize predictors
bone_predictor = BoneFracturePredictor(os.path.join(project_folder, 'Bone_Fracture_Detection'))

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
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
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/ctscan')
@login_required
def ctscan():
    return render_template('ctscan.html')

@app.route('/gemini-text', methods=["POST"])
def gemini_text():
    try:
        prompt_text = request.get_json().get('text_gemini')
        response = model.generate_content(prompt_text)
        if response and response.text:
            return jsonify({"gemini_message": response.text})
        return jsonify({"error": "API error or no response"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

        prediction = api_predict(image_path)
        os.remove(image_path)

        response = {
            'patient_name': patient_name,
            'bone_type': 'N/A',
            'fracture_status': json.loads(prediction)['predicted_class']
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
@login_required
def predict_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify({'error': 'No image selected'}), 400

    try:
        image_path = os.path.join(temp_upload_dir, image_file.filename)
        image_file.save(image_path)

        bone_type_result = bone_predictor.predict(image_path)
        result = bone_predictor.predict(image_path, bone_type_result)
        os.remove(image_path)

        response = {
            'bone_type': bone_type_result.strip(),
            'fracture_status': result.strip()
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            flash("Email already exists.")
            return redirect(url_for('register'))

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')

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
            flash('Login failed. Check your credentials.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
