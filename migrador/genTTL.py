import glob
import json
import re
import subprocess
from nanoid import generate
from datetime import date, datetime
from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, URIRef
from rdflib.namespace import RDF,OWL
import os
from utils.path_utils import FILES_DIR, ONTOLOGY_DIR, OUTPUT_DIR
from utils.log_utils import GEN
import logging
import zipfile

logger = logging.getLogger(GEN)

ns = Namespace("http://jcr.di.uminho.pt/m51-clav#")
dc = Namespace("http://purl.org/dc/elements/1.1/")
uri_ontologia = URIRef("http://jcr.di.uminho.pt/m51-clav")

agora = date.today()
# YY-mm-dd
dataAtualizacao = agora.strftime("%Y-%m-%d")
# Vou colocar o triplo nos termos de índice

# --- Migra os termos de índice ------------------------
# ------------------------------------------------------
def tiGenTTL(termosIndice):

    logger.info("Geração da ontologia dos termos índice")

    g = Graph()
    g.bind("", ns)
    g.bind("dc", dc)
    g.add((uri_ontologia, dc.date, Literal(dataAtualizacao)))

    for ti in termosIndice:
        ticod = "ti_" + ti['codigo'] + '_' + generate('abcdef', 6)
        tiUri = ns[ticod]
        g.add((tiUri,RDF.type, OWL.NamedIndividual))
        g.add((tiUri,RDF.type, ns.TermoIndice))
        g.add((tiUri, RDFS.label, Literal(f"TI: {ti['termo']}")))
        g.add((tiUri, ns.estaAssocClasse, ns[f"c{ti['codigo']}"]))
        g.add((tiUri, ns.estado, Literal("Ativo")))
        g.add((tiUri, ns.termo, Literal(ti['termo'])))

    g.serialize(format="ttl",destination=os.path.join(ONTOLOGY_DIR,"ti.ttl"))
    logger.info("Geração da ontologia dos termos índice terminada")


# --- Migra a legislação -------------------------------
# ------------------------------------------------------
def legGenTTL():

    logger.info("Geração da ontologia da legislação")
    fin = open(os.path.join(FILES_DIR,"leg.json"))
    leg = json.load(fin)

    g = Graph()
    g.bind("", ns)

    for l in leg:
        cod = l['codigo']
        lcod = "leg_" + cod
        lUri = ns[lcod]
        g.add((lUri,RDF.type, OWL.NamedIndividual))
        g.add((lUri,RDF.type, ns.Legislacao))
        g.add((lUri,ns.codigo,Literal(cod)))
        g.add((lUri,RDFS.label, Literal(f"Leg.: {cod}")))
        g.add((lUri,ns.diplomaTipo,Literal(l['tipo'])))
        g.add((lUri,ns.diplomaNumero,Literal(l['numero'])))
        g.add((lUri,ns.diplomaData,Literal(l['data'])))
        g.add((lUri,ns.diplomaSumario,Literal(l['sumario'])))
        g.add((lUri,ns.diplomaEstado,Literal(l['estado'])))

        if 'fonte' in l:
            g.add((lUri,ns.diplomaFonte,Literal(l['fonte'])))

        if 'entidade' in l:
            for e in l['entidade']:
                g.add((lUri,ns.temEntidadeResponsavel,ns[f"ent_{e}"]))

        g.add((lUri,ns.diplomaLink,Literal(l['link'])))

    fin.close()
    g.serialize(format="ttl",destination=os.path.join(ONTOLOGY_DIR,"leg.ttl"))
    logger.info("Geração da ontologia da legislação terminada")


# --- Migra as tipologias ------------------------------
# ------------------------------------------------------
def tipologiaGenTTL():

    logger.info("Geração da ontologia da tipologia")
    fin = open(os.path.join(FILES_DIR,"tip.json"))
    tipologias = json.load(fin)

    g = Graph()
    g.bind("", ns)

    for t in tipologias:
        sigla = t['sigla']
        tcod = "tip_" + sigla
        tUri = ns[tcod]
        g.add((tUri,RDF.type, OWL.NamedIndividual))
        g.add((tUri,RDF.type, ns.TipologiaEntidade))
        g.add((tUri,ns.tipEstado, Literal("Ativa")))
        g.add((tUri,ns.tipSigla, Literal(sigla)))
        if 'designacao' in t.keys():
            g.add((tUri,ns.tipDesignacao, Literal(t['designacao'])))

    fin.close()
    g.serialize(format="ttl",destination=os.path.join(ONTOLOGY_DIR,"tip.ttl"))
    logger.info("Geração da ontologia da tipologia terminada")


