import json
import time
import re
from report import Report
from collections import Counter
from itertools import zip_longest

sheets = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']

relsSimetricas = ["eCruzadoCom","eComplementarDe"]
relsInverseOf = {
    "eSinteseDe":"eSintetizadoPor",
    "eSuplementoDe":"eSuplementoPara",
    "eSucessorDe":"eAntecessorDe",
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
    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
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
            rep.addWarning("H",cod)
            harmonizacao[cod] = classe
            continue
        else:
            allClasses[cod] = classe
            if classe["nivel"] == 3:
                filhos = [c for c,_ in data.items() if c.startswith(cod + ".")]
                classe["filhos"] = filhos

        proRels = classe.get("processosRelacionados")
        rels = classe.get("proRel")
        df = classe.get("df")
        pca = classe.get("pca")

        if proRels:
            for proc,rel in zip(proRels, rels):
                # Se não existir, é registada como inválida, se existir confirma-se
                # se as simetrias e anti-simetrias estão corretas
                # Aqui "inválida" != "harmonização"
                if proc not in data.keys():
                    rep.addRelInvalida(proc,rel,cod)
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

        if pca:
            justificacao = pca.get("justificacao")
            if justificacao:
                for j in justificacao:
                    procRefs = j.get("procRefs")
                    if procRefs:
                        for p in procRefs:
                            if p not in data.keys():
                                rep.addRelInvalida(p,"procRef",cod,"pca")

    return allClasses,harmonizacao


def rel_4_inv_0(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            # Se não tem filhos tem de ter uma justificação associada ao PCA
            if not classe.get("filhos"):
                if classe.get("pca"):
                    if not classe["pca"].get("justificacao"):
                        rep.addFalhaInv("rel_4_inv_0",cod)
                else:
                    rep.addFalhaInv("rel_4_inv_0",cod)


def checkAntissimetrico(allClasses,harmonizacao,rel,rep: Report,invName):
    """
    Verifica para todas as classes se uma dada
    relação `rel` é antisimétrica.

    Os casos em que tal não acontece são guardados
    em `rep`.
    """

    for cod,classe in allClasses.items():
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            relacoes = [c for c,r in zip(proRelCods,proRels) if r==rel]
            for c in relacoes:
                relacao = allClasses.get(c)

                # Caso seja com um processo em harmonização
                if not relacao:
                    relacao = harmonizacao.get(c)
                    # FIXME: caso de quando uma relação é inválida, isto é
                    # temporário visto que no futuro o migrador não deixa 
                    # passar relações inválidas
                    if not relacao:
                        print("-"*15)
                        print(cod)
                        print(rel)
                        print(c)
                        print("-"*15)
                    continue

                proRels2 = relacao.get("proRel",[])
                proRelCods2 = relacao.get("processosRelacionados",[])
                if proRelCods2 and proRels2:
                    # É preciso acomodar os processos em harmonização com
                    # `zip_longest`, visto que não é garantido que proRels2
                    # e proRelCods2 tenham a mesma cardinalidade
                    relacoes2 = [c for c,r in zip_longest(proRelCods2,proRels2) if r==rel]
                    # Se existe a relação `rel` aqui também, não cumpre com o invariante
                    if cod in relacoes2:
                        rep.addFalhaInv(invName,cod,rel,c)


def checkJustRef(allClasses,nivel,rep: Report,invName):
    """
    Verifica se as classes do `nível` passado por input (3 ou 4)
    referenciam as legislações mencionadas nas justificações de pca e df.

    No caso da classe ser de nível 4 a legislação é mencionada
    apenas na classe pai.

    Retorna a lista das classes em que isto não se verifica.
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == nivel:
            # verificação no pca
            if "pca" in classe:
                justificacaoPca = classe["pca"].get("justificacao")
                if justificacaoPca:
                    pcaLegRefs = [x["legRefs"] for x in justificacaoPca if x["tipo"]=="legal"]
                    # Concatenar lista de listas e remover repetidos
                    pcaLegRefs = set(sum(pcaLegRefs,[]))
                    for leg in pcaLegRefs:
                        # Se a legislação mencionada no pca não se encontra
                        # na lista de legislação associada à classe,
                        # então não cumpre com o invariante
                        if nivel == 3 and ("legislacao" not in classe or leg not in classe["legislacao"]):
                            # TODO: dar mais detalhe sobre o erro
                            rep.addFalhaInv(invName,cod)

                        # Se a classe for de nível 4 verifica-se se
                        # a legislação é mencionada no pai
                        elif nivel == 4:
                            pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
                            classePai = allClasses.get(pai)
                            if classePai:
                                # TODO: dar mais detalhe sobre o erro
                                if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                    rep.addFalhaInv(invName,cod)
                            else:
                                # FIXME: erro se não houver pai
                                print(f"{cod} não tem pai ({pai})")
                                pass

            # verificação no df
            if "df" in classe:
                justificacaoDf = classe["df"].get("justificacao")
                if justificacaoDf:
                    dfLegRefs = [x["legRefs"] for x in justificacaoDf if x["tipo"]=="legal"]
                    # Concatenar lista de listas e remover repetidos
                    dfLegRefs = set(sum(dfLegRefs,[]))
                    for leg in dfLegRefs:
                        # Se a legislação mencionada no df não se encontra
                        # na lista de legislação associada à classe,
                        # então não cumpre com o invariante
                        if nivel == 3 and ("legislacao" not in classe or leg not in classe["legislacao"]):
                            # TODO: dar mais detalhe sobre o erro
                            rep.addFalhaInv(invName,cod)

                        # Se a classe for de nível 4 verifica-se se
                        # a legislação é mencionada no pai
                        if nivel == 4:
                            pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', cod).group(1)
                            classePai = allClasses.get(pai)
                            if classePai:
                                if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                    rep.addFalhaInv(invName,cod)
                            else:
                                # FIXME: erro se não houver pai
                                print(f"{cod} não tem pai ({pai})")
                                pass


def checkUniqueInst(rep: Report):
    """
    Função que verifica a unicidade das instâncias
    mencionadas nos seguintes invariantes:

    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância NotaAplicacao;
    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância NotaExclusao;
    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância ExemploNotaAplicacao;
    """

    notas = {
        "rel_2_inv_1": {}, # ex: {"nota_200.30.301_df9148e99f28": ["200.30.301","100"] }
        "rel_2_inv_2": {}, # ex: {"exemplo_200.30.301_bdd4fbd33603": ["200.30.301","100"] }
        "rel_2_inv_3": {}, # ex: {"nota_200.30.301_4f1104c7755b": ["200.30.301","100"] }
    }

    corr = [
        ("notasAp","idNota","rel_2_inv_1"),
        ("exemplosNotasAp","idExemplo","rel_2_inv_2"),
        ("notasEx","idNota","rel_2_inv_3")
    ]

    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
            data = json.load(f)
            for cod,classe in data.items():
                if classe["nivel"] in [1,2,3]:
                    for nota,idNota,invName in corr:
                        if classe.get(nota):
                            for n in classe[nota]:
                                if n[idNota] in notas[invName]:
                                    notas[invName][n[idNota]].append(cod)
                                else:
                                    notas[invName][n[idNota]] = [cod]

    for inv,nota in notas.items():
        for id,cods in nota.items():
            # TODO: mais detalhe no erro
            if len(cods) > 1:
                rep.addFalhaInv(inv,id)


def rel_4_inv_3(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação eSintetizadoPor é antisimétrica."
    """

    return checkAntissimetrico(allClasses,harmonizacao,"eSintetizadoPor",rep,"rel_4_inv_3")


def rel_4_inv_4(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação eSucessorDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,harmonizacao,"eSucessorDe",rep,"rel_4_inv_4")


def rel_4_inv_11(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um PN não pode ter em simultâneo relações de
    'éSínteseDe' e 'éSintetizadoPor' com outros PNs"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            # TODO: saber aqui quais é que "quebram o inv"
            proRels = classe.get("proRel")
            # proRelCods = classe.get("processosRelacionados")
            # Se a classe contém ambas as relações, não cumpre com o invariante
            if proRels and "eSinteseDe" in proRels and "eSintetizadoPor" in proRels:
                rep.addFalhaInv("rel_4_inv_11",cod)


def rel_4_inv_12(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto
    do processo que tem essa justificação (Classes de nível 3)"
    """

    return checkJustRef(allClasses,3,rep,"rel_4_inv_12")


def rel_4_inv_13(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto do
    processo que tem essa justificação (Classes de nível 4)"
    """

    return checkJustRef(allClasses,4,rep,"rel_4_inv_13")


def rel_4_inv_5(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação eSuplementoDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,harmonizacao,"eSuplementoDe",rep,"rel_4_inv_5")


def rel_4_inv_6(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação eSuplementoPara é antisimétrica."
    """

    return checkAntissimetrico(allClasses,harmonizacao,"eSuplementoPara",rep,"rel_4_inv_6")


def rel_4_inv_2(allClasses,harmonizacao,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "A relação eSinteseDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,harmonizacao,"eSinteseDe",rep,"rel_4_inv_2")


def rel_3_inv_6(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "As relações temDF e temPCA, existem numa classe 3
    se esta não tiver filhos"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                pca = classe.get("pca")
                df = classe.get("df")
                # TODO: especificar melhor os erros aqui
                if not pca or not df:
                    rep.addFalhaInv("rel_3_inv_6",cod)


def rel_3_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "DF distinto: Deve haver uma relação de sintese (de ou por)
    entre as classes 4 filhas."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            # Assume-se aqui que se tiver filhos, tem 2
            if codFilhos:
                codF1 = codFilhos[0]
                codF2 = codFilhos[1]
                f1 = allClasses.get(codF1)
                f2 = allClasses.get(codF2)
                df1 = f1.get("df",{}).get("valor")
                df2 = f2.get("df",{}).get("valor")

                # Aqui só interessam os que têm DFs distintos
                if df1 and df2 and df1 != df2:
                    # TODO: Especificar melhor o erro, filho a filho
                    f1Rels = f1.get("proRel")
                    f1RelCods = f1.get("processosRelacionados")

                    # A relação de "eSinteseDe" é inversa de "eSintetizadoPor",
                    # e são feitas inferências iniciais que tornam este tipo de
                    # situações explícitas, por isso basta verificar do processo
                    # A para B, e verificar B para A torna-se redundante.
                    if f1Rels and f1RelCods:
                        relacoesF1 = zip(f1Rels,f1RelCods)
                        if ("eSinteseDe",codF2) not in relacoesF1 or ("eSintetizadoPor",codF2) not in relacoesF1:
                            rep.addFalhaInv("rel_3_inv_3",cod)
                    else:
                        # Se algum não tem relações então já está mal
                        rep.addFalhaInv("rel_3_inv_3",cod)


def rel_5_inv_1(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é suplemento para outro,
    deve ser acrescentado um critério de utilidade
    administrativa na justificação do respetivo PCA"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                proRel = classe.get("proRel")
                if proRel and "eSuplementoPara" in proRel:
                    just = classe.get("pca",{}).get("justificacao")
                    if just:
                        justUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                        # TODO: faltam erros melhores aqui
                        if not justUtilidade:
                            rep.addFalhaInv("rel_5_inv_1",cod)
                    else:
                        rep.addFalhaInv("rel_5_inv_1",cod)


def rel_5_inv_2(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "No critério de utilidade administrativa devem aparecer
    todos os processos com os quais existe uma relação de
    suplemento para"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRel = classe.get("proRel")
                proRelCods = classe.get("processosRelacionados")
                if proRel and "eSuplementoPara" in proRel:
                    supls = [c for r,c in zip(proRel,proRelCods) if r=="eSuplementoPara"]
                    justificacao = classe.get("pca",{}).get("justificacao")
                    if justificacao:
                        jUtilidade = [x for x in justificacao if x["tipo"]=="utilidade"]
                        if jUtilidade:
                            allProcRefs = []
                            for crit in jUtilidade:
                                allProcRefs += crit.get("procRefs",[])

                            for s in supls:
                                if s not in allProcRefs:
                                    rep.addFalhaInv("rel_5_inv_2",cod,o=s)
                        else:
                            # Aqui como não nenhum procRef, todos os supls estão em falta
                            for s in supls:
                                rep.addFalhaInv("rel_5_inv_2",cod,o=s)
                    else:
                        # Aqui como não nenhum procRef, todos os supls estão em falta
                        for s in supls:
                            rep.addFalhaInv("rel_5_inv_2",cod,o=s)


def rel_7_inv_2(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é complementar de outro,
    a justificação do DF deverá conter o critério
    de complementaridade informacional"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eComplementarDe" in proRel:
                just = classe.get("df",{}).get("justificacao")
                if just:
                    justComplementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    # TODO: faltam erros melhores aqui
                    if not justComplementaridade:
                        rep.addFalhaInv("rel_7_inv_2",cod)
                else:
                    rep.addFalhaInv("rel_7_inv_2",cod)


def rel_6_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é síntetizado por outro,
    o DF deve ter o valor de 'Eliminação'"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eSintetizadoPor" in proRel:
                filhos = classe.get("filhos")
                if not filhos and  "eSinteseDe" not in proRel and "eComplementarDe" not in proRel:
                    valor = classe.get("df",{}).get("valor")
                    if valor != 'E':
                        rep.addFalhaInv("rel_6_inv_2",cod)


def rel_5_inv_3(allClasses,rep:Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é suplemento de outro, o critério
    a acrescentar na justificação do PCA é livre, normalmente
    é o critério legal. Todos os processos relacionados pela
    relação suplemento de devem figurar neste critério"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eSuplementoDe" in proRel:
                just = classe.get("pca",{}).get("justificacao",[])
                supl = [cod for rel,cod in zip(proRel,classe["processosRelacionados"]) if rel=="eSuplementoDe"]

                if just:
                    allProcRefs = []
                    for j in just:
                        procRefs = j.get("procRefs",[])
                        allProcRefs+=procRefs

                    for sup in supl:
                        if sup not in allProcRefs:
                            if sup not in allClasses:
                                # TODO: decidir o que fazer com os em harmonização
                                print(f"Harmonização: {sup}")

                            # TODO: melhorar o erro
                            rep.addFalhaInv("rel_5_inv_3",cod)
                else:
                    # Registar todos processos em faltam caso não haja justificação
                    for sup in supl:
                        if sup not in allClasses:
                            # TODO: decidir o que fazer com os em harmonização
                            print(f"Harmonização: {sup}")

                        # TODO: melhorar o erro
                        rep.addFalhaInv("rel_5_inv_3",cod)


def rel_9_inv_2(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN é eSinteseDe -> DF é de conservação"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eSinteseDe" in proRel:
                valor = classe.get("df",{}).get("valor")
                if valor and valor != "C":
                    rep.addFalhaInv("rel_9_inv_2",cod)


def rel_3_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Só existe desdobramento caso o PCA ou DF sejam distintos"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if codFilhos:
                filhos = [allClasses.get(c) for c in codFilhos]
                valores = [(f["pca"]["valores"],f["df"]["valor"]) for f in filhos if "pca" in f and "df" in f]
                # Se as combinações de pca e df tiverem valores repetidos,
                # então não deve haver desdobramento. E por isso o invariante falha
                if len(valores) != len(set(valores)):
                    # TODO: especificar melhor o erro
                    rep.addFalhaInv("rel_3_inv_1",cod)


def rel_3_inv_5(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "As relações temDF e temPCA, não existem numa
    classe 3 se esta tiver filhos"
    """

    # TODO: especificar melhor o erro
    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if classe.get("filhos") and (classe.get("pca") or classe.get("df")):
                rep.addFalhaInv("rel_3_inv_5",cod)


def rel_3_inv_7(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN (Classe 3) for complementar de outro que
    se desdobra ao 4º nível, é necessário, com base no
    critério de complementaridade informacional,a relação
    manter-se ao 3º nível. Pelo menos um dos 4ºs níveis
    deve ser de conservação."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRels = classe.get("proRel")
            proRelCods = classe.get("processosRelacionados")
            if proRels and proRelCods and "eComplementarDe" in proRels:
                compls = [c for c,r in zip(proRelCods,proRels) if r=="eComplementarDe"]
                for compl in compls:
                    codFilhos = allClasses[compl].get("filhos")
                    filhos = [allClasses.get(c) for c in codFilhos]
                    if filhos:
                        conservacao = False
                        for filho in filhos:
                            valor = filho.get("df",{}).get("valor")
                            if valor == "C":
                                conservacao = True
                                break
                        # Se nenhum processo tiver o valor de "C",
                        # então o invariante falha
                        if not conservacao:
                            # TODO: especificar em que compl falhou
                            rep.addFalhaInv("rel_3_inv_7",cod)


def rel_3_inv_4(allClasses,termosIndice,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando há desdobramento em 4ºs níveis, os termos de
    índice são replicados em cada um desses níveis."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if codFilhos:
                termosPai = [t["termo"] for t in termosIndice if t["codigo"]==cod]
                for c in codFilhos:
                    termosFilho = [t["termo"] for t in termosIndice if t["codigo"]==c]
                    for t in termosPai:
                        if t not in termosFilho:
                            # TODO: indicar o TI em falta no erro e em que filho
                            rep.addFalhaInv("rel_3_inv_4",cod)


def rel_6_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN tem uma relação de síntese, o seu DF deverá
    ter uma justificação onde consta um critério de
    densidade informacional"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRels = classe.get("proRel")
                if proRels and ("eSinteseDe" in proRels or "eSintetizadoPor" in proRels):
                    just = classe.get("df",{}).get("justificacao")
                    if just:
                        justDensidade = [x for x in just if x["tipo"]=="densidade"]
                        if not justDensidade:
                            rep.addFalhaInv("rel_6_inv_3",cod)
                    else:
                        rep.addFalhaInv("rel_6_inv_3",cod)


def rel_6_inv_4(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos relacionados por uma relação de
    síntese deverão estar relacionados com o critério de
    densidade informacional da respetiva justificação"
    """

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
                        just = classe.get("df",{}).get("justificacao")
                        sints = [c for c,r in zip(proRelCods,proRels) if r in ["eSinteseDe","eSintetizadoPor"]]
                        if just:
                            jDensidade = [x for x in just if x["tipo"]=="densidade"]
                            allProcRefs = []
                            for crit in jDensidade:
                                allProcRefs += crit.get("procRefs",[])

                            for s in sints:
                                if s not in allProcRefs:
                                    # TODO: meter no erro o código em falta
                                    rep.addFalhaInv("rel_6_inv_4",cod)
                        else:
                            # Aqui já se sabe que não existe justificação,
                            # por isso estão todos em falta
                            for s in sints:
                                # TODO: meter no erro o código em falta
                                rep.addFalhaInv("rel_6_inv_4",cod)


def rel_9_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN é eSintetizadoPor -> DF é de eliminação"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRels = classe.get("proRel")
                if proRels and "eSintetizadoPor" in proRels and "eComplementarDe" not in proRels and "eSinteseDe" not in proRels:
                    valor = classe.get("df",{}).get("valor")
                    if valor != "E":
                        rep.addFalhaInv("rel_9_inv_3",cod)


def rel_7_inv_3(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Todos os processos relacionados pela relação é complementar
    de, devem estar relacionados com o critério de complementaridade
    informacional da respetiva justificação"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRelCods = classe.get("processosRelacionados")
            proRels = classe.get("proRel")
            if proRels and "eComplementarDe" in proRels:
                just = classe.get("df",{}).get("justificacao")
                compls = [c for c,r in zip(proRelCods,proRels) if r=="eComplementarDe"]
                if just:
                    jComlpementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    allProcRefs = []
                    for crit in jComlpementaridade:
                        allProcRefs += crit.get("procRefs",[])

                    for c in compls:
                        if c not in allProcRefs:
                            # TODO: meter no erro o código em falta
                            rep.addFalhaInv("rel_7_inv_3",cod)
                else:
                    # Aqui já se sabe que não existe justificação,
                    # por isso estão todos em falta
                    for c in compls:
                        # TODO: meter no erro o código em falta
                        rep.addFalhaInv("rel_7_inv_3",cod)


def rel_9_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Se um PN é eComplementarDe -> DF é de conservação"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            codFilhos = classe.get("filhos")
            if not codFilhos:
                proRels = classe.get("proRel")
                if proRels and "eComplementarDe" in proRels:
                    valor = classe.get("df",{}).get("valor")
                    if valor != "C":
                        rep.addFalhaInv("rel_9_inv_1",cod)


def rel_4_inv_8(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um PN só pode ter uma relação com outro PN."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRels = classe.get("processosRelacionados")
            if proRels:
                proRelsCount = Counter(proRels)
                duplicados = [x for x,count in proRelsCount.items() if count > 1]
                for dup in duplicados:
                    # TODO: especificar melhor o erro
                    rep.addFalhaInv("rel_4_inv_8",cod,o=dup)


def rel_6_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Quando o PN em causa é síntese de outro, o DF deve
    ter o valor de 'Conservação'"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            if not classe.get("filhos"):
                proRels = classe.get("proRel")
                if proRels and "eSinteseDe" in proRels and "eSintetizadoPor" not in proRels:
                    valor = classe.get("df",{}).get("valor")
                    if valor != 'C':
                        rep.addFalhaInv("rel_6_inv_1",cod)


def rel_4_inv_10(termosIndice,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Os termos de indice de um PN não existem em mais
    nenhuma classe 3"
    """

    n3 = re.compile(r'^\d{3}\.\d{1,3}\.\d{1,3}$')
    termos = {}
    for t in termosIndice:
        cod = t["codigo"]
        termo = t["termo"]
        if n3.fullmatch(cod):
            if termo in termos:
                termos[termo].add(cod)
            else:
                termos[termo] = set([cod]) #{termo:[100,200]}

    # TODO: organizar melhor o erro aqui
    for t,cods in termos.items():
        if len(cods) > 1:
            print(t)
            print(cods)
            for c in cods:
                rep.addFalhaInv("rel_4_inv_10",c)


def rel_4_inv_7(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Na relação temRelProc um PN não se relaciona
    com ele próprio."
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] == 3:
            proRelCods = classe.get("processosRelacionados")
            proRels = classe.get("proRel")
            if proRelCods:
                # Identificar os todos os casos em que o processo
                # se menciona a si próprio
                selfRels = [(c,r) for c,r in zip(proRelCods,proRels) if cod==c]
                for r in selfRels:
                    rep.addFalhaInv("rel_4_inv_7",cod,p=r)


def rel_8_inv_1(allClasses,rep: Report):
    """
    A função testa o seguinte invariante e guarda
    em `rep` os casos em que falha:

    "Um DF, na sua justificação, deverá conter
    apenas critérios de densidade informacional,
    complementaridade informacional e legal"
    """

    for cod,classe in allClasses.items():
        if classe["nivel"] in [3,4]:
            just = classe.get("df",{}).get("justificacao")
            if just:
                for j in just:
                    if j["tipo"] not in ["complementaridade","densidade","legal"]:
                        # TODO: Especificar melhor o erro
                        rep.addFalhaInv("rel_8_inv_1",cod)

t0 = time.time()
rep = Report()

allClasses,harmonizacao = processClasses(rep)
with open("files/ti.json",'r') as f:
    termosIndice = json.load(f)
ok = rep.checkStruct()
if not ok:
    rep.fixMissingRels(allClasses)
    

# --------------------------
# "Com erros"
# --------------------------

rel_4_inv_2(allClasses,harmonizacao,rep)
rel_4_inv_3(allClasses,harmonizacao,rep)
rel_4_inv_4(allClasses,harmonizacao,rep)
rel_4_inv_12(allClasses,rep)
rel_4_inv_13(allClasses,rep)
rel_5_inv_1(allClasses,rep)
rel_5_inv_3(allClasses,rep)
rel_3_inv_4(allClasses,termosIndice,rep)
rel_7_inv_2(allClasses,rep)
rel_4_inv_0(allClasses,rep)
rel_7_inv_3(allClasses,rep)
rel_6_inv_4(allClasses,rep)
rel_9_inv_3(allClasses,rep)
rel_6_inv_3(allClasses,rep)


# --------------------------
# "Sem erros"
# --------------------------

rel_3_inv_1(allClasses,rep)
rel_3_inv_5(allClasses,rep)
rel_4_inv_5(allClasses,harmonizacao,rep)
rel_4_inv_6(allClasses,harmonizacao,rep)
rel_4_inv_11(allClasses,rep)
rel_3_inv_6(allClasses,rep)
rel_9_inv_2(allClasses,rep)
rel_6_inv_2(allClasses,rep)
rel_3_inv_7(allClasses,rep)
rel_6_inv_1(allClasses,rep)
rel_4_inv_7(allClasses,rep)


# --------------------------
# "Testes"
# --------------------------

rel_3_inv_3(allClasses,rep)
rel_5_inv_2(allClasses,rep)
rel_4_inv_8(allClasses,rep)

rel_4_inv_1_0(allClasses,rep)
rel_8_inv_1(allClasses,rep)

checkUniqueInst(rep)

rep.printInv()
rep.dumpReport()
t1 = time.time()
print(t1-t0)