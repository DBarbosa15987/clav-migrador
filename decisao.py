import pandas as pd
import re
brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
sepExtra = re.compile(r'#$|^#')

def procDecisoes(classe, myReg, ListaErros, entCatalog, tipCatalog, legCatalog):
    # PCA -----
    if classe["Prazo de conservação administrativa"]:
        myReg['pca'] = {}
        if type(classe["Prazo de conservação administrativa"]) not in [int, float]:
            pca = brancos.sub('', classe["Prazo de conservação administrativa"])
        else:
            pca = classe["Prazo de conservação administrativa"]
        # Verifica-se se tem alguma coisa
        if pd.isna(pca):
            myReg['pca']['valores'] = "NE"
        else: 
            if type(classe["Prazo de conservação administrativa"]) not in [int, float]:
                if re.search(r'\d+', pca):
                    if re.search(r'#', str(pca)):
                        pca = sepExtra.sub('', pca)
                        valores = pca.split('#')
                        myReg['pca']['valores'] = list(map(int, valores))
                    else:
                        myReg['pca']['valores'] = pca
                else:
                    myReg['pca']['valores'] = "NE"
            else:
                myReg['pca']['valores'] = pca
    # Nota ao PCA ----------------------------
    if classe["Nota ao PCA"]:
        myReg['pca']['notas'] = brancos.sub('', classe["Nota ao PCA"])
    # ERRO: um dos dois, PCA ou Nota ao PCA, tem de ter um valor válido
    if myReg["estado"]!='H':
        if classe["Prazo de conservação administrativa"] and (myReg['pca']['valores'] == "NE") and 'notas' not in myReg['pca'].keys():
            ListaErros.append('Erro::' + myReg['codigo'] + '::PCA e Nota ao PCA não podem ser simultaneamente inválidos')
    # Forma de Contagem do PCA -----
    if 'pca' in myReg.keys() and myReg['pca']['valores'] != "NE":
        formaContagem = brancos.sub('', str(classe["Forma de contagem do PCA"]))
        if re.search(r'conclusão.*procedimento', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'conclusaoProcedimento'
        elif re.search(r'cessação.*vigência', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'cessacaoVigencia'
        elif re.search(r'extinção.*entidade', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'extincaoEntidade'
        elif re.search(r'extinção.*direito', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'extincaoDireito'
        elif re.search(r'início.*procedimento', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'inicioProcedimento'
        elif re.search(r'emissão.*título', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'emissaoTitulo'
        elif re.search(r'disposição.*legal', formaContagem, re.I):
            myReg['pca']['formaContagem'] = 'disposicaoLegal'
            if re.search(r'10\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.10'
            elif re.search(r'11\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.11'
            elif re.search(r'12\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.12'
            elif re.search(r'1\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.01'
            elif re.search(r'2\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.02'
            elif re.search(r'3\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.03'
            elif re.search(r'4\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.04'
            elif re.search(r'5\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.05'
            elif re.search(r'6\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.06'
            elif re.search(r'7\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.07'
            elif re.search(r'8\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.08'
            elif re.search(r'9\s+-', formaContagem):
                myReg['pca']['subFormaContagem'] = 'F01.09'
            else:
                ListaErros.append('Erro::' + myReg['codigo'] + '::Não consegui extrair a subforma de contagem::' + formaContagem)
        else:
            myReg['pca']['formaContagem'] = "Desconhecida"
            ListaErros.append('Erro::' + myReg['codigo'] + '::Forma de contagem do PCA desconhecida::' + formaContagem)
    # Justificação do PCA -----
    if 'pca' in myReg and classe["Justificação PCA"]:
        just = brancos.sub('', classe["Justificação PCA"])
        just = sepExtra.sub('', just)
        criterios = just.split('#')
        myReg['pca']['justificacao'] = []
        for index,crit in enumerate(criterios):
            jcodigo = "just_pca_c" + myReg['codigo'] + "_" + str(index)
            myCrit = {'critCodigo': jcodigo}
            # --- Critério Legal ------------------------------------------
            if res := re.search(r'(?:Critério legal:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'legal'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                myCrit['legRefs'] = []
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                for ref in legRefs:
                    myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-\u2010]+', '_', ref.group(1)))  
                for ref in myCrit['legRefs']:
                    # ERRO: Legislação referenciado no critério não existe no catálogo
                    if ref not in legCatalog:
                        ListaErros.append('Erro::' + jcodigo + '::Legislação inexistente no catálogo legislativo::' + ref)
                    else:
                        if 'legislacao' in myReg and ref not in myReg['legislacao']:
                            # ListaErros.append('Aviso::' + jcodigo + '::Legislação usado no critério não está incluída no contexto, será incluída::' + ref)
                            myReg['legislacao'].append(ref)
            # --- Critério Gestionário ------------------------------------
            if res := re.search(r'(?:Critério gestionário:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'gestionário'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                # Referências a legislação no texto do critério -----------
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                if len(list(legRefs)) > 0:
                    myCrit['legRefs'] = []
                    for ref in legRefs:
                        myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-]+', '_', ref.group(1)))
                # Referências a processos no texto do critério -----------
                procRefs = re.finditer(r'\d{3}\.\d{2,3}\.\d{3}', myCrit['conteudo'])
                myRefs = []
                for ref in procRefs:
                    myRefs.append(ref.group())
                if len(myRefs) > 0:
                    myCrit['procRefs'] = myRefs
                    # ERRO: Todos os processos referenciados têm de estar na zona de contexto
                    for ref in myRefs:
                        if 'processosRelacionados' in myReg and ref not in myReg['processosRelacionados']:
                            ListaErros.append('ERRO::' + jcodigo + '::Processo usado no critério não está incluído no contexto::' + ref)
            # --- Critério de Utilidade Administrativa ------------------------------------
            if res := re.search(r'(?:Critério de utilidade administrativa:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'utilidade'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                # Referências a legislação no texto do critério -----------
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                if len(list(legRefs)) > 0:
                    myCrit['legRefs'] = []
                    for ref in legRefs:
                        myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-]+', '_', ref.group(1)))
                # Referências a processos no texto do critério -----------
                procRefs = re.finditer(r'\d{3}\.\d{2,3}\.\d{3}', myCrit['conteudo'])
                myRefs = []
                for ref in procRefs:
                    myRefs.append(ref.group())
                if len(myRefs) > 0:
                    myCrit['procRefs'] = myRefs
                    # ERRO: Todos os processos referenciados têm de estar na zona de contexto (classes N3)
                    for ref in myRefs:
                        if 'processosRelacionados' in myReg and ref not in myReg['processosRelacionados']:
                            ListaErros.append('ERRO::' + jcodigo + '::Processo usado no critério não está incluído no contexto::' + ref)

            myReg['pca']['justificacao'].append(myCrit)
      
    # DF ------------------------------------------------------
    # print("--> ", myReg['codigo'])
    if classe["Destino final"]:
        myReg['df'] = {}
        df = brancos.sub('', classe["Destino final"]).upper()
        # Verifica-se se tem alguma coisa
        if re.search(r'C|CP|E|NE', df):
            myReg['df']['valor'] = df
        else: 
            if myReg["estado"]!='H':
                ListaErros.append('Erro::' + myReg['codigo'] + '::Valor inválido para o DF::' + df)
    # Nota ao DF ------------------------------------------------------
    if "Nota ao DF" in classe and classe["Nota ao DF"]:
        myReg['df']['nota'] = brancos.sub('', classe["Nota ao DF"])
    # ERRO: um dos dois, DF ou Nota ao DF, tem de ter um valor válido
    if myReg["estado"]!='H' and classe["Destino final"] and (myReg['df']['valor'] == "NE") and not myReg['df']['nota']:
        ListaErros.append('Erro::' + myReg['codigo'] + '::DF e Nota ao DF não podem ser simultaneamente inválidos')
    # Justificação do DF ----------------------------------------------
    if 'df' in myReg and classe["Justificação DF"]:
        just = brancos.sub('', classe["Justificação DF"])
        just = sepExtra.sub('', just)
        criterios = just.split('#')
        myReg['df']['justificacao'] = []
        for index,crit in enumerate(criterios):
            jcodigo = "just_df_c" + myReg['codigo'] + "_" + str(index)
            myCrit = {'critCodigo': jcodigo}
            # --- Critério Legal ------------------------------------------
            if res := re.search(r'(?:Critério legal:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'legal'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                myCrit['legRefs'] = []
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                for ref in legRefs:
                    myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-]+', '_', ref.group(1)))
                for ref in myCrit['legRefs']:
                    # ERRO: Legislação referenciado no critério não existe no catálogo
                    if ref not in legCatalog:
                        ListaErros.append('Erro::' + jcodigo + '::Legislação inexistente no catálogo legislativo::' + ref)
                    else:
                        if 'legislacao' in myReg and ref not in myReg['legislacao']:
                            # ListaErros.append('Aviso::' + jcodigo + '::Legislação usado no critério não está incluída no contexto, será incluída::' + ref)
                            myReg['legislacao'].append(ref)
            # --- Critério de Densidade Informacional ------------------------------------------
            if res := re.search(r'(?:Critério de densidade informacional:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'densidade'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                # Referências a legislação no texto do critério -----------
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                if len(list(legRefs)) > 0:
                    myCrit['legRefs'] = []
                    for ref in legRefs:
                        myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-]+', '_', ref.group(1)))
                    for ref in myCrit['legRefs']:
                        # ERRO: Legislação referenciado no critério não existe no catálogo
                        if ref not in legCatalog:
                            ListaErros.append('Erro::' + jcodigo + '::Legislação inexistente no catálogo legislativo::' + ref)
                        else:
                            if 'legislacao' in myReg and ref not in myReg['legislacao']:
                                # ListaErros.append('Aviso::' + jcodigo + '::Legislação usado no critério não está incluída no contexto, será incluída::' + ref)
                                myReg['legislacao'].append(ref)
                # Referências a processos no texto do critério -----------
                procRefs = re.finditer(r'\d{3}\.\d{2,3}\.\d{3}', myCrit['conteudo'])
                myRefs = []
                for ref in procRefs:
                    myRefs.append(ref.group())
                if len(myRefs) > 0:
                    myCrit['procRefs'] = myRefs
                    # ERRO: Todos os processos referenciados têm de estar na zona de contexto
                    for ref in myRefs:
                        if 'processosRelacionados' in myReg and ref not in myReg['processosRelacionados']:
                            ListaErros.append('ERRO::' + jcodigo + '::Processo usado no critério não está incluído no contexto::' + ref)
            # --- Critério de Complementaridade Informacional ------------------------------------------
            if res := re.search(r'(?:Critério de complementaridade informacional:\s*)(.+)', crit, re.I):
                myCrit['tipo'] = 'complementaridade'
                conteudo = res.group(1)
                myCrit['conteudo'] = conteudo
                # Referências a legislação no texto do critério -----------
                legRefs = re.finditer(r'(?:\[)([a-zA-Z0-9\-\/ ]+)(?:\])', myCrit['conteudo'])
                if len(list(legRefs)) > 0:
                    myCrit['legRefs'] = []
                    for ref in legRefs:
                        myCrit['legRefs'].append(re.sub(r'[/ \u202F\u00A0()\-]+', '_', ref.group(1)))
                    for ref in myCrit['legRefs']:
                        # ERRO: Legislação referenciado no critério não existe no catálogo
                        if ref not in legCatalog:
                            ListaErros.append('Erro::' + jcodigo + '::Legislação inexistente no catálogo legislativo::' + ref)
                        else:
                            if 'legislacao' in myReg and ref not in myReg['legislacao']:
                                # ListaErros.append('Aviso::' + jcodigo + '::Legislação usado no critério não está incluída no contexto, será incluída::' + ref)
                                myReg['legislacao'].append(ref)
                # Referências a processos no texto do critério -----------
                procRefs = re.finditer(r'\d{3}\.\d{2,3}\.\d{3}', myCrit['conteudo'])
                myRefs = []
                for ref in procRefs:
                    myRefs.append(ref.group())
                if len(myRefs) > 0:
                    myCrit['procRefs'] = myRefs
                    # ERRO: Todos os processos referenciados têm de estar na zona de contexto
                    for ref in myRefs:
                        if 'processosRelacionados' in myReg and ref not in myReg['processosRelacionados']:
                            ListaErros.append('ERRO::' + jcodigo + '::Processo usado no critério não está incluído no contexto::' + ref)

            myReg['df']['justificacao'].append(myCrit)
            
    if classe["Notas"]:
        myReg["Notas"] = classe["Notas"]
        