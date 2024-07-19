# import Dependencies
import os
import numpy as np
import pandas as pd
from six import reraise
import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import preprocess_input
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from flask import Flask , redirect , url_for , request , render_template, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy


# Create a Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/', methods=['GET'])
def index():
    if session.get('logged_in'):
        return render_template('home.html')
    else:
        return render_template('index.html', message="Invalid username and password")
    
@app.route('/graph',methods=['GET'])
def graph():
    return render_template('graph2.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db.session.add(User(username=request.form['username'], password=request.form['password']))
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('index.html', message="User Already Exists")
    else:
        return render_template('register.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u = request.form['username']
        p = request.form['password']
        data = User.query.filter_by(username=u, password=p).first()
        if data is not None:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('index.html', message="Incorrect Details")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


# load the model
Model_path = "model.h5"
model = load_model(Model_path)


# Create a function to take and image and predict the class
def model_predict(img_path , model):
    print(img_path)
    img = image.load_img(img_path , target_size=(299 , 299))
    x = image.img_to_array(img)
    x = x / 255 
    x = np.expand_dims(x , axis = 0)

    preds = model.predict(x)
    preds = np.argmax(preds , axis = 1)
    if preds == 5:
        preds = "Bengin"
    elif preds == 8:
        preds = "Normal"
    else:
        preds = "Malignant"
    return preds

@app.route('/predict' , methods=['GET', 'POST'])
def uploads():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath , 'uploads' , secure_filename(f.filename))
        f.save(file_path)
        preds = model_predict(file_path , model)
        result = preds
        return result
    return None


@app.route('/confusion')
def confusion():
    return render_template('confusion.html')

if(__name__ == '__main__'):
    app.secret_key = "ThisIsNotASecret:p"
    with app.app_context():
        db.create_all()
        app.run( port=8401, debug=True)
