import os
import wave
import time
import json
import azure.functions as func
import pymongo

from flask import Flask, request
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from vosk import Model, KaldiRecognizer, SetLogLevel
from pymongo.server_api import ServerApi
from datetime import datetime

now = datetime.now()
current_time = now.strftime("%H:%M:%S")

app = Flask(__name__)
SetLogLevel(-1)
UPLOAD_FOLDER = 'tmp/'

client = pymongo.MongoClient(
    "mongodb+srv://s69PVtLMCG:7xkbQYDhfPIWPLsc@cluster0.vdjgf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", server_api=ServerApi('1'))
mydb = client["s69PVtLMCG"]
mycol = mydb["Logs"]


@app.route("/")
def index():
    return ("Make a POST call to /audio_processor, form-data with file and word")


@app.route("/logs", methods=['POST'])
def check_logs():
    try:
        if request.headers['Authorization'] != 'Bearer 2A7FRC9AScGpt2a7BU8IOtKmuLzYFj0DtMRbS354P7V565hFJ7LmGq34nel2':
            return 'Unauthorized', 401

        if request.is_json and 'filter' in request.json:
            return {'logs': get_logs(request.json['filter'])}, 200
        elif not request.is_json:
            return {'logs': get_logs()}, 200
        else:
            raise 'invalid filter'
    except:
        return 'an error ocurred', 400


@ app.route("/audio_processor", methods=['POST'])
def audio_processor():
    try:
        if request.headers['Authorization'] != 'Bearer 2A7FRC9AScGpt2a7BU8IOtKmuLzYFj0DtMRbS354P7V565hFJ7LmGq34nel2':
            insert_log({
                'time': current_time,
                'action': '/audio_processor',
                'response_code': 401,
                'output': 'Unauthorized'
            })
            return 'Unauthorized', 401

        if 'file' not in request.files:
            insert_log({
                'time': current_time,
                'action': '/audio_processor',
                'response_code': 400,
                'output': 'File required'
            })
            return 'File required', 400

        if not request.files['file'].filename.lower().endswith('.mp3'):
            insert_log({
                'time': current_time,
                'action': '/audio_processor',
                'response_code': 400,
                'output': 'File not supported'
            })
            return 'File not supported', 400

        if 'word' not in request.form:
            insert_log({
                'time': current_time,
                'action': '/audio_processor',
                'response_code': 400,
                'output': 'Word required'
            })
            return 'Word required', 400

        return process_audio_file(request.form['word'], request.files['file'])
    except:
        return 'an error ocurred', 400


def insert_log(log):
    x = mycol.insert_one(log)
    return x.inserted_id


def query_log(query):
    myquery = {"address": "Park Lane 38"}
    mydoc = mycol.find(query)
    return mydoc


def get_logs(filter = {}):
    print(filter)
    print(type(filter))
    logs = []
    if isinstance(filter, dict) or filter == {}:
        for x in mycol.find(filter, {"_id": 0}):
            logs.append(x)
    else:
        raise 'Invalid filter'
    return logs


def process_audio_file(word: str, file):
    audio_file = save_audio_file(file)
    wav_file = mp3_to_wav(audio_file)
    processed_audio = process_wav_file(wav_file)
    processed_audio['words'] = filter_words(word, processed_audio['words'])
    delete_file(audio_file)
    delete_file(wav_file)
    insert_log({
        'time': current_time,
        'action': '/audio_processor',
        'response_code': 200,
        'word': word,
        'audio_file_name': file.filename,
        'output': processed_audio
    })
    return processed_audio, 200


def save_audio_file(file):
    filename = f'{secure_filename(file.filename)}_{str(int(time.time()))}.mp3'
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return os.path.join(UPLOAD_FOLDER, filename)


def mp3_to_wav(source, skip=0):
    sound = AudioSegment.from_mp3(source)  # load source
    sound = sound.set_channels(1)  # mono
    sound = sound.set_frame_rate(16000)  # 16000Hz

    audio = sound[skip*1000:]
    output_path = os.path.splitext(source)[0]+".wav"
    audio.export(output_path, format="wav")

    return output_path


def process_wav_file(wav_file):
    wf = wave.open(wav_file, "rb")
    model = Model("models/vosk-model-small-en-us-0.15")  # Initialize model
    rec = KaldiRecognizer(model, wf.getframerate())

    transcription = []  # To store results
    result = []

    rec.SetWords(True)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            # Convert json output to dict
            result_dict = json.loads(rec.Result())
            if 'result' in result_dict:
                result = result + result_dict['result']
            # Extract text values and append them to transcription list
            transcription.append(result_dict.get("text", ""))

    # Get final bits of audio and flush the pipeline
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        result = result + final_result['result']
    transcription.append(final_result.get("text", ""))

    # merge or join all list elements to one big string
    transcription_text = ' '.join(transcription)

    frames = wf.getnframes()
    rate = wf.getframerate()
    duration = frames / float(rate)

    return {
        'number_of_words': len(result),
        'duration': duration,
        'avg_conf': sum(d['conf'] for d in result) / len(result),
        'transcription_text': transcription_text,
        'words': result
    }


def filter_words(word: str, result):
    return [w for w in result if w['word'] == word.lower()]


def delete_file(file):
    os.remove(file)


if __name__ == "__main__":
    app.run()
