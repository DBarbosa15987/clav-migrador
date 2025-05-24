from flask import Flask, render_template, request, jsonify, send_file
from migrador.migrador import migra, zip_output_files
from path_utils import UPLOAD_FOLDER, FILES_DIR, OUTPUT_FOLDER, ONTOLOGY_DIR
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
    # allowedMimetypes = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-excel"]
    # print(mimetype)
    if mimetype != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return jsonify({'error': 'Ficheiro não suportado'})
    # TODO: mudar o filename para um "timestamp"?
    try:
        filePath = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(filePath,"wb") as f:
            f.write(fileContent)
        rep = migra(filePath)
        zip_output_files(ONTOLOGY_DIR,os.path.join(OUTPUT_FOLDER,"output.zip"))
    except Exception as e:
        return jsonify({'error': f"Erro na migração: {e}"})

    return jsonify({
        "table_by_entity": rep.generate_entity_table_dict(),
        "table_by_invariant": rep.generate_error_table()
    })


@app.route('/download')
def download_output():
    zip_path = os.path.join(OUTPUT_FOLDER, 'output.zip')  # or wherever you saved it
    if not os.path.exists(zip_path):
        return "Arquivo zip não encontrado", 404
    return send_file(zip_path, as_attachment=True, download_name='output.zip')


if __name__ == '__main__':
    app.run(debug=True,port=5001)
