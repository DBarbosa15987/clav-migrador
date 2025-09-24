
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
            html_content += f"<tr><td><span class='error-critical'>{cod}</span></td><td>{', '.join(files)}</td></tr>"
        html_content += '</table>'

    # Rels Invalidas (Grave)
    if globalErrors["grave"]["relsInvalidas"]:
        html_content += f'<div class="error-section">Relações Inválidas ({len(globalErrors["grave"]["relsInvalidas"])}): Declarações que referenciam um processo que não existe</div>\n'
        html_content += '<table class="error-table"><tr><th>Código Inválido</th><th>Relação Inválida</th></tr>'
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            html_content += f"<tr><td><span class='error-critical'>{cod}</span></td><td><ul style='list-style-type: disc; padding-left: 1.25rem; margin: 0;'>"
            for rel in rels:
                html_content += f"<li style='display: list-item;'>{rel[0]} {rel[1]} <span class='error-critical'>{cod}</span></li>"
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
                cod = err.cod
                msg = err.msg
                if err.fixStatus == FixStatus.FIXED:
                    msg = f"<span class='error-fixed'>✅ {msg} <b>(corrigido automaticamente)</b></span>"
                html_content += f"<tr><td>{cod}</td><td class='msg'>{msg}</td></tr>"
            html_content += "</table>\n"


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

    entityTables = {}
    entityNumErrors = {}
    grave_header = '<div class="error-section">🟥 Erros Graves (Estes erros têm de ser corrigidos para a ontologia ser gerada)</div>\n'
    grave_ents = set()

    def addRow(entity_dict, ent, content):
        if ent not in entity_dict:
            entity_dict[ent] = ''
        entity_dict[ent] += content

    def ensureGraveHeader(ent):
        if ent not in grave_ents:
            addRow(entityTables, ent, grave_header)
            grave_ents.add(ent)

    def getEnt(cod):
        ent = cod
        try:
            ent = cod[:3]
        except Exception:
            pass
        return ent

    def addError(ent):
        if ent in entityNumErrors:
            entityNumErrors[ent]+=1
        else:
            entityNumErrors[ent]=1

    # Declarações Repetidas
    # TODO: Falta testar
    if globalErrors["grave"]["declsRepetidas"]:
        ents = set()
        for cod, sheet in globalErrors["grave"]["declsRepetidas"].items():
            ent = getEnt(cod)
            ensureGraveHeader(ent)
            # Header de cada tabela (uma por entidade)
            if ent not in ents:
                header = f'<div class="error-section">Declarações Repetidas: Códigos que foram declarados mais do que uma vez</div>\n'
                header += '<table class="error-table"><tr><th>Código Repetido</th><th>Folhas</th></tr>'
                addRow(entityTables, ent, header)
            ents.add(ent)

            # Linhas de cada tabela
            row = f"<tr><td><span class='error-critical'>{cod}</span></td><td>{', '.join(sheet)}</td></tr>"
            addError(ent)
            addRow(entityTables, ent, row)

        # Conclusão de cada tabela
        for cod in globalErrors["grave"]["declsRepetidas"]:
            ent = getEnt(cod)
            addRow(entityTables, ent, "</table>")

    # Relações Inválidas
    if globalErrors["grave"]["relsInvalidas"]:
        ents = set()
        # Criação dos headers das tabelas para as entidades
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = getEnt(rel[0])
                ensureGraveHeader(ent)
                if ent not in ents:
                    rels_header = f'<div class="error-section">Relações Inválidas: Declarações que referenciam um processo que não existe</div>\n'
                    rels_header += '<table class="error-table"><tr><th>Código Inválido</th><th>Relação Inválida</th></tr>'
                    addRow(entityTables, ent, rels_header)
                    ents.add(ent)

        # Linhas de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = getEnt(rel[0])
                rels_html = f"<tr><td><span class='error-critical'>{cod}</span></td>"
                rels_html += f"<td>{rel[0]} {rel[1]} <span class='error-critical'>{cod}</span></td></tr>"
                addError(ent)
                addRow(entityTables, ent, rels_html)

        # Conclusão de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                ent = getEnt(rel[0])
                addRow(entityTables, ent, "</table>")

    # Outros Erros Graves
    # TODO: Falta testar
    if globalErrors["grave"]["outro"]:
        ents = set()
        for cod, msgs in globalErrors["grave"]["outro"].items():
            ent = getEnt(cod)
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
            ent = getEnt(cod)
            addRow(entityTables, ent, "</table>")

    # Erros Genéricos
    # TODO: Falta testar
    if globalErrors["normal"]:
        ents = set()
        for cod, msgs in globalErrors["normal"].items():
            ent = getEnt(cod)
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
            ent = getEnt(cod)
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
                    msg = err.msg
                    if err.fixStatus == FixStatus.FIXED:
                        msg = f"<span class='error-fixed'>✅ {msg} <b>(corrigido automaticamente)</b></span>"

                    addError(ent)
                    html_part += f"<tr><td>{err.cod}</td><td class='msg'>{msg}</td></tr>"
                html_part += "</table>\n"

                addRow(entityTables, ent, html_part)

    # Criar o header para todas as entidades referidas
    for entCod in entityTables:
        ent = classesN1.get(entCod, {"titulo": "Sem descrição", "clarificacao": ""})
        entTitle = f'<div class="error-section">{entCod} ({entityNumErrors[entCod]}): {ent['titulo']}</div>\n'
        entityTables[entCod] = entTitle + entityTables[entCod]

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
        pass

    return html_content
