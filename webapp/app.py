from flask import Flask, render_template, request, jsonify
import magic

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

    file_content = file.read()

    return jsonify({'html': "<h1>Hey there</h1>"})

if __name__ == '__main__':
    app.run(debug=True,port=5001)
