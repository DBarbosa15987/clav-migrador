
import json
from path_utils import PROJECT_ROOT,FILES_DIR
import os
from .report import FixStatus, Report


def generate_error_table(globalErrors):
    """
    Função que gera a tabela HTML que faz o display dos
    erros ocorridos durante a migração.

    Os erros são agrupados por tipo.
    """

    with open(os.path.join(PROJECT_ROOT, "invariantes.json")) as f:
        x = json.load(f)

    invs = {}
    for r in x["invariantes"]:
        for i in r["inv"]:
            invs[f"{r["idRel"]}_{i["idInv"]}"] = {
                "desc": i["desc"],
                "clarificacao": i["clarificacao"]
            }

    html_content = "<div>"

    if globalErrors["grave"]["declsRepetidas"] or globalErrors["grave"]["relsInvalidas"] or globalErrors["grave"]["outro"]:
        html_content += f'<div class="error-section">🟥 Erros Graves (Estes erros têm de ser corrigidos para a ontologia ser gerada)</div>\n'

        # Decls Repetidas (Grave)
        if globalErrors["grave"]["declsRepetidas"]:
            html_content += f'<div class="error-section">Declarações Repetidas ({len(globalErrors["grave"]["declsRepetidas"])}): Códigos que foram declarados mais do que uma vez</div>\n'
            html_content += '<table class="error-table"><tr><th>Código Repetido</th><th>Folhas</th></tr>'
            for cod, files in globalErrors["grave"]["declsRepetidas"].items():
                html_content += f"<tr><td><span class='error-critical'>{cod}</span></td><td><b>{', '.join(files)}</b></td></tr>"
            html_content += '</table>'

        # Rels Invalidas (Grave)
        if globalErrors["grave"]["relsInvalidas"]:
            html_content += f'<div class="error-section">Relações Inválidas ({len(globalErrors["grave"]["relsInvalidas"])}): Declarações que referenciam um processo que não existe</div>\n'
            html_content += '<table class="error-table"><tr><th>Código Inválido</th><th>Relação Inválida</th></tr>'
            for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
                html_content += f"<tr><td><span class='error-critical'>{cod}</span></td><td><ul style='list-style-type: disc; padding-left: 1.25rem; margin: 0;'>"
                for rel in rels:
                    html_content += f"<li style='display: list-item;'><b>{rel[0]}</b> <b><i>{rel[1]}</b></i> <span class='error-critical'><b>{cod}</b></span></li>"
                html_content += "</ul></td></tr>"
            html_content += '</table>'

        # Outros (Grave)
        if globalErrors["grave"]["outro"]:
            html_content += '<div class="error-section">Outros Erros Graves</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for cod, msgs in globalErrors["grave"]["outro"].items():
                for msg in msgs:
                    html_content += f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

    # Normal
    if globalErrors["normal"]:
        html_content += f'<div class="error-section">🟨 Erros Genéricos</div>\n'
        html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
        for cod, msgs in globalErrors["normal"].items():
            for msg in msgs:
                html_content += f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
        html_content += '</table>'

    # Outros
    # TODO: TESTAR!!!!!
    if globalErrors["outro"]["leg"] or globalErrors["outro"]["tindice"] or globalErrors["outro"]["tipologia"] or globalErrors["outro"]["entidade"]:
        html_content += f'<div class="error-section">🟧 Outros Erros</div>\n'

        # Legislação (Outros)
        if globalErrors["outro"]["leg"]:
            html_content += f'<div class="error-section">Legislação ({len(globalErrors["outro"]["leg"])}): Erros na migração do catálogo das legislações</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["outro"]["leg"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Termos Índice (Outros)
        if globalErrors["outro"]["tindice"]:
            html_content += f'<div class="error-section">Termos Índice ({len(globalErrors["outro"]["tindice"])}): Erros na migração do catálogo dos termos índice</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["outro"]["tindice"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Tipologia (Outros)
        if globalErrors["outro"]["tipologia"]:
            html_content += f'<div class="error-section">Tipologia ({len(globalErrors["outro"]["tipologia"])}): Erros na migração do catálogo das tipologias</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["outro"]["tipologia"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Entidade (Outros)
        if globalErrors["outro"]["entidade"]:
            html_content += f'<div class="error-section">Entidade ({len(globalErrors["outro"]["entidade"])}): Erros na migração do catálogo das entidades</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["outro"]["entidade"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

    # Invariantes
    if globalErrors["erroInv"]:
        html_content += f'<div class="error-section">🟦 Erros de Invariantes</div>\n'
        for inv, erros in globalErrors["erroInv"].items():
            invariante = invs.get(inv, {"desc": "Sem descrição", "clarificacao": ""})
            errTitle = f"{inv} ({len(erros)}): {invariante['desc']}"
            if invariante["clarificacao"]:
                errTitle += f" ({invariante['clarificacao']})"
            html_content += f'<div class="error-section">{errTitle}</div>\n'
            html_content += """
            <table class="error-table">
                <tr><th>Código</th><th>Mensagem de Erro</th></tr>
            """
            for err in erros:
                msg = ""
                if err.fixStatus == FixStatus.FIXED:
                    msg = f"""
                    <details>
                        <summary class='error-fixed'>✅ {err.msg} <b>(corrigido automaticamente)</b></summary>
                        <div class='correction-details'>
                            {(err.fixMsg or "Correção efetuada com sucesso.")}
                        </div>
                    </details>
                    """
                elif err.fixStatus == FixStatus.FAILED:

                    msg = f"""
                    <details>
                        <summary class='error-failed'>❌ {err.msg} <b>(correção automática falhou)</b></summary>
                        <div class='correction-details'>
                            {(err.fixMsg or "A correção automática não foi possível.")}
                        </div>
                    </details>
                    """
                else:
                    msg = err.msg

                html_content += f"<tr><td>{err.cod}</td><td class='msg'>{msg}</td></tr>"
            html_content += "</table>\n"

    # Caso não hajam erros nenhuns, em qualquer classe
    if (not any([
        globalErrors["grave"]["declsRepetidas"],
        globalErrors["grave"]["relsInvalidas"],
        globalErrors["grave"]["outro"],
        globalErrors["normal"],
        globalErrors["outro"]["leg"],
        globalErrors["outro"]["tindice"],
        globalErrors["outro"]["tipologia"],
        globalErrors["outro"]["entidade"],
        globalErrors["erroInv"]
    ])):
            html_content += """
            <div class="no-errors">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path fill="green" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15.59-4.29-4.3
                    1.42-1.41L11 14.17l5.88-5.88 1.42 1.41Z" />
                </svg>
                <p>Nenhum erro encontrado 🎉</p>
            </div>
            """

    html_content += "</div>"
    return html_content


