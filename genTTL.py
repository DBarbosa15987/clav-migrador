import json
import re
from nanoid import generate
from datetime import date

agora = date.today()
# YY-mm-dd
dataAtualizacao = agora.strftime("%Y-%m-%d")
# Vou colocar o triplo nos termos de índice

# --- Migra os termos de índice ------------------------
# ------------------------------------------------------
def tiGenTTL():
    fin = open('./files/ti.json')
    fout = open('./ontologia/ti.ttl', 'w')
    termos = json.load(fin)

    ttl = ""

    ttl = """@prefix : <http://jcr.di.uminho.pt/m51-clav#> .
@prefix dc: <http://purl.org/dc/elements/1.1#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@base <http://jcr.di.uminho.pt/m51-clav> ."""

    ttl += "\n# -------------- Data de atualização da ontologia ----------\n"
    ttl += "<http://jcr.di.uminho.pt/m51-clav> dc:date \"" + dataAtualizacao + "\" .\n"
    ttl += "\n# -------------- TERMOS DE ÍNDICE --------------------------\n"

    for ti in termos:
        ticod = "ti_" + ti['codigo'] + '_' + generate('abcdef', 6)
        ttl += "###  http://jcr.di.uminho.pt/m51-clav#" + ticod + '\n'
        ttl += ":" + ticod + " rdf:type owl:NamedIndividual ,\n"
        ttl += "\t:TermoIndice ;\n"
        ttl += "\trdfs:label \"TI: " + ti['termo'] + "\";\n"
        ttl += "\t:estaAssocClasse :c" + ti['codigo'] + ";\n"
        ttl += "\t:estado \"Ativo\";\n"
        ttl += "\t:termo " + "\"" + ti['termo'] + "\"" + ".\n"

    fout.write(ttl)
    fin.close()
    fout.close()

# --- Migra a legislação -------------------------------
# ------------------------------------------------------
def legGenTTL():
    fin = open('./files/leg.json')
    fout = open('./ontologia/leg.ttl', 'w')
    leg = json.load(fin)

    ttl = ""

    ttl = """@prefix : <http://jcr.di.uminho.pt/m51-clav#> .
@prefix dc: <http://purl.org/dc/elements/1.1#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@base <http://jcr.di.uminho.pt/m51-clav> ."""

    for l in leg:
        ttl += "###  http://jcr.di.uminho.pt/m51-clav#" + l['codigo'] + '\n'
        ttl += ":leg_" + l['codigo'] + " rdf:type owl:NamedIndividual ,\n"
        ttl += "\t:Legislacao ;\n"
        ttl += "\t:codigo \"" + l['codigo'] + "\";\n"
        ttl += "\t:rdfs:label \"Leg.: " + l['codigo'] + "\";\n"
        ttl += "\t:diplomaTipo " + "\"" + l['tipo'] + "\";\n"
        ttl += "\t:diplomaNumero " + "\"" + l['numero'] + "\";\n"
        ttl += "\t:diplomaData " + "\"" + l['data'] + "\";\n"
        ttl += "\t:diplomaSumario " + "\"" + l['sumario'] + "\";\n"
        ttl += "\t:diplomaEstado " + "\"" + l['estado'] + "\";\n"
        
        if 'fonte' in l:
            ttl += "\t:diplomaFonte " + "\"" + l['fonte'] + "\";\n"

        if 'entidade' in l:
            for e in l['entidade']:
                ttl += "\t:temEntidadeResponsavel " + ":ent_" + e + ";\n"

        ttl += "\t:diplomaLink " + "\"" + l['link'] + "\".\n"

    fout.write(ttl)
    fin.close()
    fout.close()