# --- Migra as entidades -------------------------------
# ------------------------------------------------------
def entidadeGenTTL():

    logger.info("Geração da ontologia das entidades")
    fin = open(os.path.join(FILES_DIR,"ent.json"))
    entidades = json.load(fin)

    g = Graph()
    g.bind("", ns)

    for e in entidades:
        sigla = e['sigla']
        ecod = "ent_" + sigla
        eUri = ns[ecod]
        g.add((eUri,RDF.type, OWL.NamedIndividual))
        g.add((eUri,RDF.type, ns.Entidade))
        g.add((eUri,ns.entSigla, Literal(sigla)))
        g.add((eUri,ns.entDesignacao, Literal(e['designacao'])))

        if 'estado' in e:
            g.add((eUri,ns.entEstado, Literal("Inativa")))
        else:
            g.add((eUri,ns.entEstado, Literal("Ativa")))

        if 'sioe' in e:
            g.add((eUri,ns.entSIOE, Literal(e['sioe'])))

        if 'dataCriacao' in e:
            g.add((eUri,ns.entDataCriacao, Literal(e['dataCriacao'])))

        if 'dataExtincao' in e:
            g.add((eUri,ns.entDataExtincao, Literal(e['dataExtincao'])))

        g.add((eUri,ns.entInternacional, Literal(e['internacional'])))
        if 'tipologias' in e:
            for tip in e['tipologias']:
                g.add((ns[f"ent_{sigla}"],ns.pertenceTipologiaEnt,ns[f"tip_{tip}"]))

    fin.close()
    g.serialize(format="ttl",destination=os.path.join(ONTOLOGY_DIR,"ent.ttl"))
    logger.info("Geração da ontologia das entidades terminada")


