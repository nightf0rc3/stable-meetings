from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/demo')
def greet():
    return send_from_directory('./dist', 'indexDemo.html')