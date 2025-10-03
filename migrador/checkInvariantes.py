import json
import re
from .report import Report
from collections import Counter
import os
from path_utils import FILES_DIR, DUMP_DIR
from log_utils import INV, PROC
import logging

logger = logging.getLogger(INV)
loggerProc = logging.getLogger(PROC)

relsSimetricas = ["eCruzadoCom","eComplementarDe"]
relsInverseOf = {
    "eSinteseDe": "eSintetizadoPor",
    "eSuplementoDe": "eSuplementoPara",
    "eSucessorDe": "eAntecessorDe",
    "eSintetizadoPor": "eSinteseDe",
    "eSuplementoPara": "eSuplementoDe",
    "eAntecessorDe": "eSucessorDe"
}


def processClasses(rep: Report):
    """
    Função que verifica se existem códigos de classe repetidas
    e se todas as classes mencionadas (em relações) existem de facto.
    A função também regista todas as possíveis inferências tendo em
    conta algumas propriedades da futura ontologia.

    No final a função produz um relatório em que contam os erros
    encontrados, warnings e possíveis inferências a aplicar aos dados.
    A função retorna dois dicionários:

    * um dicionário com os dados, que exclui os processos em
    Harmonização que não serão testados pelos invariantes.
    * e outro dicionário com os processos em Harmonização,
    caso precisem de ser consultados
    """

    data = {}
    for sheet in rep.classesN1:
        with open(os.path.join(FILES_DIR,f"{sheet}.json"),'r') as f:
            x = json.load(f)
            data.update(x)

    allClasses = {}
    harmonizacao = {}
    for cod,classe in data.items():

        # Se a classe está em harmonização, ainda pode estar incompleta,
        # por isso não é incluída para verificação de invariantes. Deve
        # ser marcada como warning e adicionada a um dicionário diferente,
        # não para ser testada, mas para ser consultada caso seja referenciada.
        if classe["estado"] == "H":
            rep.addWarning("H",{"proc":cod})
            harmonizacao[cod] = classe
            continue
        elif classe["estado"] in ['A','I']:
            if classe["estado"] == "I":
                rep.addInativo(cod)
            if classe["nivel"] == 3:
                filhos = [c for c,_ in data.items() if c.startswith(cod + ".")]
                classe["filhos"] = filhos
            elif classe["nivel"] == 4:
                # É feita uma verificação sobre as de nível 4 para garantir que
                # o pai de cada uma é válido e está ativo
                pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
                classePai = data.get(pai)
                if not classePai:
                    # Não tem pai
                    rep.addErro(cod,f"<b>{cod}</b> não tem pai")
                elif classePai.get("estado") == 'H':
                    # Tem pai em harmonização
                    rep.addWarning(info={"msg":f"O processo <b>{cod}</b> está ativo/inativo, mas o seu pai <b>{pai}</b> está em harmonização"})

            allClasses[cod] = classe
        else:
            # O valor do estado da classe encontra-se fora do domínio estabelecido.
            # Trata-se de um erro que já foi registado previamente, nestes
            # casos os invariantes não são verificados
            continue


        proRels = classe.get("processosRelacionados")
        rels = classe.get("proRel")
        df = classe.get("df")
        pca = classe.get("pca")

        if proRels and rels:
            for proc,rel in zip(proRels, rels):
                # Se não existir, é registada como inválida, se existir confirma-se
                # se as simetrias e anti-simetrias estão corretas
                # Aqui "inválida" != "harmonização"
                if proc not in data.keys():
                    rep.addRelInvalida(proc,rel,cod)
                # Se a relação mencionar um processo em harmonização fica anotado
                # como warning
                elif data[proc]['estado'] == 'H':
                    rep.addWarning("R",{"rel":(cod,rel,proc)})
                else:
                    classe2 = data[proc]
                    proRels2 = classe2.get("processosRelacionados",[])
                    rels2 = classe2.get("proRel",[])

                    if rel in relsSimetricas:
                        if (cod,rel) not in zip(proRels2,rels2):
                            rep.addMissingRels(proc,rel,cod,"relsSimetricas")
                    elif rel in relsInverseOf.keys():
                        if (cod,relsInverseOf[rel]) not in zip(proRels2,rels2):
                            rep.addMissingRels(proc,relsInverseOf[rel],cod,"relsInverseOf")

        if df:
            justificacao = df.get("justificacao")
            if justificacao:
                for j in justificacao:
                    procRefs = j.get("procRefs")
                    if procRefs:
                        for p in procRefs:
                            if p not in data.keys():
                                rep.addRelInvalida(p,"procRef",cod,"df")
                            # Se a relação mencionar um processo em harmonização fica anotado
                            # como warning
                            elif data[p]['estado'] == 'H':
                                rep.addWarning("R",{"rel":(cod,rel,p)})

        if pca:
            justificacao = pca.get("justificacao")
            if justificacao:
                for j in justificacao:
                    procRefs = j.get("procRefs")
                    if procRefs:
                        for p in procRefs:
                            if p not in data.keys():
                                rep.addRelInvalida(p,"procRef",cod,"pca")
                            # Se a relação mencionar um processo em harmonização fica anotado
                            # como warning
                            elif data[p]['estado'] == 'H':
                                rep.addWarning("R",{"rel":(cod,rel,p)})

    loggerProc.info(f"Foram encontrados {len(harmonizacao)} processos em harmonização")
    loggerProc.info(f"Foram encontradas {len(allClasses)} processos em ativos/inativos")
    with open(os.path.join(DUMP_DIR,f"allClasses.json"),'w') as f:
        json.dump(allClasses,f,ensure_ascii=False,indent=4)

    return allClasses,harmonizacao


