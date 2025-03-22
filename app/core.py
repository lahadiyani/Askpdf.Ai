from flask import Flask
from app.constants.paths import PATH_PROGRAM

app = Flask(__name__, template_folder=f"{PATH_PROGRAM}/template", static_folder=f"{PATH_PROGRAM}/static")