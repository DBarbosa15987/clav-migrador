import json
import re
from nanoid import generate
from datetime import date
from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, URIRef
from rdflib.namespace import RDF,OWL

ns = Namespace("http://jcr.di.uminho.pt/m51-clav#")
dc = Namespace("http://purl.org/dc/elements/1.1/")
uri_ontologia = URIRef("http://jcr.di.uminho.pt/m51-clav")

agora = date.today()
# YY-mm-dd
dataAtualizacao = agora.strftime("%Y-%m-%d")
# Vou colocar o triplo nos termos de índice

# --- Migra os termos de índice ------------------------
# ------------------------------------------------------
def tiGenTTL():
    fin = open('./files/ti.json')
    termos = json.load(fin)

    g = Graph()
    g.bind("", ns)
    g.bind("dc", dc)
    g.add((uri_ontologia, dc.date, Literal(dataAtualizacao)))
    
    for ti in termos:
        ticod = "ti_" + ti['codigo'] + '_' + generate('abcdef', 6)
        tiUri = ns[ticod]
        g.add((tiUri,RDF.type, OWL.NamedIndividual))
        g.add((tiUri,RDF.type, ns.TermoIndice))
        g.add((tiUri, RDFS.label, Literal(f"TI: {ti['termo']}")))
        g.add((tiUri, ns.estaAssocClasse, ns[f"c{ti['codigo']}"]))
        g.add((tiUri, ns.estado, Literal("Ativo")))
        g.add((tiUri, ns.termo, Literal(ti['termo'])))

    fin.close()
    g.serialize(format="ttl",destination="./ontologia/ti.ttl")


# --- Migra a legislação -------------------------------
# ------------------------------------------------------
def legGenTTL():
    fin = open('./files/leg.json')
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
    g.serialize(format="ttl",destination="./ontologia/leg.ttl")


# --- Migra as tipologias ------------------------------
# ------------------------------------------------------
def tipologiaGenTTL():
    fin = open('./files/tip.json')
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
        else:
            print("AVISO: a tipologia " + sigla + " não tem designação definida.")

    fin.close()
    g.serialize(format="ttl",destination="./ontologia/tip.ttl")


# --- Migra as entidades -------------------------------
# ------------------------------------------------------
def entidadeGenTTL():
    fin = open('./files/ent.json')
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
    g.serialize(format="ttl",destination="./ontologia/ent.ttl")


# --- Migra uma classe ---------------------------------
# ------------------------------------------------------
def classeGenTTL(c):
    fin = open('./files/' + c + '.json')
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
    
    g = Graph()
    g.bind("", ns)

    for classe in classes:
        print(classe['codigo'])
        # codigo, estado, nível e título
        codigoUri = ns[f"c{classe['codigo']}"] 
        g.add((codigoUri,RDF.type, OWL.NamedIndividual))
        g.add((codigoUri,ns.classeStatus, Literal(classe['estado'])))
        g.add((codigoUri,RDF.type, ns[f"Classe_N{classe['nivel']}"]))
        g.add((codigoUri,ns.codigo, Literal(classe['codigo'])))
        g.add((codigoUri,ns.titulo, Literal(classe['titulo'])))
        
        # Relação hierárquica-------------------------------
        if classe['nivel'] == 1:
            g.add((codigoUri,ns.pertenceLC, ns.lc1))
            g.add((codigoUri,ns.temPai, ns.lc1))
        elif classe['nivel'] in [2,3,4]:
            partes = classe['codigo'].split('.')
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

            pcaUri = ns[f"pca_c{classe['codigo']}"]
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

                justUri = ns[f"just_pca_c{classe['codigo']}"]
                g.add((justUri,RDF.type,OWL.NamedIndividual))
                g.add((justUri,RDF.type,ns.JustificacaoPCA))
                g.add((ns[f"pca_c{classe['codigo']}"],ns.temJustificacao,justUri))

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

            dfUri = ns[f"df_c{classe['codigo']}"]

            g.add((codigoUri,ns.temDF,dfUri))
            g.add((dfUri,RDF.type,OWL.NamedIndividual))
            g.add((dfUri,RDF.type,ns.DestinoFinal))
            g.add((dfUri,ns.dfValor,Literal(classe['df']['valor'])))

            if 'nota' in classe['df']:
                g.add((dfUri,ns.dfNota,Literal(classe['df']['nota'])))

        # ------------------------------------------------------------
        # Justificação do DF -----------------------------------------
            if 'justificacao' in classe['df']:

                justDfUri = ns[f"just_df_c{classe['codigo']}"]
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
    
    g.serialize(format="ttl",destination='./ontologia/' + c + '.ttl')
    fin.close()

# Invocação dos migradores 
# ------------------------------------------------------

tiGenTTL()
entidadeGenTTL()
tipologiaGenTTL()
legGenTTL()

classes = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']
for c in classes:
    print('Classe: ', c)
    classeGenTTL(c)