def checkAntissimetrico(allClasses,rel,rep: Report,invName):
    """
    Verifica para todas as classes se uma dada
    relação `rel` é antissimétrica.

    Os casos em que tal não acontece são guardados
    em `rep`.
    """

    erros = []
    for cod,classe in allClasses.items():
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            relacoes = [c for c,r in zip(proRelCods,proRels) if r==rel]
            for c in relacoes:
                relacao = allClasses.get(c)

                # Caso a relação em questão mencione um processo em harmonização
                # ou um processo com código inválido, não é feita a verificação
                # do invariante.
                if not relacao:
                    continue

                proRels2 = relacao.get("proRel",[])
                proRelCods2 = relacao.get("processosRelacionados",[])
                if proRelCods2 and proRels2:
                    relacoes2 = [c for c,r in zip(proRelCods2,proRels2) if r==rel]
                    # Se existe a relação `rel` aqui também, não cumpre com o invariante
                    if cod in relacoes2:
                        # Evita-se guardar 2 erros iguais, por exemplo
                        # A :x B e B :x A apontam o mesmo erro
                        if (c,rel,cod) not in erros:
                            erros.append((cod,rel,c))

    for (cod,rel,c) in erros:
        rep.addFalhaInv(invName,cod,{"rel": rel,"c": c})


