import os
import wave
import time
import json
import azure.functions as func

from flask import Flask, request
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from vosk import Model, KaldiRecognizer, SetLogLevel

app = Flask(__name__)
SetLogLevel(-1)
UPLOAD_FOLDER = 'tmp/'


@app.route("/")
def index():
    return ("Make a POST call to /audio_processor, form-data with file and word")


@app.route("/audio_processor", methods=['POST'])
def audio_processor():
    try:
        if request.headers['Authorization'] != 'Bearer 2A7FRC9AScGpt2a7BU8IOtKmuLzYFj0DtMRbS354P7V565hFJ7LmGq34nel2':
            return func.HttpResponse(body='Unauthorized', status_code=401)

        if 'file' not in request.files:
            return 'File required', 400

        if not request.files['file'].filename.lower().endswith('.mp3'):
            return 'File not supported', 400

        if 'word' not in request.form:
            return 'Word required', 400

        return process_audio_file(request.form['word'], request.files['file'])
    except:
        return 'an error ocurred', 400


def process_audio_file(word: str, file):
    audio_file = save_audio_file(file)
    wav_file = mp3_to_wav(audio_file)
    processed_audio = process_wav_file(wav_file)
    processed_audio['words'] = filter_words(word, processed_audio['words'])
    delete_file(audio_file)
    delete_file(wav_file)
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
    model = Model("models/vosk-model-small-en-us-0.15") # Initialize model
    rec = KaldiRecognizer(model, wf.getframerate())
    
    transcription = [] # To store results
    result = []

    rec.SetWords(True)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):            
            result_dict = json.loads(rec.Result()) # Convert json output to dict
            if 'result' in result_dict:
                result = result + result_dict['result']            
            transcription.append(result_dict.get("text", "")) # Extract text values and append them to transcription list
    
    final_result = json.loads(rec.FinalResult()) # Get final bits of audio and flush the pipeline
    if 'result' in final_result:
        result = result + final_result['result']
    transcription.append(final_result.get("text", ""))
    
    transcription_text = ' '.join(transcription) # merge or join all list elements to one big string

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
