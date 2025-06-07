from datetime import datetime
import glob
from flask import Flask, render_template, request, jsonify, send_file, session
from migrador.migrador import migra
from migrador.genTTL import genFinalOntology
from path_utils import UPLOAD_DIR, OUTPUT_DIR
import os
import uuid


app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

@app.route('/')
def index():
    session.clear()
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
    allowedMimetypes = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-excel"]
    if mimetype not in allowedMimetypes:
        return jsonify({'error': 'Ficheiro não suportado'})

    try:
        filePath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filePath,"wb") as f:
            f.write(fileContent)

        rep,ok = migra(filePath)
        session['migration_ok'] = ok

        # A ontologia final só é gerada se não forem encontrados erros "graves"
        if ok:
            genFinalOntology()

    except Exception as e:
        return jsonify({'error': f"Erro na migração: {e}"})

    return jsonify({
        "ok": ok,
        "table_by_entity": rep.generate_entity_table_dict(),
        "table_by_invariant": rep.generate_error_table()
    })


@app.route('/download')
def download_output():

    if not session.get('migration_ok'):
        return "Não é permitido fazer download. A migração não foi bem-sucedida.", 403

    pattern = os.path.join(OUTPUT_DIR, "CLAV_*.ttl")
    files = glob.glob(pattern)

    if not files:
        print("No files found.")
    else:
        try:
            mostRecentFile = max(files, key=extract_timestamp)
        except Exception:
            return "Erro ao encontrar o ficheiro final", 500
        print("Getting file:", mostRecentFile)

    clav = os.path.join(OUTPUT_DIR, mostRecentFile)
    if not os.path.exists(clav):
        return "Erro ao encontrar o ficheiro final", 500

    return send_file(clav, as_attachment=True, download_name=mostRecentFile)


def extract_timestamp(filepath):
    filename = os.path.basename(filepath)
    timestamp_str = filename.replace("CLAV_", "").replace(".ttl", "")
    return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")


if __name__ == '__main__':
    app.run(debug=True,port=5001)