# --- Migra uma classe ---------------------------------
# ------------------------------------------------------
def classeGenTTL(clN1,classes):

    logger.info(f"Geração da ontologia da classe {clN1}")

    # Carregam-se os catálogos
    # --------------------------------------------------
    ecatalog = open(os.path.join(FILES_DIR,"entCatalog.json"))
    lcatalog = open(os.path.join(FILES_DIR,"legCatalog.json"))
    entCatalog = json.load(ecatalog)
    legCatalog = json.load(lcatalog)

    # Correspondência de intervenções e relações
    intervCatalog = {'Apreciar': 'temParticipanteApreciador','Assessorar': 'temParticipanteAssessor',
                    'Comunicar': 'temParticipanteComunicador','Decidir': 'temParticipanteDecisor',
                    'Executar': 'temParticipanteExecutor','Iniciar': 'temParticipanteIniciador'}

    g = Graph()
    g.bind("", ns)

    for cod,classe in classes.items():
        # codigo, estado, nível e título
        codigoUri = ns[f"c{cod}"]
        g.add((codigoUri,RDF.type, OWL.NamedIndividual))
        g.add((codigoUri,ns.classeStatus, Literal(classe['estado'])))
        g.add((codigoUri,RDF.type, ns[f"Classe_N{classe['nivel']}"]))
        g.add((codigoUri,ns.codigo, Literal(cod)))
        g.add((codigoUri,ns.titulo, Literal(classe['titulo'])))

        # Relação hierárquica-------------------------------
        if classe['nivel'] == 1:
            g.add((codigoUri,ns.pertenceLC, ns.lc1))
            g.add((codigoUri,ns.temPai, ns.lc1))
        elif classe['nivel'] in [2,3,4]:
            partes = cod.split('.')
            pai = '.'.join(partes[0:-1])
            g.add((codigoUri,ns.pertenceLC, ns.lc1))
            g.add((codigoUri,ns.temPai, ns[f"c{pai}"]))

        # ------------------------------------------------
        # Descrição
        if classe["descricao"]:
            g.add((codigoUri,ns.descricao, Literal(classe["descricao"])))

        # ------------------------------------------------
        # Notas de Aplicação -----------------------------
        if 'notasAp' in classe.keys():
            for n in classe['notasAp']:

                notaUri = ns[n['idNota']]
                g.add((notaUri,RDF.type, OWL.NamedIndividual))
                g.add((notaUri,RDF.type, ns.NotaAplicacao))
                g.add((notaUri,RDFS.label, Literal("Nota de Aplicação")))
                g.add((notaUri,ns.conteudo, Literal(n['nota'])))
                # criar as relações com das notas de aplicação com a classe
                g.add((codigoUri,ns.temNotaAplicacao, ns[n['idNota']]))

        # ------------------------------------------------
        # Exemplos de Notas de Aplicação -----------------
        if 'exemplosNotasAp' in classe.keys():
            for e in classe['exemplosNotasAp']:

                exemploUri = ns[e['idExemplo']]
                g.add((exemploUri,RDF.type, OWL.NamedIndividual))
                g.add((exemploUri,RDF.type, ns.ExemploNotaAplicacao))
                g.add((exemploUri,RDFS.label, Literal("Exemplo de nota de aplicação")))
                g.add((exemploUri,ns.conteudo, Literal(e['exemplo'])))
                # criar as relações com das notas de aplicação com a classe
                g.add((codigoUri,ns.temExemploNA, ns[e['idExemplo']]))

        # ------------------------------------------------
        # Notas de Exclusão ------------------------------
        if 'notasEx' in classe.keys():
            for n in classe['notasEx']:

                notaUri = ns[n['idNota']]
                g.add((notaUri,RDF.type, OWL.NamedIndividual))
                g.add((notaUri,RDF.type, ns.NotaExclusao))
                g.add((notaUri,RDFS.label, Literal("Nota de Exclusão")))
                nota = re.sub(r'\"', '\"', n['nota'])
                g.add((notaUri,ns.conteudo, Literal(nota)))
                # criar as relações com das notas de aplicação com a classe
                g.add((codigoUri,ns.temNotaExclusao, ns[n['idNota']]))

        # ------------------------------------------------
        # Tipo de Processo -------------------------------
        if 'tipoProc' in classe.keys():
            if classe['tipoProc'] == 'PC':
                g.add((codigoUri,ns.processoTipoVC,ns.vc_processoTipo_pc))
            else:
                g.add((codigoUri,ns.processoTipoVC,ns.vc_processoTipo_pe))
        # ------------------------------------------------
        # Transversalidade -------------------------------
        if 'procTrans' in classe.keys():
            g.add((codigoUri,ns.processoTransversal,Literal(classe['procTrans'])))
        # ------------------------------------------------
        # Donos
        # ------------------------------------------------
        if 'donos' in classe.keys():
            for d in classe['donos']:
                if d in entCatalog:
                    prefixo = 'ent_'
                else:
                    prefixo = 'tip_'
                g.add((codigoUri,ns.temDono,ns[prefixo + d]))

        # ------------------------------------------------
        # Participantes ----------------------------------
        # Um processo tem participantes se for transversal
        if 'procTrans' in classe.keys() and classe['procTrans'] == 'S':
            for p in classe['participantes']:
                if p['id'] in entCatalog:
                    prefixo = 'ent_'
                else:
                    prefixo = 'tip_'
                g.add((codigoUri,ns[intervCatalog[p['interv']]],ns[prefixo + p['id']]))

        # ------------------------------------------------
        # Legislação -------------------------------------
        if 'legislacao' in classe.keys():
            for l in classe['legislacao']:
                if l in legCatalog:
                    g.add((codigoUri,ns.temLegislacao,ns[f"leg_{l}"]))

        # ------------------------------------------------------------
        # Processos Relacionados -------------------------------------
        if 'processosRelacionados' in classe:
            for index, p in enumerate(classe['processosRelacionados']):

                g.add((codigoUri,ns.temRelProc,ns[f"c{p}"]))
                if 'proRel' in classe:
                    g.add((codigoUri,ns[classe['proRel'][index]],ns[f"c{p}"]))

        # ------------------------------------------------------------
        # PCA --------------------------------------------------------
        if 'pca' in classe:

            pcaUri = ns[f"pca_c{cod}"]
            g.add((codigoUri,ns.temPCA,pcaUri))
            g.add((pcaUri,RDF.type,OWL.NamedIndividual))
            g.add((pcaUri,RDF.type,ns.PCA))

            if type(classe['pca']['valores']) != list:
                if str(classe['pca']['valores']) == 'NE':
                    g.add((pcaUri,ns.pcaValor,Literal("NE")))
                else:
                    g.add((pcaUri,ns.pcaValor,Literal(str(classe['pca']['valores']))))
            else:
                for v in classe['pca']['valores']:
                    g.add((pcaUri,ns.pcaValor,Literal(str(v))))

        # ------------------------------------------------------------
        # Nota ao PCA ------------------------------------------------
            if 'notas' in classe['pca']:
                g.add((pcaUri,ns.pcaNota,Literal(classe['pca']['notas'])))

        # ------------------------------------------------------------
        # Forma de Contagem do PCA -----------------------------------
            if 'formaContagem' in classe['pca']:
                g.add((pcaUri,ns.pcaFormaContagemNormalizada,ns[f"vc_pcaFormaContagem_{classe['pca']['formaContagem']}"]))
            if 'subFormaContagem' in classe['pca']:
                g.add((pcaUri,ns.pcaSubformaContagem,ns[f"vc_pcaSubformaContagem_{classe['pca']['subFormaContagem']}"]))

        # ------------------------------------------------------------
        # Justificação do PCA ----------------------------------------
            if 'justificacao' in classe['pca']:

                justUri = ns[f"just_pca_c{cod}"]
                g.add((justUri,RDF.type,OWL.NamedIndividual))
                g.add((justUri,RDF.type,ns.JustificacaoPCA))
                g.add((ns[f"pca_c{cod}"],ns.temJustificacao,justUri))

                for crit in classe['pca']['justificacao']:

                    critUri = ns[crit['critCodigo']]
                    g.add((critUri,RDF.type,OWL.NamedIndividual))

                    if crit['tipo'] == 'legal':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoLegal))
                    elif crit['tipo'] == 'utilidade':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoUtilidadeAdministrativa))
                    elif crit['tipo'] == 'gestionário':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoGestionario))

                    g.add((critUri,ns.conteudo,Literal(crit['conteudo'])))
                    g.add((justUri,ns.temCriterio,ns[crit['critCodigo']]))

                    if 'legRefs' in crit:
                        for ref in crit['legRefs']:
                            g.add((critUri,ns.critTemLegAssoc,ns[f"leg_{ref}"]))

                    if 'procRefs' in crit:
                        for ref in crit['procRefs']:
                            g.add((critUri,ns.critTemProcRel,ns[f"c{ref}"]))

        # ------------------------------------------------------------
        # DF ---------------------------------------------------------
        if 'df' in classe:

            dfUri = ns[f"df_c{cod}"]

            g.add((codigoUri,ns.temDF,dfUri))
            g.add((dfUri,RDF.type,OWL.NamedIndividual))
            g.add((dfUri,RDF.type,ns.DestinoFinal))
            g.add((dfUri,ns.dfValor,Literal(classe['df']['valor'])))

            if 'nota' in classe['df']:
                g.add((dfUri,ns.dfNota,Literal(classe['df']['nota'])))

        # ------------------------------------------------------------
        # Justificação do DF -----------------------------------------
            if 'justificacao' in classe['df']:

                justDfUri = ns[f"just_df_c{cod}"]
                g.add((justDfUri,RDF.type,OWL.NamedIndividual))
                g.add((justDfUri,RDF.type,ns.JustificacaoDF))
                g.add((dfUri,ns.temJustificacao,justDfUri))

                for crit in classe['df']['justificacao']:

                    critUri = ns[crit['critCodigo']]
                    g.add((critUri,RDF.type,OWL.NamedIndividual))

                    if crit['tipo'] == 'legal':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoLegal))
                    elif crit['tipo'] == 'densidade':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoDensidadeInfo))
                    elif crit['tipo'] == 'complementaridade':
                        g.add((critUri,RDF.type,ns.CriterioJustificacaoComplementaridadeInfo))

                    g.add((critUri,ns.conteudo,Literal(crit['conteudo'])))
                    g.add((justDfUri,ns.temCriterio,critUri))

                    if 'legRefs' in crit:
                        for ref in crit['legRefs']:
                            g.add((critUri,ns.critTemLegAssoc,ns[f"leg_{ref}"]))

                    if 'procRefs' in crit:
                        for ref in crit['procRefs']:
                            g.add((critUri,ns.critTemProcRel,ns[f"c{ref}"]))

    ecatalog.close()
    lcatalog.close()

    g.serialize(format="ttl",destination=os.path.join(ONTOLOGY_DIR,f"{clN1}.ttl"))
    logger.info(f"Geração da ontologia da classe {clN1} terminada")


# --- Geração da ontologia final -----------------------
# ------------------------------------------------------
def genFinalOntology():

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    outputFile = os.path.join(OUTPUT_DIR, f"CLAV_{timestamp}.ttl")
    zipedOutputFile = os.path.join(OUTPUT_DIR, f"CLAV_{timestamp}.zip")

    # Concatenação dos ficheiros intermédios num só
    logger.info("Concatenação dos ficheiros ttl intermédios num só")
    try:
        ontFiles = sorted(glob.glob(os.path.join(ONTOLOGY_DIR, "*.ttl")))
        with open(outputFile, 'w', encoding='utf-8') as outfile:
            for file_path in ontFiles:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')
    except Exception as e:
        logger.error(f"Falha na concatenação da ontologia")
        raise

    # Compressão da ontologia final
    try:
        with zipfile.ZipFile(zipedOutputFile, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(outputFile, os.path.basename(zipedOutputFile))
        logger.info(f"Ontologia comprimida em {zipedOutputFile}")
    except Exception as e:
        logger.error(f"Falha na compressão")
        raise

    return zipedOutputFile
