from traceback import print_tb
from flask import Flask
from flask import request
from pydub import AudioSegment
import os
from werkzeug.utils import secure_filename
import wave
from vosk import Model, KaldiRecognizer, SetLogLevel
import time
import json 

app = Flask(__name__)

UPLOAD_FOLDER = 'tmp/'


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

    process_audio_file()

    return f"hello Juan"


def process_audio_file(word, file):
    #audio_file = request.files['file']
    #audio_file_path = save_audio_file(audio_file)
    #print('file saved {}'.format(audio_file_path))
    #wav_file_path = mp3_to_wav(audio_file_path)
    processed_audio = process_wav_file_2('tmp/1652278101.wav')
    return processed_audio


def save_audio_file(file):
    #filename = secure_filename(file.filename)
    filename = f'{str(int(time.time()))}.mp3'
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return os.path.join(UPLOAD_FOLDER, filename)


def mp3_to_wav(source, skip=0, excerpt=False):
    sound = AudioSegment.from_mp3(source)  # load source

    sound = sound.set_channels(1)  # mono
    sound = sound.set_frame_rate(16000)  # 16000Hz

    if excerpt:
        # 30 seconds - Does not work anymore when using skip
        excrept = sound[skip*1000:skip*1000+30000]
        output_path = os.path.splitext(source)[0]+"_excerpt.wav"
        excrept.export(output_path, format="wav")
    else:
        audio = sound[skip*1000:]
        output_path = os.path.splitext(source)[0]+".wav"
        audio.export(output_path, format="wav")

    return output_path


def process_wav_file(wav_file):
    # open audio file
    wf = wave.open(wav_file, "rb")

    # Initialize model
    model = Model(
        "models/vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, wf.getframerate())
    return rec


def process_wav_file_2(wav_file):
    wf = wave.open(wav_file, "rb")

    # Initialize model
    model = Model(
        "models/vosk-model-small-en-us-0.15")
    rec = KaldiRecognizer(model, wf.getframerate())

    # To store our results
    transcription = []
    result = []

    rec.SetWords(True)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            # Convert json output to dict
            result_dict = json.loads(rec.Result())
            result.append(result_dict['result'])
            # Extract text values and append them to transcription list
            transcription.append(result_dict.get("text", ""))

    # Get final bits of audio and flush the pipeline
    final_result = json.loads(rec.FinalResult())
    transcription.append(final_result.get("text", ""))

    # merge or join all list elements to one big string
    transcription_text = ' '.join(transcription)
    print(transcription_text)
    print(result)
    return {

    }

if __name__ == "__main__":
    app.run()
