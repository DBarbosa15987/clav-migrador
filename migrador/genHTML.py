from .report import FixStatus


def getCod(cod,inativos):
    c = cod
    if cod in inativos:
        c += " <b>(inativo)</b>"
    return c


def generate_error_table(globalErrors,inativos,invs):
    """
    Função que gera a tabela HTML que faz o display dos
    erros ocorridos durante a migração.

    Os erros são agrupados por tipo.
    """

    html_content = "<div>"

    if globalErrors["grave"]["declsRepetidas"] or globalErrors["grave"]["relsInvalidas"] or globalErrors["grave"]["outro"]:
        html_content += f'<div class="error-section">🟥 Erros Graves (Estes erros têm de ser corrigidos para a ontologia ser gerada)</div>\n'

        # Decls Repetidas (Grave)
        if globalErrors["grave"]["declsRepetidas"]:
            html_content += f'<div class="error-section">Declarações Repetidas ({len(globalErrors["grave"]["declsRepetidas"])}): Códigos que foram declarados mais do que uma vez</div>\n'
            html_content += '<table class="error-table"><tr><th>Código Repetido</th><th>Folhas</th></tr>'
            for cod, files in globalErrors["grave"]["declsRepetidas"].items():
                html_content += f"<tr><td><span class='error-critical'>{getCod(cod,inativos)}</span></td><td><b>{', '.join(files)}</b></td></tr>"
            html_content += '</table>'

        # Rels Invalidas (Grave)
        if globalErrors["grave"]["relsInvalidas"]:
            num_err = sum([len(x) for x in globalErrors["grave"]["relsInvalidas"].values()])
            html_content += f'<div class="error-section">Relações Inválidas ({num_err}): Declarações que referenciam um processo que não existe</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Código Inválido</th><th>Relação Inválida</th></tr>'
            for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
                for rel in rels:
                    html_content += f"<tr><td>{getCod(rel[0],inativos)}</td><td><span class='error-critical'>{getCod(cod,inativos)}</span></td><td>"
                    if rel[2]:
                        html_content += f"O processo <span class='error-critical'><b>{cod}</b></span> é inválido e é referenciado na justificação do {rel[2].upper()} do processo <b>{rel[0]}</b>."
                    else:
                        html_content += f"A relação <b>{rel[0]}</b> <b><i>{rel[1]}</b></i> <span class='error-critical'><b>{cod}</b></span>, declarada na zona de contexto do processo <b>{rel[0]}</b>, é inválida."

                html_content += "</td></tr>"
            html_content += '</table>'

        # Outros (Grave)
        if globalErrors["grave"]["outro"]:
            num_err = sum([len(x) for x in globalErrors["grave"]["outro"].values()])
            html_content += f'<div class="error-section">Outros Erros Graves ({num_err})</div>\n'
            html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
            for cod, msgs in globalErrors["grave"]["outro"].items():
                for msg in msgs:
                    html_content += f"<tr><td>{getCod(cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

    # Normal
    if globalErrors["normal"]:
        html_content += f'<div class="error-section">🟨 Erros Genéricos</div>\n'
        html_content += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
        for cod, msgs in globalErrors["normal"].items():
            for msg in msgs:
                html_content += f"<tr><td>{getCod(cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
        html_content += '</table>'

    # Catálogos
    if globalErrors["catalogo"]["leg"] or globalErrors["catalogo"]["tindice"] or globalErrors["catalogo"]["tipologia"] or globalErrors["catalogo"]["entidade"]:
        html_content += f'<div class="error-section">🟧 Erros de Catálogo</div>\n'

        # Legislação
        if globalErrors["catalogo"]["leg"]:
            html_content += f'<div class="error-section">Legislação ({len(globalErrors["catalogo"]["leg"])}): Erros na migração do catálogo das legislações</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["catalogo"]["leg"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Termos Índice
        if globalErrors["catalogo"]["tindice"]:
            html_content += f'<div class="error-section">Termos Índice ({len(globalErrors["catalogo"]["tindice"])}): Erros na migração do catálogo dos termos índice</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["catalogo"]["tindice"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Tipologia
        if globalErrors["catalogo"]["tipologia"]:
            html_content += f'<div class="error-section">Tipologia ({len(globalErrors["catalogo"]["tipologia"])}): Erros na migração do catálogo das tipologias</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["catalogo"]["tipologia"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Entidade
        if globalErrors["catalogo"]["entidade"]:
            html_content += f'<div class="error-section">Entidade ({len(globalErrors["catalogo"]["entidade"])}): Erros na migração do catálogo das entidades</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in globalErrors["catalogo"]["entidade"]:
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

                html_content += f"<tr><td>{getCod(err.cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
            html_content += "</table>\n"

    # Caso não hajam erros nenhuns, em qualquer classe
    if (not any([
        globalErrors["grave"]["declsRepetidas"],
        globalErrors["grave"]["relsInvalidas"],
        globalErrors["grave"]["outro"],
        globalErrors["normal"],
        globalErrors["catalogo"]["leg"],
        globalErrors["catalogo"]["tindice"],
        globalErrors["catalogo"]["tipologia"],
        globalErrors["catalogo"]["entidade"],
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


def generate_classe_table_dict(globalErrors,classesN1,inativos,decls,invs):
    """
    Gera um dicionário indexado por classe de nível 1
    em que o seu valor é a tabela HTML correspondente.
    """

    # Estas tabelas são inicializadas para poder
    # mostrar as classes todas, mesmo quando não
    # são registados erros
    classTables = {c:"" for c in classesN1}
    classNumErrors = {c:0 for c in classesN1}

    grave_header = '<div class="error-section">🟥 Erros Graves (Estes erros têm de ser corrigidos para a ontologia ser gerada)</div>\n'
    grave_classes = set()

    def addRow(classe_dict, cl, content):
        # É sempre verificado se a classe
        # existe para poder tolerar erros na
        # introdução do código
        if cl in classe_dict:
            classe_dict[cl] += content

    def ensureGraveHeader(cl):
        if cl not in grave_classes:
            addRow(classTables, cl, grave_header)
            grave_classes.add(cl)

    def addError(cl):
        # É sempre verificado se a classe
        # existe para poder tolerar erros na
        # introdução do código
        if cl in classNumErrors:
            classNumErrors[cl] += 1

    def getClasse(cod,decls):
        # Obter a página onde a classe foi declarada.
        # Assim sabe-se sempre em que folha foi declarado
        # o processo, mesmo que tenha um formato inválido.
        if sheets := decls.get(cod):
            cl = sheets[0].replace("_csv","")
        else:
            cl = cod[:3]
        return cl

    # Declarações Repetidas
    if globalErrors["grave"]["declsRepetidas"]:
        # Contagem dos erros de cada classe
        num_err = {c:0 for c in classesN1}
        for c in globalErrors["grave"]["declsRepetidas"].keys():
            cl = getClasse(c,decls)
            if cl in num_err:
                num_err[cl] += 1


        classes = set()
        for cod, sheet in globalErrors["grave"]["declsRepetidas"].items():
            cl = getClasse(cod,decls)
            ensureGraveHeader(cl)
            # Header de cada tabela (uma por classe)
            if cl not in classes:
                header = f'<div class="error-section">Declarações Repetidas ({num_err[cl]}): Códigos que foram declarados mais do que uma vez</div>\n'
                header += '<table class="error-table"><tr><th>Código Repetido</th><th>Folhas</th></tr>'
                addRow(classTables, cl, header)
                classes.add(cl)

            # Linhas de cada tabela
            row = f"<tr><td><span class='error-critical'>{getCod(cod,inativos)}</span></td><td><b>{', '.join(sheet)}</b></td></tr>"
            addError(cl)
            addRow(classTables, cl, row)

        # Conclusão de cada tabela
        for cod in globalErrors["grave"]["declsRepetidas"]:
            cl = getClasse(cod,decls)
            addRow(classTables, cl, "</table>")

    # Relações Inválidas
    if globalErrors["grave"]["relsInvalidas"]:
        classes = set()

        # Contagem dos erros de cada classe
        num_err = {c:0 for c in classesN1}
        for rels in globalErrors["grave"]["relsInvalidas"].values():
            for rel in rels:
                cl = getClasse(rel[0],decls)
                if cl in num_err:
                    num_err[cl] += 1

        # Criação dos headers das tabelas para as classes
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                cl = getClasse(rel[0],decls)
                ensureGraveHeader(cl)
                if cl not in classes:
                    rels_header = f'<div class="error-section">Relações Inválidas ({num_err[cl]}): Declarações que referenciam um processo que não existe</div>\n'
                    rels_header += '<table class="error-table"><tr><th>Código</th><th>Código Inválido</th><th>Relação Inválida</th></tr>'
                    addRow(classTables, cl, rels_header)
                    classes.add(cl)

        # Linhas de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                cl = getClasse(rel[0],decls)
                rels_html = f"<tr><td>{getCod(rel[0],inativos)}</td><td><span class='error-critical'>{getCod(cod,inativos)}</span></td>"
                rels_html += f"<td><b>{rel[0]}</b> <b><i>{rel[1]}</b></i> <span class='error-critical'><b>{cod}<b></span></td></tr>"
                addError(cl)
                addRow(classTables, cl, rels_html)

        # Conclusão de cada tabela
        for cod, rels in globalErrors["grave"]["relsInvalidas"].items():
            for rel in rels:
                cl = getClasse(rel[0],decls)
                addRow(classTables, cl, "</table>")

    # Outros Erros Graves
    if globalErrors["grave"]["outro"]:
        classes = set()
        # Contagem dos erros de cada classe
        num_err = {c:0 for c in classesN1}
        for c,msgs in globalErrors["grave"]["outro"].items():
            cl = getClasse(c,decls)
            if cl in num_err:
                num_err[cl] += len(msgs)

        for cod, msgs in globalErrors["grave"]["outro"].items():
            cl = getClasse(cod,decls)
            ensureGraveHeader(cl)
            # Header de cada tabela (uma por classe)
            if cl not in classes:
                header = f'<div class="error-section">Outros Erros Graves ({num_err[cl]})</div>\n'
                header += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
                addRow(classTables, cl, header)
                classes.add(cl)

            # Linhas de cada tabela
            for msg in msgs:
                row = f"<tr><td>{getCod(cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
                addError(cl)
                addRow(classTables, cl, row)

        # Conclusão de cada tabela
        for cod in globalErrors["grave"]["outro"]:
            cl = getClasse(cod,decls)
            addRow(classTables, cl, "</table>")

    # Erros Genéricos
    if globalErrors["normal"]:
        classes = set()

        for cod, msgs in globalErrors["normal"].items():
            cl = getClasse(cod,decls)
            # Header de cada tabela (uma por classe)
            if cl not in classes:
                header = f'<div class="error-section">🟨 Erros Genéricos</div>\n'
                header += '<table class="error-table"><tr><th>Código</th><th>Mensagem</th></tr>'
                addRow(classTables, cl, header)
                classes.add(cl)

            # Linhas de cada tabela
            for msg in msgs:
                row = f"<tr><td>{getCod(cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
                addError(cl)
                addRow(classTables, cl, row)

        # Conclusão de cada tabela
        for cod in globalErrors["normal"]:
            cl = getClasse(cod,decls)
            addRow(classTables, cl, "</table>")

    # Erros de Invariantes por classe
    if globalErrors["erroInvByCod"]:
        classes = set()
        for cl, invs_dict in globalErrors["erroInvByCod"].items():

            for inv, erros in invs_dict.items():

                # Header de cada tabela (uma por classe)
                if cl not in classes:
                    addRow(classTables, cl, '<div class="error-section">🟦 Erros de Invariantes</div>\n')
                    classes.add(cl)

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

                    addError(cl)
                    html_part += f"<tr><td>{getCod(err.cod,inativos)}</td><td class='msg'>{msg}</td></tr>"
                html_part += "</table>\n"

                addRow(classTables, cl, html_part)

    # Criar o header para todas as classes existentes
    for cod,classe in classesN1.items():
        if classNumErrors[cod] > 0:
            entTitle = f'<div class="error-section">{cod} ({classNumErrors[cod]}): {classe['titulo']}</div>\n'
            classTables[cod] = entTitle + classTables[cod]
        else:
            entTitle = f'<div class="error-section">{cod}: {classe['titulo']}</div>\n'
            content = """
            <div class="no-errors">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path fill="green" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m-1 15.59-4.29-4.3
                    1.42-1.41L11 14.17l5.88-5.88 1.42 1.41Z" />
                </svg>
                <p>Nenhum erro encontrado 🎉</p>
            </div>"""
            classTables[cod] = entTitle + content

    return classTables


def generate_warnings_table(warnings):

    html_content = ""
    warnings["normal"] = []
    warnings["relHarmonizacao"] = []
    warnings["harmonizacao"] = []
    warnings["inferencias"] = []
    # Warnings
    if warnings["normal"] or warnings["relHarmonizacao"] or warnings["harmonizacao"] or warnings["inferencias"]:
        html_content += f'<div class="error-section">⚠️ Warnings</div>\n'

        # Normal
        if warnings["normal"]:
            html_content += f'<div class="error-section">Warnings Genéricos ({len(warnings["normal"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["normal"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Relações Envolvendo Processos em Harmonização
        if warnings["relHarmonizacao"]:
            html_content += f'<div class="error-section">Relações Envolvendo Processos em Harmonização ({len(warnings["relHarmonizacao"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["relHarmonizacao"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Harmonização
        if warnings["harmonizacao"]:
            html_content += f'<div class="error-section">Processos em Harmonização ({len(warnings["harmonizacao"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["harmonizacao"]:
                html_content += f"<tr><td class='msg'>{msg}</td></tr>"
            html_content += '</table>'

        # Inferências
        if warnings["inferencias"]:
            html_content += f'<div class="error-section">Inferências ({len(warnings["inferencias"])})</div>\n'
            html_content += '<table class="error-table"><tr><th>Mensagem</th></tr>'
            for msg in warnings["inferencias"]:
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