# --- Migra as tipologias ------------------------------
# ------------------------------------------------------
def tipologiaGenTTL():
    fin = open('./files/tip.json')
    fout = open('./ontologia/tip.ttl', 'w')
    tipologias = json.load(fin)

    ttl = ""

    ttl = """@prefix : <http://jcr.di.uminho.pt/m51-clav#> .
@prefix dc: <http://purl.org/dc/elements/1.1#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@base <http://jcr.di.uminho.pt/m51-clav> ."""

    for t in tipologias:
        ttl += "###  http://jcr.di.uminho.pt/m51-clav#tip_" + t['sigla'] + '\n'
        ttl += ":tip_" + t['sigla'] + " rdf:type owl:NamedIndividual ,\n"
        ttl += "\t\t:TipologiaEntidade ;\n"
        ttl += "\t:tipEstado \"Ativa\";\n"
        ttl += "\t:tipSigla " + "\"" + t['sigla'] 
        if 'designacao' in t.keys():
            ttl += "\";\n" + "\t:tipDesignacao " + "\"" + t['designacao'] + "\".\n"
        else:
            print("AVISO: a tipologia " + t['sigla'] + " não tem designação definida.")
            ttl += ".\n"

    fout.write(ttl)
    fin.close()
    fout.close()

# --- Migra as entidades -------------------------------
# ------------------------------------------------------
def entidadeGenTTL():
    fin = open('./files/ent.json')
    fout = open('./ontologia/ent.ttl', 'w')
    entidades = json.load(fin)

    ttl = ""

    ttl = """@prefix : <http://jcr.di.uminho.pt/m51-clav#> .
@prefix dc: <http://purl.org/dc/elements/1.1#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@base <http://jcr.di.uminho.pt/m51-clav> ."""

    for e in entidades:
        ttl += "###  http://jcr.di.uminho.pt/m51-clav#ent_" + e['sigla'] + '\n'
        ttl += ":ent_" + e['sigla'] + " rdf:type owl:NamedIndividual ,\n"
        ttl += "\t\t:Entidade ;\n"

        ttl += "\t:entSigla " + "\"" + e['sigla'] + "\";\n"
        ttl += "\t:entDesignacao " + "\"" + e['designacao'] + "\";\n"

        if 'estado' in e:
            ttl += "\t:entEstado " + "\"Inativa\";\n"
        else:
            ttl += "\t:entEstado " + "\"Ativa\";\n"
            
        if 'sioe' in e:
            ttl += "\t:entSIOE " + "\"" + e['sioe'] + "\";\n"
        
        if 'dataCriacao' in e:
            ttl += "\t:entDataCriacao " + "\"" + e['dataCriacao'] + "\";\n"
            
        if 'dataExtincao' in e:
            ttl += "\t:entDataExtincao " + "\"" + e['dataExtincao'] + "\";\n"
        
        ttl += "\t:entInternacional " + "\"" + e['internacional'] + "\".\n"    
        
        if 'tipologias' in e:
            for tip in e['tipologias']:
                ttl += ":ent_" + e['sigla'] + " :pertenceTipologiaEnt " + ":tip_" + tip + " .\n"

    fout.write(ttl)
    fin.close()
    fout.close()

