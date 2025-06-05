from flask import Flask, render_template, url_for, send_from_directory
import os

app = Flask(__name__)

# Роуты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/style.css')
def style():
    return send_from_directory('static/css', 'style.css')

@app.route('/app.js')
def script():
    return send_from_directory('static', 'app.js')

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(debug=True)