def generate_entity_table_dict(globalErrors,rep:Report):
    """
    Gera um dicionário indexado por entidade da AP
    em que o seu valor é a tabela HTML correspondente.
    """
    rep.errorsByEnt()
    with open(os.path.join(FILES_DIR, "classesN1.json")) as f:
        classesN1 = json.load(f)

    with open(os.path.join(PROJECT_ROOT, "invariantes.json")) as f:
        x = json.load(f)

    invs = {}
    for r in x["invariantes"]:
        for i in r["inv"]:
            invs[f"{r["idRel"]}_{i["idInv"]}"] = {
                "desc": i["desc"],
                "clarificacao": i["clarificacao"]
            }

    # Estas tabelas são incializadas para poder
    # mostrar as classes todas, mesmo quando não
    # são registados erros
    entityTables = {c:"" for c in classesN1}
    entityNumErrors = {c:0 for c in classesN1}

    grave_header = '<div class="error-section">🟥 Erros Graves (Estes erros têm de ser corrigidos para a ontologia ser gerada)</div>\n'
    grave_ents = set()

    def addRow(entity_dict, ent, content):
        # É sempre verificado se a entidade
        # existe para poder tolerar erros na
        # introdução do código
        if ent in entity_dict:
            entity_dict[ent] += content

    def ensureGraveHeader(ent):
        if ent not in grave_ents:
            addRow(entityTables, ent, grave_header)
            grave_ents.add(ent)

    def addError(ent):
        # É sempre verificado se a entidade
        # existe para poder tolerar erros na
        # introdução do código
        if ent in entityNumErrors:
            entityNumErrors[ent] += 1

    # Declarações Repetidas
    # TODO: Falta testar
    if globalErrors["grave"]["declsRepetidas"]:
        ents = set()
        for cod, sheet in globalErrors["grave"]["declsRepetidas"].items():
            ent = cod[:3]
            ensureGraveHeader(ent)
            # Header de cada tabela (uma por entidade)
            if ent not in ents:
                header = f'<div class="error-section">Declarações Repetidas: Códigos que foram declarados mais do que uma vez</div>\n'
                header += '<table class="error-table"><tr><th>Código Repetido</th><th>Folhas</th></tr>'
                addRow(entityTables, ent, header)
            ents.add(ent)

            # Linhas de cada tabela
            row = f"<tr><td><span class='error-critical'>{cod}</span></td><td><b>{', '.join(sheet)}</b></td></tr>"
            addError(ent)
            addRow(entityTables, ent, row)

        # Conclusão de cada tabela
        for cod in globalErrors["grave"]["declsRepetidas"]:
            ent = cod[:3]
            addRow(entityTables, ent, "</table>")

    # Relações Inválidas
    if globalErrors["grave"]["relsInvalidas"]:
        ents = set()
        # Criação dos headers das tabelas para as entidades
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = cod[:3]
                ensureGraveHeader(ent)
                if ent not in ents:
                    rels_header = f'<div class="error-section">Relações Inválidas: Declarações que referenciam um processo que não existe</div>\n'
                    rels_header += '<table class="error-table"><tr><th>Código Inválido</th><th>Relação Inválida</th></tr>'
                    addRow(entityTables, ent, rels_header)
                    ents.add(ent)

        # Linhas de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = cod[:3]
                rels_html = f"<tr><td><span class='error-critical'>{cod}</span></td>"
                rels_html += f"<td><b>{rel[0]}</b> <b><i>{rel[1]}</b></i> <span class='error-critical'><b>{cod}<b></span></td></tr>"
                addError(ent)
                addRow(entityTables, ent, rels_html)

        # Conclusão de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = cod[:3]
                addRow(entityTables, ent, "</table>")

    # Outros Erros Graves
    # TODO: Falta testar
    if globalErrors["grave"]["outro"]:
        ents = set()
        for cod, msgs in globalErrors["grave"]["outro"].items():
            ent = cod[:3]
            ensureGraveHeader(ent)
            # Header de cada tabela (uma por entidade)
            if ent not in ents:
                header = f'<div class="error-section">Outros Erros Graves</div>\n'
                header += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
                addRow(entityTables, ent, header)
            ents.add(ent)

            # Linhas de cada tabela
            for msg in msgs:
                row = f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
                addError(ent)
                addRow(entityTables, ent, row)

        # Conclusão de cada tabela
        for cod in globalErrors["grave"]["outro"]:
            ent = cod[:3]
            addRow(entityTables, ent, "</table>")

    # Erros Genéricos
    # TODO: Falta testar
    if globalErrors["normal"]:
        ents = set()
        for cod, msgs in globalErrors["normal"].items():
            ent = cod[:3]
            # Header de cada tabela (uma por entidade)
            if ent not in ents:
                header = f'<div class="error-section">🟨 Erros Genéricos</div>\n'
                header += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
                addRow(entityTables, ent, header)
            ents.add(ent)

            # Linhas de cada tabela
            for msg in msgs:
                row = f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
                addError(ent)
                addRow(entityTables, ent, row)

        # Conclusão de cada tabela
        for cod in globalErrors["normal"]:
            ent = cod[:3]
            addRow(entityTables, ent, "</table>")

    # Erros de Invariantes por entidade
    if globalErrors["erroInvByEnt"]:

        for ent, invs_dict in globalErrors["erroInvByEnt"].items():
            addRow(entityTables, ent, '<div class="error-section">🟦 Erros de Invariantes</div>\n')

            for inv, erros in invs_dict.items():
                invariante = invs.get(inv, {"desc": "Sem descrição", "clarificacao": ""})
                errTitle = f"{inv} ({len(erros)}): {invariante['desc']}"
                if invariante["clarificacao"]:
                    errTitle += f" ({invariante['clarificacao']})"

                html_part = f'<div class="error-section">{errTitle}</div>\n'
                html_part += '<table class="error-table"><tr><th>Código</th><th>Mensagem de Erro</th></tr>'
                for err in erros:
                    msg = ""
                    if err.fixStatus == FixStatus.FIXED:
                        msg = f"""
                        <details>
                            <summary class='error-fixed'>✅ {err.msg} <b>(corrigido automaticamente)</b></summary>
                            <div class='correction-details'>
                                {(err.fixMsg or "Correção efetuada com sucesso.")}
                            </div>
                        </details>
                        """
                    elif err.fixStatus == FixStatus.FAILED:
                        msg = f"""
                        <details>
                            <summary class='error-failed'>❌ {err.msg} <b>(correção automática falhou)</b></summary>
                            <div class='correction-details'>
                                {(err.fixMsg or "A correção automática não foi possível.")}
                            </div>
                        </details>
                        """
                    else:
                        msg = err.msg

                    addError(ent)
                    html_part += f"<tr><td>{err.cod}</td><td class='msg'>{msg}</td></tr>"
                html_part += "</table>\n"

                addRow(entityTables, ent, html_part)

    # Criar o header para todas as entidades existentes
    for entCod,ent in classesN1.items():
        if entityNumErrors[entCod] > 0:
            entTitle = f'<div class="error-section">{entCod} ({entityNumErrors[entCod]}): {ent['titulo']}</div>\n'
            entityTables[entCod] = entTitle + entityTables[entCod]
        else:
            entTitle = f'<div class="error-section">{entCod}: {ent['titulo']}</div>\n'
            content = """
            <div class="no-errors">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path fill="green" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15.59-4.29-4.3
                    1.42-1.41L11 14.17l5.88-5.88 1.42 1.41Z" />
                </svg>
                <p>Nenhum erro encontrado 🎉</p>
            </div>"""
            entityTables[entCod] = entTitle + content

    return entityTables


def generate_warnings_table(warnings):

    html_content = ""

    # Warnings
    if warnings:
        html_content += f'<div class="error-section">⚠️ Warnings</div>\n'

        # Inferências
        if warnings["inferencias"]:
            html_content += f'<div class="error-section">Inferências ({len(warnings["inferencias"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["inferencias"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Harmonização
        if warnings["harmonizacao"]:
            html_content += f'<div class="error-section">Harmonização ({len(warnings["harmonizacao"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["harmonizacao"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Relações de Harmonização
        if warnings["relHarmonizacao"]:
            html_content += f'<div class="error-section">Relações de Harmonização ({len(warnings["relHarmonizacao"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["relHarmonizacao"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Normal
        if warnings["normal"]:
            html_content += f'<div class="error-section">Warnings Genéricos ({len(warnings["normal"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["normal"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'
    else:
        # Tabela vazia: Não foram registados warnings
        html_content += """<div class="no-errors">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path fill="green" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15.59-4.29-4.3
                1.42-1.41L11 14.17l5.88-5.88 1.42 1.41Z" />
            </svg>
            <p>Não foram registados warnings</p>
        </div>"""

    return html_content
