from flask import Flask, url_for, flash, redirect, render_template, request, Response
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from form import registrationForm, loginForm
import numpy as np
from models import Conversion
from flask_login import current_user
from flask_login import fresh_login_required
from models import db, User
from flask_bcrypt import Bcrypt
import os
import cv2
from dotenv import load_dotenv
import img2pdf
load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
# Secret key for flash/session
app.config['SECRET_KEY'] = 'harish'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
# Folder configurations
UPLOAD_FOLDER = os.path.join('static', 'uploads')
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg', 'gif'}

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)


# Check allowed file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# Image Processing Function
def processImg(filename, operation):
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    name = filename.rsplit('.', 1)[0]

    if operation == "cgrey":
        img = cv2.imread(input_path)
        if img is None:
            return None
        imgprocessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        output_filename = f"{name}_grey.jpg"
        cv2.imwrite(os.path.join(STATIC_FOLDER, output_filename), imgprocessed)
        return output_filename

    elif operation == "cpng":
        img = cv2.imread(input_path)
        output_filename = f"{name}.png"
        cv2.imwrite(os.path.join(STATIC_FOLDER, output_filename), img)
        return output_filename

    elif operation == "cjpg":
        img = cv2.imread(input_path)
        output_filename = f"{name}.jpg"
        cv2.imwrite(os.path.join(STATIC_FOLDER, output_filename), img)
        return output_filename

    elif operation == "cwebp":
        img = cv2.imread(input_path)
        output_filename = f"{name}.webp"
        cv2.imwrite(os.path.join(STATIC_FOLDER, output_filename), img)
        return output_filename

    elif operation == "cpdf":
        output_filename = f"{name}.pdf"
        output_path = os.path.join(STATIC_FOLDER, output_filename)

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(input_path))

        return output_filename

    return None


# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = registrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
            email=form.email.data
        )
        db.session.add(user)
        db.session.commit()
        users = User.query.all()
        print("\n===== REGISTERED USERS =====")
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}")
        print("============================\n")

        flash(f"Account created successfully {form.username.data}", "success")
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = loginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login Successful", "success")
            return redirect(url_for('edit'))
        else:
            flash("Invalid Credentials", "danger")

    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('home'))

@app.route('/history', methods = ['GET', 'POST'])
@login_required
def history():
    conversions = Conversion.query.filter_by(user_id=current_user.id)\
                    .order_by(Conversion.created_at.desc()).all()

    return render_template('history.html', conversions=conversions)

from flask import Response

@app.route('/image/<int:id>/<type>')
@login_required
def get_image(id, type):
    conversion = Conversion.query.get_or_404(id)

    if type == "before":
        return Response(conversion.image_before, mimetype='image/jpeg')
    elif type == "after":
        return Response(conversion.image_after, mimetype='image/jpeg')
@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':

        operation = request.form.get('operation')

        if 'file' not in request.files:
            flash("No file selected", "danger")
            return redirect(url_for('home'))

        file = request.files['file']

        if file.filename == '':
            flash("No file selected", "danger")
            return redirect(url_for('home'))

        if file and allowed_file(file.filename):

            # Read original file bytes
            file_bytes = file.read()

            # Convert bytes to OpenCV image
            npimg = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

            if img is None:
                flash("Invalid image", "danger")
                return redirect(url_for('home'))

            # Process image
            if operation == "cgrey":
                processed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                processed = img

            # Convert processed image to bytes
            _, buffer = cv2.imencode('.jpg', processed)
            processed_bytes = buffer.tobytes()

            # Save to DB
            conversion = Conversion(
                image_before=file_bytes,
                image_after=processed_bytes,
                user_id=current_user.id
            )

            db.session.add(conversion)
            db.session.commit()

            flash(
                "File converted successfully!" f"<a href='{url_for('get_image', id=conversion.id, type='after')}' "
                f"target='_blank'>Download here</a>", "success")
                

            return redirect(url_for('home'))

    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
