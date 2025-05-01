from flask import Flask, render_template, request, jsonify
from migrador.migrador import migra
from path_utils import UPLOAD_FOLDER
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    fileContent = file.read()
    mimetype = file.mimetype
    print(mimetype)
    # TODO: mudar o filename para um "timestamp"?
    filePath = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filePath,"wb") as f:
        f.write(fileContent)

    rep = migra(filePath)

    return jsonify({'html': "<h1>Hey there</h1>"})

if __name__ == '__main__':
    app.run(debug=True,port=5001)
