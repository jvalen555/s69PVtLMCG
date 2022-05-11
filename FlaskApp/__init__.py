from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/")
def index():
    return ("Make a POST call to /audio_processor, form-data with file and word")


@app.route("/audio_processor", methods=['POST'])
def audio_processor():
    if request.headers['Authorization'] != 'Bearer 2A7FRC9AScGpt2a7BU8IOtKmuLzYFj0DtMRbS354P7V565hFJ7LmGq34nel2':
        return 'Unauthorized'

    if 'file' not in request.files:
        return 'file required'


    if not request.files['file'].filename.lower().endswith('.mp3'):
        return 'file not supported'

    if 'word' not in request.form:
        return 'word required'
        
    return f"hello Juan"


def process_audio_file():
    return 0

if __name__ == "__main__":
    app.run()
