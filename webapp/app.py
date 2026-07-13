from flask import Flask, render_template, request, jsonify, send_file, session, make_response
from migrador.migrador import migra
from migrador.genTTL import genFinalOntology
from utils.path_utils import UPLOAD_DIR, OUTPUT_DIR, WEBAPP, DUMP_DIR
from io import BytesIO
import zipfile
import os
import json
import uuid
from utils.log_utils import WEB
import logging
from migrador.genHTML import generate_classe_table_dict, generate_error_table, generate_warnings_table
import threading


lock = threading.Lock()
logger = logging.getLogger(WEB)
app = Flask(__name__)
app.secret_key = str(uuid.uuid4())


@app.route('/')
def index():
    session.clear()
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_file():

    session.clear()
    if not lock.acquire(blocking=False):
        logger.error(f"Endpoint /process não pode ser utilizado até que o processamento dos dados acabe")
        return jsonify({
            "error": "Processo já está em execução no segundo plano."
        }), 429

    try:
        if 'file' not in request.files:
            logger.error("'file' não encontrado no request")
            return jsonify({'error': '\'file\' não encontrado no request'}), 400

        file = request.files['file']

        if file.filename == '':
            logger.error("Ficheiro não selecionado")
            return jsonify({'error': 'Ficheiro não selecionado'}), 400

        logger.info(f"Ficheiro recebido: {file.filename}")

        fileContent = file.read()
        mimetype = file.mimetype
        allowedMimetypes = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel"
        ]
        if mimetype not in allowedMimetypes:
            return jsonify({'error': 'Ficheiro não suportado'}), 415

        filePath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filePath, "wb") as f:
            f.write(fileContent)

        rep, ok, invs = migra(filePath)
        session['migration_ok'] = ok

        if ok:
            zipedOutputFile = genFinalOntology()
            session['zipedOutputFile'] = zipedOutputFile

        table_by_classe = generate_classe_table_dict(
            rep.globalErrors, rep.classesN1, rep.inativos, rep.declaracoes, invs
        )
        table_all_errors = generate_error_table(rep.globalErrors, rep.inativos, invs)
        warnings = generate_warnings_table(rep.warnings)

        report = {
            "table_by_classe": table_by_classe,
            "table_all_errors": table_all_errors,
            "warnings": warnings
        }

        # Dump do das tabelas html do relatório de erros para
        # serem usadas no /download-report
        report_file = os.path.join(DUMP_DIR, "report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f)

        session["report_file"] = report_file

        return jsonify({
            "ok": ok,
            "table_by_classe": table_by_classe,
            "table_all_errors": table_all_errors,
            "warnings": warnings
        })
    except Exception as e:
        logger.exception(f"Exceção levantada na migração dos dados")
        return jsonify({'error': 'Erro na migração dos dados'}), 500
    finally:
        lock.release()


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


@app.route("/download-report")
def download_report():

    try:
        with open(session["report_file"], encoding="utf-8") as f:
            report = json.load(f)
        with open(os.path.join(WEBAPP, "static/css/index.css"), encoding="utf-8") as f:
            css = f.read()
        with open(os.path.join(WEBAPP, "static/js/report.js"), encoding="utf-8") as f:
            js = f.read()
    except Exception as e:
        logger.exception(f"Erro de leitura de ficheiros:{e}")
        return jsonify({'error': 'Erro no download do Relatório de Erros'}), 500

    html = render_template(
        "report.html",
        table_all_errors=report["table_all_errors"],
        table_by_classe=report["table_by_classe"],
        warnings=report["warnings"],
        embedded_css=css,
        embedded_js=js,
    )

    try:
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("report.html", html)

        zip_buffer.seek(0)
    except Exception as e:
        logger.exception(f"Erro ao zipar o ficheiro:{e}")
        return jsonify({'error': 'Erro no download do Relatório de Erros'}), 500

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="report.zip",
    )