def checkJustRef(allClasses,nivel,rep: Report,invName):
    """
    Verifica se as classes do `nível` passado por input (3 ou 4)
    referenciam as legislações mencionadas nas justificações de pca e df.

    No caso da classe ser de nível 4 a legislação é mencionada
    apenas na classe pai.

    A função guarda em `rep` todos os casos em que falha.
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == nivel:
            # verificação no pca
            justificacaoPca = classe.get("pca",{}).get("justificacao")
            if justificacaoPca:
                pcaLegRefs = [x["legRefs"] for x in justificacaoPca if x["tipo"]=="legal"]
                # Concatenar lista de listas e remover repetidos
                pcaLegRefs = set(sum(pcaLegRefs,[]))
                for leg in pcaLegRefs:
                    # Se a legislação mencionada no pca não se encontra
                    # na lista de legislação associada à classe,
                    # então não cumpre com o invariante
                    if nivel == 3 and (leg not in classe.get("legislacao",[])):
                        rep.addFalhaInv(invName,cod,{"leg":leg,"tipo": "PCA"})

                    # Se a classe for de nível 4 verifica-se se
                    # a legislação é mencionada no pai
                    elif nivel == 4:
                        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
                        classePai = allClasses.get(pai)
                        # Tem pai ativo
                        if classePai:
                            if leg not in classePai.get("legislacao",[]):
                                rep.addFalhaInv(invName,cod,{"leg":leg,"tipo": "PCA", "pai": pai})

            # verificação no df
            justificacaoDf = classe.get("df",{}).get("justificacao")
            if justificacaoDf:
                dfLegRefs = [x["legRefs"] for x in justificacaoDf if x["tipo"]=="legal"]
                # Concatenar lista de listas e remover repetidos
                dfLegRefs = set(sum(dfLegRefs,[]))
                for leg in dfLegRefs:
                    # Se a legislação mencionada no df não se encontra
                    # na lista de legislação associada à classe,
                    # então não cumpre com o invariante
                    if nivel == 3 and (leg not in classe.get("legislacao",[])):
                        rep.addFalhaInv(invName,cod,{"leg":leg,"tipo": "DF"})

                    # Se a classe for de nível 4 verifica-se se
                    # a legislação é mencionada no pai
                    if nivel == 4:
                        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
                        classePai = allClasses.get(pai)
                        # Tem pai ativo
                        if classePai:
                            if leg not in classePai.get("legislacao",[]):
                                rep.addFalhaInv(invName,cod,{"leg":leg,"tipo": "DF", "pai": pai})


def rel_2_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA"
    """

    logger.info("Verificação do invariante rel_2_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                pca = classe.get("pca")
                just = pca.get("justificacao")
                if not just:
                    rep.addFalhaInv("rel_2_inv_1",cod)
                elif not pca:
                    rep.addFalhaInv("rel_2_inv_1",cod,extra="Neste caso nem tem PCA")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_1")


def rel_2_inv_4(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação <b>eSintetizadoPor</b> é antissimétrica"
    """

    logger.info("Verificação do invariante rel_2_inv_4")

    checkAntissimetrico(allClasses,"eSintetizadoPor",rep,"rel_2_inv_4")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_4",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_4")


def rel_2_inv_5(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação <b>eSucessorDe</b> é antissimétrica"
    """

    logger.info("Verificação do invariante rel_2_inv_5")

    checkAntissimetrico(allClasses,"eSucessorDe",rep,"rel_2_inv_5")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_5",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_5")


def rel_2_inv_11(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um PN não pode ter em simultâneo relações de
    <b>éSínteseDe</b> e <b>éSintetizadoPor</b> com outros PNs"
    """

    logger.info("Verificação do invariante rel_2_inv_11")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRels = classe.get("proRel")
            proRelCods = classe.get("processosRelacionados")
            # Se a classe contém ambas as relações, não cumpre com o invariante
            if proRels and proRelCods:
                if "eSinteseDe" in proRels and "eSintetizadoPor" in proRels:
                    sinteses = [(c,r) for (c,r) in zip(proRelCods,proRels) if r in ["eSinteseDe","eSintetizadoPor"]]
                    rep.addFalhaInv("rel_2_inv_11",cod,{"sinteses":sinteses})

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_11",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_11")


def rel_2_inv_12(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um diploma legislativo referenciado num critério de
    justificação tem de estar associado na zona de contexto
    do processo que tem essa justificação (Classes de nível 3)"
    """

    logger.info("Verificação do invariante rel_2_inv_12")

    checkJustRef(allClasses,3,rep,"rel_2_inv_12")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_12",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_12")


def rel_2_inv_13(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um diploma legislativo referenciado num critério de
    justificação tem de estar associado na zona de contexto do
    processo que tem essa justificação (Classes de nível 4)"
    """

    logger.info("Verificação do invariante rel_2_inv_13")

    checkJustRef(allClasses,4,rep,"rel_2_inv_13")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_13",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_13")


def rel_2_inv_6(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação <b>eSuplementoDe</b> é antissimétrica"
    """

    logger.info("Verificação do invariante rel_2_inv_6")

    checkAntissimetrico(allClasses,"eSuplementoDe",rep,"rel_2_inv_6")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_6",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_6")


def rel_2_inv_7(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação <b>eSuplementoPara</b> é antissimétrica"
    """

    logger.info("Verificação do invariante rel_2_inv_7")

    checkAntissimetrico(allClasses,"eSuplementoPara",rep,"rel_2_inv_7")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_7",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_7")


def rel_2_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação <b>eSinteseDe</b> é antissimétrica"
    """

    logger.info("Verificação do invariante rel_2_inv_3")

    checkAntissimetrico(allClasses,"eSinteseDe",rep,"rel_2_inv_3")

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_3",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_3")


def rel_1_inv_5(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "As relações temDF e temPCA, existem numa classe 3
    se esta não tiver filhos"
    """

    logger.info("Verificação do invariante rel_1_inv_5")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                temPca = bool(classe.get("pca"))
                temDf = bool(classe.get("df"))
                if not temPca or not temDf:
                    rep.addFalhaInv("rel_1_inv_5",cod,{"temPca":temPca,"temDf":temDf})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_5",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_5")


def rel_1_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando os filhos resultantes de um desdobramento de
    um PN têm o DF distinto, deve haver uma relação de
    síntese (de ou por) entre eles"
    """

    logger.info("Verificação do invariante rel_1_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos",[])
            # Assume-se aqui que se tiver filhos, tem 2
            if len(codFilhos) == 2:
                codF1 = codFilhos[0]
                codF2 = codFilhos[1]
                f1 = allClasses.get(codF1)
                f2 = allClasses.get(codF2)
                df1 = f1.get("df",{}).get("valor")
                df2 = f2.get("df",{}).get("valor")

                # Aqui só interessam os que têm DFs distintos
                if df1 and df2 and df1 != df2:
                    f1Rels = f1.get("proRel")
                    f1RelCods = f1.get("processosRelacionados")

                    # A relação de "eSinteseDe" é inversa de "eSintetizadoPor",
                    # e são feitas inferências iniciais que tornam este tipo de
                    # situações explícitas, por isso basta verificar do processo
                    # A para B, e verificar B para A torna-se redundante.
                    if f1Rels and f1RelCods:
                        relacoesF1 = zip(f1Rels,f1RelCods)
                        if ("eSinteseDe",codF2) not in relacoesF1 or ("eSintetizadoPor",codF2) not in relacoesF1:
                            rep.addFalhaInv("rel_1_inv_2",cod,{"codF1":codF1,"codF2":codF2})
                    else:
                        # Se algum não tem relações então já está mal
                        rep.addFalhaInv("rel_1_inv_2",cod,{"codF1":codF1,"codF2":codF2})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_2")


def rel_3_inv_1(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é <b>eSuplementoPara</b> outro,
    deve ser acrescentado um <b>critério de utilidade
    administrativa</b> na justificação do respetivo PCA"
    """

    logger.info("Verificação do invariante rel_3_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                proRel = classe.get("proRel")
                if proRel and "eSuplementoPara" in proRel:
                    pca = classe.get("pca",{})
                    just = pca.get("justificacao")
                    if just:
                        justUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                        if not justUtilidade:
                            rep.addFalhaInv("rel_3_inv_1",cod)
                    elif pca:
                        rep.addFalhaInv("rel_3_inv_1",cod,extra="Neste caso nem tem justificação do PCA")
                    else:
                        rep.addFalhaInv("rel_3_inv_1",cod,extra="Neste caso nem tem PCA")

    err = len(rep.globalErrors["erroInv"].get("rel_3_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_3_inv_1")


def rel_3_inv_2(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "No <b>critério de utilidade administrativa</b> devem aparecer
    todos os processos com os quais existe uma relação de
    <b>eSuplementoPara</b>"
    """

    logger.info("Verificação do invariante rel_3_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRel = classe.get("proRel")
                proRelCods = classe.get("processosRelacionados")
                if proRel and "eSuplementoPara" in proRel:
                    supls = [c for r,c in zip(proRel,proRelCods) if r=="eSuplementoPara"]
                    pca = classe.get("pca",{})
                    just = pca.get("justificacao")
                    if just:
                        jUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                        allProcRefs = []
                        for crit in jUtilidade:
                            allProcRefs += crit.get("procRefs",[])

                        for s in supls:
                            if s not in allProcRefs:
                                rep.addFalhaInv("rel_3_inv_2",cod,{"proc":s})
                    else:
                        extra = ""
                        if pca:
                            extra = "Neste caso nem tem justificação do PCA"
                        else:
                            extra = "Neste caso nem tem PCA"

                        # Aqui como nem tem justificação/pca, não tem nenhum procRef,
                        # por isso todos os supls estão em falta
                        for s in supls:
                            rep.addFalhaInv("rel_3_inv_2",cod,{"proc":s},extra=extra)

    err = len(rep.globalErrors["erroInv"].get("rel_3_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_3_inv_2")


def rel_5_inv_1(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é <b>complementar de</b> outro,
    a justificação do DF deverá conter o <b>critério de
    complementaridade informacional</b>"
    """

    logger.info("Verificação do invariante rel_5_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eComplementarDe" in proRel:
                df = classe.get("df",{})
                just = df.get("justificacao")
                if just:
                    justComplementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    if not justComplementaridade:
                        rep.addFalhaInv("rel_5_inv_1",cod)
                elif df:
                    rep.addFalhaInv("rel_5_inv_1",cod,extra="Neste caso nem tem justificação no DF")
                else:
                    rep.addFalhaInv("rel_5_inv_1",cod,extra="Neste caso nem tem DF")

    err = len(rep.globalErrors["erroInv"].get("rel_5_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_5_inv_1")


def rel_4_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é <b>síntetizado por</b>
    outro, o DF deve ter o valor de \"Eliminação\""
    """

    logger.info("Verificação do invariante rel_4_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eSintetizadoPor" in proRel:
                filhos = classe.get("filhos")
                if not filhos:
                    if "eSinteseDe" not in proRel and "eComplementarDe" not in proRel:
                        df = classe.get("df",{})
                        valor = df.get("valor")
                        if valor != 'E':
                            rep.addFalhaInv("rel_4_inv_1",cod,{"valor":valor})

    err = len(rep.globalErrors["erroInv"].get("rel_4_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_4_inv_1")


def rel_3_inv_3(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é <b>suplemento de</b> outro,
    todos os processos relacionados pela relação
    <b>eSuplementoDe</b> devem constar na justificação do PCA"
    """

    logger.info("Verificação do invariante rel_3_inv_3")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRel = classe.get("proRel")
                proRelCods = classe.get("processosRelacionados")
                if proRel and proRelCods and "eSuplementoDe" in proRel:
                    pca = classe.get("pca",{})
                    just = pca.get("justificacao",[])
                    supl = [cod for rel,cod in zip(proRel,proRelCods) if rel=="eSuplementoDe"]
                    if just:
                        allProcRefs = []
                        for j in just:
                            procRefs = j.get("procRefs",[])
                            allProcRefs+=procRefs

                        for sup in supl:
                            if sup not in allProcRefs:
                                if sup in allClasses:
                                    rep.addFalhaInv("rel_3_inv_3",cod,{"proc":sup})
                    else:
                        extra = ""
                        if pca:
                            extra = "Neste caso nem tem justificação do PCA"
                        else:
                            extra = "Neste caso nem tem PCA"

                        # Aqui como nem tem justificação/pca, não tem nenhum procRef,
                        # por isso todos os sups estão em falta
                        for sup in supl:
                            if sup in allClasses:
                                rep.addFalhaInv("rel_3_inv_3",cod,{"proc":sup},extra=extra)

    err = len(rep.globalErrors["erroInv"].get("rel_3_inv_3",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_3_inv_3")


def rel_8_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN é <b><i>eSinteseDe</i></b, então
    o valor do DF é de \"Conservação\""
    """

    logger.info("Verificação do invariante rel_8_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            filhos = classe.get("filhos")
            if not filhos:
                proRel = classe.get("proRel")
                if proRel and "eSinteseDe" in proRel:
                    df = classe.get("df",{})
                    valor = df.get("valor")
                    if valor != "C":
                        rep.addFalhaInv("rel_8_inv_2",cod,{"valor":valor})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_2")


def rel_1_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Os PNs só podem ter desbobramento ao nível 4
    quando os descendentes de nível 4 têm valores
    de PCA ou DF distintos entre eles"
    """

    logger.info("Verificação do invariante rel_1_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if codFilhos:
                filhos = [(c,allClasses.get(c)) for c in codFilhos]
                valoresCounter = {} # {(pca,df):["100","200"]}
                for c,f in filhos:
                    valores = (f.get("pca",{}).get("valores"),f.get("df",{}).get("valor"))
                    if valores in valoresCounter:
                        valoresCounter[valores].append(c)
                    else:
                        valoresCounter[valores] = [c]

                for valor,cods in valoresCounter.items():
                    # Quando uma combinação de valores de pca e df se repete,
                    # o invariante falha. É registado o valor em questão e
                    # os sítios onde acontece
                    if len(cods) > 1:
                        rep.addFalhaInv("rel_1_inv_1",cod,{"filhos": cods})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_1")


def rel_1_inv_4(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Uma classe de nível 3 não pode ter valores de
    DF e PCA se esta tiver desdobramento no nível 4"
    """

    logger.info("Verificação do invariante rel_1_inv_4")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if classe.get("filhos"):
                temPca = bool(classe.get("pca"))
                temDf = bool(classe.get("df"))
                if (temDf or temPca):
                    rep.addFalhaInv("rel_1_inv_4",cod,{"temPca":temPca,"temDf":temDf})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_4",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_4")


def rel_1_inv_6(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN (Classe 3) for <b>complementar de</b> outro
    que se desdobra ao 4º nível, é necessário, com base no
    <b>critério de complementaridade informacional</b>,
    a relação manter-se ao 3º nível.
    Pelo menos um dos 4ºs níveis deve ser de conservação"
    """

    logger.info("Verificação do invariante rel_1_inv_6")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRels = classe.get("proRel")
            proRelCods = classe.get("processosRelacionados")
            if proRels and proRelCods and "eComplementarDe" in proRels:
                compls = [c for c,r in zip(proRelCods,proRels) if r=="eComplementarDe"]
                for compl in compls:
                    codFilhos = allClasses.get(compl,{}).get("filhos",[])
                    filhos = [allClasses.get(c) for c in codFilhos]
                    if filhos:
                        conservacao = False
                        for filho in filhos:
                            valor = filho.get("df",{}).get("valor")
                            if valor == "C":
                                conservacao = True
                                break
                        # Se nenhum filho tiver o valor de "C",
                        # então o invariante falha
                        if not conservacao:
                            rep.addFalhaInv("rel_1_inv_6",cod,{"proc": compl,"filhos": codFilhos})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_6",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_6")


def rel_1_inv_3(allClasses,termosIndice,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando há desdobramento em 4ºs níveis, os termos
    de índice são replicados em cada um desses níveis"
    """

    logger.info("Verificação do invariante rel_1_inv_3")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if codFilhos:
                termosPai = [t["termo"] for t in termosIndice if t["codigo"]==cod]
                for c in codFilhos:
                    termosFilho = [t["termo"] for t in termosIndice if t["codigo"]==c]
                    for t in termosPai:
                        if t not in termosFilho:
                            rep.addFalhaInv("rel_1_inv_3",cod,{"termo":t,"filho" :c})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_3",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_3")


def rel_4_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN tem uma relação de <b>síntese</b>,
    o seu DF deverá ter uma justificação onde consta
    um <b>critério de densidade informacional</b>"
    """

    logger.info("Verificação do invariante rel_4_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRels = classe.get("proRel")
                if proRels and ("eSinteseDe" in proRels or "eSintetizadoPor" in proRels):
                    df = classe.get("df",{})
                    just = df.get("justificacao")
                    if just:
                        justDensidade = [x for x in just if x["tipo"]=="densidade"]
                        if not justDensidade:
                            rep.addFalhaInv("rel_4_inv_2",cod)
                    elif df:
                        rep.addFalhaInv("rel_4_inv_2",cod,extra="Neste caso nem tem justificação do DF")
                    else:
                        rep.addFalhaInv("rel_4_inv_2",cod,extra="Neste caso nem tem DF")

    err = len(rep.globalErrors["erroInv"].get("rel_4_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_4_inv_2")


def rel_4_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos relacionados por uma relação de
    <b>síntese</b> deverão estar relacionados com o
    <b>critério de densidade informacional</b> da
    respetiva justificação"
    """

    logger.info("Verificação do invariante rel_4_inv_3")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRelCods = classe.get("processosRelacionados")
                proRels = classe.get("proRel")
                if proRels and ("eSinteseDe" in proRels or "eSintetizadoPor" in proRels):
                    valor = classe.get("df",{}).get("valor")
                    # Só faz sentido fazer esta verificação em processos
                    # com o DF de "Eliminação"
                    if valor != "C":
                        df = classe.get("df",{})
                        just = df.get("justificacao")
                        sints = [(c,r) for c,r in zip(proRelCods,proRels) if r in ["eSinteseDe","eSintetizadoPor"]]
                        if just:
                            jDensidade = [x for x in just if x["tipo"]=="densidade"]
                            allProcRefs = []
                            for crit in jDensidade:
                                allProcRefs += crit.get("procRefs",[])

                            for c,r in sints:
                                if c not in allProcRefs:
                                    rep.addFalhaInv("rel_4_inv_3",cod,{"proc": c, "rel": r})
                        else:
                            extra = ""
                            if df:
                                extra = "Neste caso nem tem justificação do DF"
                            else:
                                extra = "Neste caso nem tem DF"

                            # Aqui como nem tem justificação, não tem nenhum procRef,
                            # por isso estão todos em falta
                            for c,r in sints:
                                rep.addFalhaInv("rel_4_inv_3",cod,{"proc": c, "rel": r},extra=extra)

    err = len(rep.globalErrors["erroInv"].get("rel_4_inv_3",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_4_inv_3")


def rel_5_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos relacionados pela relação
    <b>eComplementarDe</b>, devem estar relacionados
    com o <b>critério de complementaridade informacional</b>
    da respetiva justificação"
    """

    logger.info("Verificação do invariante rel_5_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRelCods = classe.get("processosRelacionados")
            proRels = classe.get("proRel")
            if proRels and "eComplementarDe" in proRels:
                df = classe.get("df",{})
                just = df.get("justificacao")
                compls = [c for c,r in zip(proRelCods,proRels) if r=="eComplementarDe"]
                if just:
                    jComlpementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    allProcRefs = []
                    for crit in jComlpementaridade:
                        allProcRefs += crit.get("procRefs",[])

                    for c in compls:
                        if c not in allProcRefs:
                            rep.addFalhaInv("rel_5_inv_2",cod,{"proc":c})
                else:
                    extra = ""
                    if df:
                        extra = "Neste caso nem tem justificação do DF"
                    else:
                        extra = "Neste caso nem tem DF"

                    # Aqui como nem tem justificação, não tem nenhum procRef,
                    # por isso estão todos em falta
                    for c in compls:
                        rep.addFalhaInv("rel_5_inv_2",cod,{"proc":c},extra=extra)

    err = len(rep.globalErrors["erroInv"].get("rel_5_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_5_inv_2")


def rel_8_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN é <b><i>eComplementarDe</i></b>,
    então o valor do DF é de \"Conservação\""
    """

    logger.info("Verificação do invariante rel_8_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRels = classe.get("proRel")
                if proRels and "eComplementarDe" in proRels:
                    df = classe.get("df",{})
                    valor = df.get("valor")
                    if valor != "C":
                        rep.addFalhaInv("rel_8_inv_1",cod,{"valor":valor})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_1")


def rel_2_inv_9(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um PN só pode ter uma relação com outro PN"
    """

    logger.info("Verificação do invariante rel_2_inv_9")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRelCods = classe.get("processosRelacionados")
            proRels = classe.get("proRel")
            if proRelCods and proRels:
                proRelsCount = Counter(proRelCods)
                rels = list(zip(proRelCods,proRels))
                for x,count in proRelsCount.items():
                    if count > 1:
                        relsDuplicadas = [(c,r) for c,r in rels if c == x]
                        rep.addFalhaInv("rel_2_inv_9",cod,{"proc":x,"rels":relsDuplicadas})

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_9",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_9")


def rel_2_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um processo não transversal não pode ter participantes"
    """

    logger.info("Verificação do invariante rel_2_inv_2")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            procTrans = classe.get("procTrans")
            if procTrans == "N":
                participantes = classe.get("participantes")
                if participantes:
                    rep.addFalhaInv("rel_2_inv_2",cod)

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_2",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_2")


def rel_2_inv_10(termosIndice,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Os termos de índice de um PN não existem em mais
    nenhuma classe 3"
    """

    logger.info("Verificação do invariante rel_2_inv_10")

    n3 = re.compile(r'^\d{3}\.\d{1,3}\.\d{1,3}$')
    termos = {} # {termo:[100,200]}
    for t in termosIndice:
        cod = t["codigo"]
        termo = t["termo"]
        if n3.fullmatch(cod):
            if termo in termos:
                termos[termo].add(cod)
            else:
                termos[termo] = set([cod])

    for t,cods in termos.items():
        if len(cods) > 1:
            for c in cods:
                rep.addFalhaInv("rel_2_inv_10",c,{"t":t,"cods": cods})

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_10",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_10")


def rel_2_inv_8(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um PN não se pode relacionar com ele próprio"
    """

    logger.info("Verificação do invariante rel_2_inv_8")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRelCods = classe.get("processosRelacionados")
            proRels = classe.get("proRel")
            if proRelCods:
                # Identificar os todos os casos em que o processo
                # se menciona a si próprio
                selfRels = [r for c,r in zip(proRelCods,proRels) if cod==c]
                for r in selfRels:
                    rep.addFalhaInv("rel_2_inv_8",cod,{"rel":r})

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_8",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_8")


def rel_2_inv_14(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um processo transversal tem que ter participantes"
    """

    logger.info("Verificação do invariante rel_2_inv_14")

    for cod,classe in allClasses.items():
        if classe['nivel'] == 3:
            procTrans = classe.get("procTrans")
            if procTrans == "S":
                participantes = classe.get("participantes")
                if not participantes:
                    rep.addFalhaInv("rel_2_inv_14",cod)

    err = len(rep.globalErrors["erroInv"].get("rel_2_inv_14",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_2_inv_14")


def rel_1_inv_7(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Os PNs em harmonização não podem ter filhos ativos"
    """

    logger.info("Verificação do invariante rel_1_inv_7")

    # Como em `allClasses` apenas existem processos ativos,
    # a verificação é feita dos filhos para os pais.
    for cod,classe in allClasses.items():
        if classe["nivel"] == 4:
            pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
            if pai in harmonizacao:
                rep.addFalhaInv("rel_1_inv_7",cod,{"pai":pai})

    err = len(rep.globalErrors["erroInv"].get("rel_1_inv_7",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_1_inv_7")


def rel_8_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Qualquer processo referenciado num critério da
    justificação do PCA/DF tem de estar declarado na
    zona de contexto"
    """

    logger.info("Verificação do invariante rel_8_inv_3")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            filhos = classe.get("filhos")
            if not filhos:
                proRelCods = classe.get("processosRelacionados",[])

                justPca = classe.get("pca",{}).get("justificacao")
                if justPca:
                    for crit in justPca:
                        procRefs = crit.get("procRefs",[])
                        for p in procRefs:
                            if p not in proRelCods:
                                rep.addFalhaInv("rel_8_inv_3",cod,{"proc":p,"tipo":"PCA"})

                justDf = classe.get("df",{}).get("justificacao")
                if justDf:
                    for crit in justDf:
                        procRefs = crit.get("procRefs",[])
                        for p in procRefs:
                            if p not in proRelCods:
                                rep.addFalhaInv("rel_8_inv_3",cod,{"proc":p,"tipo":"DF"})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_3",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_3")


def rel_8_inv_4(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos referenciados no <b>critério
    de densidade informacional</b> devem estar declarado
    na zona de contexto com a relação <b><i>eSinteseDe</i></b>
    ou <b><i>eSintetizadoPor</i></b>"
    """

    logger.info("Verificação do invariante rel_8_inv_4")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            filhos = classe.get("filhos")
            if not filhos:
                just = classe.get("df",{}).get("justificacao")
                if just:
                    jDensidade = [x for x in just if x["tipo"]=="densidade"]
                    proRels = classe.get("proRel",[])
                    proRelCods = classe.get("processosRelacionados",[])
                    sints = [c for c,r in zip(proRelCods,proRels) if r in ["eSinteseDe","eSintetizadoPor"]]
                    for crit in jDensidade:
                        procRefs = crit.get("procRefs",[])
                        for p in procRefs:
                            if p not in sints:
                                rep.addFalhaInv("rel_8_inv_4",cod,{"proc":p})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_4",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_4")


def rel_8_inv_5(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos referenciados no <b>critério
    de complementaridade informacional</b> devem estar
    declarado na zona de contexto com a relação
    <b><i>eComplementarDe</i></b>"
    """

    logger.info("Verificação do invariante rel_8_inv_5")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            filhos = classe.get("filhos")
            if not filhos:
                just = classe.get("df",{}).get("justificacao")
                if just:
                    jComlpementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    proRels = classe.get("proRel",[])
                    proRelCods = classe.get("processosRelacionados",[])
                    compls = [c for c,r in zip(proRelCods,proRels) if r=="eComplementarDe"]
                    for crit in jComlpementaridade:
                        procRefs = crit.get("procRefs",[])
                        for p in procRefs:
                            if p not in compls:
                                rep.addFalhaInv("rel_8_inv_5",cod,{"proc":p})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_5",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_5")


def rel_8_inv_6(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos referenciados no <b>critério
    de utilidade administrativa</b> devem estar
    declarado na zona de contexto com a relação
    <b><i>eSuplementoPara</i></b>"
    """

    logger.info("Verificação do invariante rel_8_inv_6")

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            filhos = classe.get("filhos")
            if not filhos:
                just = classe.get("pca",{}).get("justificacao")
                if just:
                    jUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                    proRels = classe.get("proRel",[])
                    proRelCods = classe.get("processosRelacionados",[])
                    supls = [c for r,c in zip(proRels,proRelCods) if r=="eSuplementoPara"]
                    for crit in jUtilidade:
                        procRefs = crit.get("procRefs",[])
                        for p in procRefs:
                            if p not in supls:
                                rep.addFalhaInv("rel_8_inv_6",cod,{"proc":p})

    err = len(rep.globalErrors["erroInv"].get("rel_8_inv_6",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_8_inv_6")


def rel_7_inv_1(allClasses, rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A justificação de um PCA só pode conter um
    critério de cada tipo"
    """

    logger.info("Verificação do invariante rel_7_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] in [3,4]:
            just = classe.get("pca",{}).get("justificacao")
            if just:
                tiposSet = set()
                tipos = [x["tipo"] for x in just if "tipo" in x]
                for t in tipos:
                    if t in tiposSet:
                        rep.addFalhaInv("rel_7_inv_1",cod,{"tipo":t})
                    else:
                        tiposSet.add(t)

    err = len(rep.globalErrors["erroInv"].get("rel_7_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_7_inv_1")


def rel_6_inv_1(allClasses, rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A justificação de um DF só pode conter um
    critério de cada tipo"
    """

    logger.info("Verificação do invariante rel_6_inv_1")

    for cod,classe in allClasses.items():
        if classe["nivel"] in [3,4]:
            just = classe.get("df",{}).get("justificacao")
            if just:
                tiposSet = set()
                tipos = [x["tipo"] for x in just if "tipo" in x]
                for t in tipos:
                    if t in tiposSet:
                        rep.addFalhaInv("rel_6_inv_1",cod,{"tipo":t})
                    else:
                        tiposSet.add(t)

    err = len(rep.globalErrors["erroInv"].get("rel_6_inv_1",[]))
    logger.info(f"Foram encontradas {err} falhas no invariante rel_6_inv_1")
