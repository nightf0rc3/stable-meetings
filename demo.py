from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route('/demo')
def greet():
    return send_from_directory('./dist', 'indexDemo.html')


@app.route('/test', methods=['GET'])
def test():
    return "Test successful"

if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')
