from flask import Flask
from waitress import serve

app = Flask('connection-checker')


@app.route('/')
def check_root():
    return '', 200


def run(_host='0.0.0.0', _port=80):
    serve(app, host=_host, port=_port)