# --- Migra uma classe ---------------------------------
# ------------------------------------------------------
def classeGenTTL(c):
    fin = open('./files/' + c + '.json')
    fout = open('./ontologia/' + c + '.ttl', 'w')
    classes = json.load(fin)

    # Carregam-se os catálogos 
    # --------------------------------------------------
    ecatalog = open('./files/entCatalog.json')
    tcatalog = open('./files/tipCatalog.json')
    lcatalog = open('./files/legCatalog.json')
    entCatalog = json.load(ecatalog)
    tipCatalog = json.load(tcatalog)
    legCatalog = json.load(lcatalog)
    # Correspondência de intervenções e relações
    intervCatalog = {'Apreciar': 'temParticipanteApreciador','Assessorar': 'temParticipanteAssessor',
                    'Comunicar': 'temParticipanteComunicador','Decidir': 'temParticipanteDecisor',
                    'Executar': 'temParticipanteExecutor','Iniciar': 'temParticipanteIniciador'}
    
    ttl = """
@prefix : <http://jcr.di.uminho.pt/m51-clav#> .
@prefix dc: <http://purl.org/dc/elements/1.1#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@base <http://jcr.di.uminho.pt/m51-clav> .
"""
    
    for classe in classes:
        print(classe['codigo'])
        # codigo, estado, nível e título
        ttl += f"""
###  http://jcr.di.uminho.pt/m51-clav#c{ classe['codigo'] }
:c{ classe['codigo'] } rdf:type owl:NamedIndividual ;
\t:classeStatus '{ classe['estado'] }';
\trdf:type :Classe_N{classe['nivel']} ;
\t:codigo '{ classe['codigo'] }' ;
\t:titulo '{ classe['titulo'] }' ;\n"""
        # Relação hierárquica-------------------------------
        if classe['nivel'] == 1:
            ttl += "\t:pertenceLC :lc1 ;\n"
            ttl += "\t:temPai :lc1 ;\n"
        elif classe['nivel'] in [2,3,4]:
            partes = classe['codigo'].split('.')
            pai = '.'.join(partes[0:-1])
            ttl += "\t:pertenceLC :lc1 ;\n"
            ttl += "\t:temPai :c" + pai + " ;\n"
        # ------------------------------------------------
        # Descrição
        if classe["descricao"]:
            ttl += "\t:descricao '" + classe["descricao"] + "' .\n"
        # ------------------------------------------------
        # Notas de Aplicação -----------------------------
        if 'notasAp' in classe.keys():
            for n in classe['notasAp']:
                ttl += "###  http://jcr.di.uminho.pt/m51-clav#" + n['idNota'] + "\n"
                ttl += ":" + n['idNota'] + " rdf:type owl:NamedIndividual ,\n"
                ttl += "\t\t:NotaAplicacao ;\n"
                ttl += "\t:rdfs:label \"Nota de Aplicação\";\n"
                ttl += "\t:conteudo " + "\"" + n['nota'] + "\".\n\n"
                # criar as relações com das notas de aplicação com a classe
                ttl += ":c" + classe['codigo'] +" :temNotaAplicacao " + ":" + n['idNota'] + " .\n\n"
        # ------------------------------------------------
        # Exemplos de Notas de Aplicação -----------------
        if 'exemplosNotasAp' in classe.keys():
            for e in classe['exemplosNotasAp']:
                ttl += "###  http://jcr.di.uminho.pt/m51-clav#" + e['idExemplo'] + "\n"
                ttl += ":" + e['idExemplo'] + " rdf:type owl:NamedIndividual ,\n"
                ttl += "\t\t:ExemploNotaAplicacao ;\n"
                ttl += "\t:rdfs:label \"Exemplo de nota de aplicação\";\n"
                ttl += "\t:conteudo " + "\"" + e['exemplo'] + "\".\n\n"
                # criar as relações com das notas de aplicação com a classe
                ttl += ":c" + classe['codigo'] +" :temExemploNA " + ":" + e['idExemplo'] + " .\n\n"
        # ------------------------------------------------
        # Notas de Exclusão ------------------------------
        if 'notasEx' in classe.keys():
            for n in classe['notasEx']:
                ttl += "###  http://jcr.di.uminho.pt/m51-clav#" + n['idNota'] + "\n"
                ttl += ":" + n['idNota'] + " rdf:type owl:NamedIndividual ,\n"
                ttl += "\t\t:NotaExclusao ;\n"
                ttl += "\t:rdfs:label \"Nota de Exclusão\";\n"
                nota = re.sub(r'\"', '\"', n['nota'])
                ttl += "\t:conteudo " + "\"" + nota + "\".\n\n"
                # criar as relações com das notas de aplicação com a classe
                ttl += ":c" + classe['codigo'] + " :temNotaExclusao " + ":" + n['idNota'] + " .\n\n"
        # ------------------------------------------------
        # Tipo de Processo -------------------------------
        if 'tipoProc' in classe.keys():
            if classe['tipoProc'] == 'PC':
                ttl += ":c" + classe['codigo'] + " :processoTipoVC :vc_processoTipo_pc .\n"
            else:
                ttl += ":c" + classe['codigo'] + " :processoTipoVC :vc_processoTipo_pe .\n"
        # ------------------------------------------------
        # Transversalidade -------------------------------
        if 'procTrans' in classe.keys():
            ttl += ":c" + classe['codigo'] + " :processoTransversal " + "\"" + classe['procTrans'] + "\" .\n"
        # ------------------------------------------------
        # Donos
        # ------------------------------------------------
        if 'donos' in classe.keys():
            for d in classe['donos']:
                if d in entCatalog:
                    prefixo = 'ent_'
                else:
                    prefixo = 'tip_'
                ttl += ":c" + classe['codigo'] + " :temDono" + " :" + prefixo + d + " .\n"
        # ------------------------------------------------
        # Participantes ----------------------------------
        # Um processo tem participantes se for transversal
        if 'procTrans' in classe.keys() and classe['procTrans'] == 'S':
            for p in classe['participantes']:
                if p['id'] in entCatalog:
                    prefixo = 'ent_'
                else:
                    prefixo = 'tip_'
                ttl += ":c" + classe['codigo'] + " :" + intervCatalog[p['interv']] + " :" + prefixo + p['id'] + " .\n"
        # ------------------------------------------------
        # Legislação -------------------------------------
        if 'legislacao' in classe.keys():
            for l in classe['legislacao']:
                if l in legCatalog:
                    ttl += ":c" + classe['codigo'] + " :temLegislacao" + " :leg_" + l + " .\n"
        # ------------------------------------------------------------
        # Processos Relacionados -------------------------------------
        if 'processosRelacionados' in classe:
            for index, p in enumerate(classe['processosRelacionados']):
                ttl += ":c" + classe['codigo'] + " :temRelProc" + " :c" + p + " .\n"
                if 'proRel' in classe:
                    ttl += ":c" + classe['codigo'] + " :" + classe['proRel'][index] + " :c" + p + " .\n"
        # ------------------------------------------------------------
        # PCA --------------------------------------------------------
        if 'pca' in classe:
            ttl += ":c" + classe['codigo'] + " :temPCA :pca_c" + classe['codigo'] + ".\n"
            ttl += "###  http://jcr.di.uminho.pt/m51-clav#pca_c" + classe['codigo'] + "\n"
            ttl += ":pca_c" + classe['codigo'] + " rdf:type owl:NamedIndividual ,\n"
            ttl += "\t:PCA .\n"
            if type(classe['pca']['valores']) != list:
                if str(classe['pca']['valores']) == 'NE':
                    ttl += ":pca_c" + classe['codigo'] + " :pcaValor \"NE\" .\n"
                else:
                    ttl += ":pca_c" + classe['codigo'] + " :pcaValor " + str(classe['pca']['valores']) + ".\n"
            else:
                for v in classe['pca']['valores']:
                    ttl += ":pca_c" + classe['codigo'] + " :pcaValor " + str(v) + ".\n"
        # ------------------------------------------------------------
        # Nota ao PCA ------------------------------------------------
            if 'notas' in classe['pca']:
                ttl += ":pca_c" + classe['codigo'] + " :pcaNota " + "\"" + classe['pca']['notas'] + "\".\n"
        # ------------------------------------------------------------
        # Forma de Contagem do PCA -----------------------------------
            if 'formaContagem' in classe['pca']:
                ttl += ":pca_c" + classe['codigo'] + " :pcaFormaContagemNormalizada :vc_pcaFormaContagem_" + classe['pca']['formaContagem'] + " .\n"
            if 'subFormaContagem' in classe['pca']:
                ttl += ":pca_c" + classe['codigo'] + " :pcaSubformaContagem :vc_pcaSubformaContagem_" + classe['pca']['subFormaContagem'] + " .\n"
        # ------------------------------------------------------------
        # Justificação do PCA ----------------------------------------
            if 'justificacao' in classe['pca']:
                ttl += "###  http://jcr.di.uminho.pt/m51-clav#just_pca_c" + classe['codigo'] + "\n"
                ttl += ":just_pca_c" + classe['codigo'] + " rdf:type owl:NamedIndividual ,\n"
                ttl += "\t\t:JustificacaoPCA .\n"
                ttl += ":pca_c"  + classe['codigo'] + " :temJustificacao :just_pca_c" + classe['codigo'] + " .\n"
                for crit in classe['pca']['justificacao']:
                    ttl += ":" + crit['critCodigo'] + " rdf:type owl:NamedIndividual ,\n"

                    if crit['tipo'] == 'legal':
                        ttl += "\t\t:CriterioJustificacaoLegal ;\n"
                    elif crit['tipo'] == 'utilidade':
                        ttl += "\t\t:CriterioJustificacaoUtilidadeAdministrativa ;\n"
                    elif crit['tipo'] == 'gestionário':
                        ttl += "\t\t:CriterioJustificacaoGestionario ;\n"

                    ttl += "\t:conteudo \"" + crit['conteudo'] + "\" .\n"
                    ttl += ":just_pca_c" + classe['codigo'] + " :temCriterio :" + crit['critCodigo'] + ". \n"

                    if 'legRefs' in crit:
                        for ref in crit['legRefs']:
                            ttl += ":" + crit['critCodigo'] + " :critTemLegAssoc :leg_" + ref + " .\n"

                    if 'procRefs' in crit:
                        for ref in crit['procRefs']:
                            ttl += ":" + crit['critCodigo'] + " :critTemProcRel :c" + ref + " .\n"

        # ------------------------------------------------------------
        # DF ---------------------------------------------------------
        if 'df' in classe:
            ttl += ":c" + classe['codigo'] + " :temDF :df_c" + classe['codigo'] + ".\n"
            ttl += "###  http://jcr.di.uminho.pt/m51-clav#df_c" + classe['codigo'] + "\n"
            ttl += ":df_c" + classe['codigo'] + " rdf:type owl:NamedIndividual ,\n"
            ttl += "\t\t:DestinoFinal .\n"

            ttl += ":df_c" + classe['codigo'] + " :dfValor \"" + classe['df']['valor'] + "\" .\n"

            if 'nota' in classe['df']:
                ttl += ":df_c" + classe['codigo'] + " :dfNota \"" + classe['df']['nota'] + "\" .\n"

        # ------------------------------------------------------------
        # Justificação do DF -----------------------------------------
            if 'justificacao' in classe['df']:
                ttl += "###  http://jcr.di.uminho.pt/m51-clav#just_df_c" + classe['codigo'] + "\n"
                ttl += ":just_df_c" + classe['codigo'] + " rdf:type owl:NamedIndividual ,\n"
                ttl += "\t\t:JustificacaoDF .\n"
                ttl += ":df_c"  + classe['codigo'] + " :temJustificacao :just_df_c" + classe['codigo'] + " .\n"
                for crit in classe['df']['justificacao']:
                    ttl += ":" + crit['critCodigo'] + " rdf:type owl:NamedIndividual ,\n"

                    if crit['tipo'] == 'legal':
                        ttl += "\t\t:CriterioJustificacaoLegal ;\n"
                    elif crit['tipo'] == 'densidade':
                        ttl += "\t\t:CriterioJustificacaoDensidadeInfo ;\n"
                    elif crit['tipo'] == 'complementaridade':
                        ttl += "\t\t:CriterioJustificacaoComplementaridadeInfo ;\n"

                    ttl += "\t:conteudo \"" + crit['conteudo'] + "\" .\n"
                    ttl += ":just_df_c" + classe['codigo'] + " :temCriterio :" + crit['critCodigo'] + ". \n"

                    if 'legRefs' in crit:
                        for ref in crit['legRefs']:
                            ttl += ":" + crit['critCodigo'] + " :critTemLegAssoc :leg_" + ref + " .\n"

                    if 'procRefs' in crit:
                        for ref in crit['procRefs']:
                            ttl += ":" + crit['critCodigo'] + " :critTemProcRel :c" + ref + " .\n"
    

    fout.write(ttl)
    
    fin.close()
    fout.close()

# Invocação dos migradores -----------------------------------------------------------

tiGenTTL()
entidadeGenTTL()
tipologiaGenTTL()
legGenTTL()

classes = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']
for c in classes:
    print('Classe: ', c)
    classeGenTTL(c)

    