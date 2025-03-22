from flask import Flask
from app.constants.paths import PATH_PROGRAM

app = Flask(__name__, template_folder="../template/", static_folder="../static/")