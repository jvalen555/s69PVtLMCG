from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/")
def index():
    return (
        "Try /hello/Chris for parameterized Flask route.\n"
    )


@app.route("/hello/<name>", methods=['GET'])
def hello(name: str):
    return f"hello {name}"


@app.route("/audio_processor", methods=['POST'])
def audio_processor():

    if 'file' in request.files:
        print('files')
        print(request.files)
    else:
        return 'file required'

    if 'word' in request.form:
        print('form')
        print(request.form)
    else:
        return 'word required'

    return f"hello Juan"

if __name__ == "__main__":
    app.run()
