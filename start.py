import os
import sys
from flask import Flask

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:12345@127.0.0.1:3306/project"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["SECRET_KEY"] = "secretkey"

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


from routes import *
from extensions import *
from models import *
from admin import admin
from commands import *


with app.app_context():
    db.create_all()


if __name__=="__main__":
    if len(sys.argv) == 2 and sys.argv[1] in COMMANDS: #Superuser yarat: python start.py create_superuser
       COMMANDS[sys.argv[1]]()
    else:
        app.run(port=5000, debug=True)