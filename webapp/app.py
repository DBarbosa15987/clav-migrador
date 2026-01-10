from flask import Flask, render_template, request, jsonify, send_file, session
from migrador.migrador import migra
from migrador.genTTL import genFinalOntology
from utils.path_utils import UPLOAD_DIR, OUTPUT_DIR
import os
import uuid
from utils.log_utils import WEB
import logging
from migrador.genHTML import generate_classe_table_dict, generate_error_table, generate_warnings_table


logger = logging.getLogger(WEB)
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_file():

    if 'file' not in request.files:
        logger.error("'file' não encontrado no request")
        return jsonify({'error': '\'file\' não encontrado no request'}), 400

    file = request.files['file']

    if file.filename == '':
        logger.error("Ficheiro não selecionado")
        return jsonify({'error': 'Ficheiro não selecionado'}), 400

    logger.info(f"Ficheiro recebido: {file.filename}")

    logger.info("Verificação do ficheiro recebido")
    fileContent = file.read()
    mimetype = file.mimetype
    allowedMimetypes = ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-excel"]
    if mimetype not in allowedMimetypes:
        logger.error("Ficheiro não suportado")
        return jsonify({'error': 'Ficheiro não suportado'}), 415

    try:
        filePath = os.path.join(UPLOAD_DIR, file.filename)
        logger.info(f"Criação de uma cópia do ficheiro recebido em {filePath}")
        with open(filePath,"wb") as f:
            f.write(fileContent)
    except Exception as e:
        logger.error(f"Erro ao guardar uma cópia do ficheiro recebido em {filePath}")
        logger.exception(f"[{e.__class__.__name__}]: {e}")
        return jsonify({'error': f"Erro ao guardar uma cópia do ficheiro recebido em {filePath}"}), 500

    try:
        rep,ok,invs = migra(filePath)
        session['migration_ok'] = ok
        # A ontologia final só é gerada se não forem encontrados erros "graves"
        if ok:
            logger.info("Geração da ontologia final")
            zipedOutputFile = genFinalOntology()
            session['zipedOutputFile'] = zipedOutputFile
        else:
            logger.warning("A ontologia final não foi gerada")

    except Exception as e:
        logger.error("Erro na migração")
        logger.exception(f"[{e.__class__.__name__}]: {e}")
        return jsonify({'error': f"Erro na migração, para mais informação verifique os logs"}), 500

    logger.info("Geração das tabelas a partir do relatório de erros")
    return jsonify({
        "ok": ok,
        "table_by_classe": generate_classe_table_dict(rep.globalErrors,rep.classesN1,rep.inativos,rep.declaracoes,invs),
        "table_by_invariant": generate_error_table(rep.globalErrors,rep.inativos,invs),
        "warnings": generate_warnings_table(rep.warnings)
    })

@app.route('/download')
def download_output():

    if not session.get('migration_ok'):
        logger.error("Tentativa de download da ontologia falhou. A migração não foi bem-sucedida")
        return jsonify({"error": "Não é permitido fazer download. A migração não foi bem-sucedida."}), 422

    zipedOutputFile = session['zipedOutputFile']
    clav = os.path.join(OUTPUT_DIR, zipedOutputFile)
    if os.path.exists(clav):
        logger.info(f"Ficheiro selecionado: {clav}")
    else:
        logger.error(f"Erro ao encontrar o ficheiro final::{clav}")
        return jsonify({"error": "Erro ao encontrar o ficheiro final"}), 404

    logger.info(f"Download da ontologia::{zipedOutputFile}")
    return send_file(clav, as_attachment=True, download_name=zipedOutputFile, mimetype="application/zip")
