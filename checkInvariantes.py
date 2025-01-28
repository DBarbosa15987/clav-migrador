import json
import time
import re
from report import Report
from itertools import zip_longest
from collections import Counter

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

    A função produz um relatório destes erros e retorna `False` se
    encontrar algo e `True` se não houver inconsistências deste tipo.
    """

    data = {}
    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
            x = json.load(f)
            data.update(x)

    allClasses = {}
    for cod,classe in data.items():

        # Se a classe está em harmonização, ainda pode estar incompleta,
        # por isso não é incluída para verificação de invariantes. Deve
        # ser marcada como warning.
        if classe["estado"] == "H":
            rep.addWarning("H",cod)
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
                if proc not in data.keys():
                    rep.addRelInvalida(proc,rel,cod)
                else:
                    # TODO: eliminar os checks redundantes??
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

    return allClasses


def rel_4_inv_0(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

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


def checkAntissimetrico(allClasses,rel,rep: Report,invName):
    """
    Verifica para uma `sheet` se uma dada relação
    é antisimétrica.

    Retorna a lista das classes em que isto não se verifica.
    """


    for cod,classe in allClasses.items():
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            relacoes = [c for c,r in zip(proRelCods,proRels) if r==rel]
            for c in relacoes:
                relacao = allClasses.get(c)

                # TODO: no futuro assumir que está certo, porque só depois de validado é que se chega a esta função
                if not relacao:
                    print("-"*15)
                    print(cod)
                    print(rel)
                    print(c)
                    print("-"*15)
                    continue

                proRels2 = relacao.get("proRel")
                proRelCods2 = relacao.get("processosRelacionados")
                if proRelCods2 and proRels2:
                    relacoes2 = [c for c,r in zip(proRelCods2,proRels2) if r==rel]
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


def checkSimetrico(allClasses,rel,rep: Report,invName):
    """
    Verifica para uma `sheet` se uma dada relação
    é simétrica.

    Retorna a lista das classes em que isto não se verifica.
    """
    pass
    # global i,allErros
    # cache = {sheetName:sheet}
    # erros = []
    # for classe in sheet:
    #     proRels = classe.get("proRel")
    #     proRelCods = classe.get("processosRelacionados")
    #     if proRels and proRelCods:
    #         relacoes = [proRelCods[i] for i,x in enumerate(proRels) if x==rel]
    #         for r in relacoes:
    #             fileName = re.search(r'^\d{3}', r).group(0)
    #             if fileName not in cache:
    #                 with open(f"files/{fileName}.json","r") as f:
    #                     cache[fileName] = json.load(f)
    #             # Econtrar o processo em questão
    #             classeRel = [x for x in cache[fileName] if x["codigo"]==r]

    #             # FIXME: A classe menciona uma classe que não existe!
    #             if len(classeRel) == 0:
    #                 print("-"*15)
    #                 print(classe["codigo"])
    #                 print(rel)
    #                 print(r)
    #                 print("-"*15)
    #                 # Por enquanto ignora-se quando não existe
    #                 continue

    #             proRels2 = classeRel[0].get("proRel")
    #             proRelCods2 = classeRel[0].get("processosRelacionados")
    #             if proRelCods2 and proRels2 and (len(proRelCods2)==len(proRels2)):
    #                 relacoes2 = [proRelCods2[i] for i,x in enumerate(proRels2) if x==rel]
    #                 # Se a `rel` não se verifica de volta então não cumpre com o invariante
    #                 if classe["codigo"] not in relacoes2:
    #                     erros.append(classe["codigo"])
    #                 else:
    #                     i+=1
    #             # Se não existe, então também não contém `rel`,
    #             # e por isso não cumpre com o invariante
    #             else:
    #                 erros.append(classe["codigo"])

    # # print(f"Erros:{len(erros)}")
    # # allErros += erros
    # return erros


def rel_4_inv_1_1(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eCruzadoCom é simétrica."
    """

    return checkSimetrico(allClasses,"eCruzadoCom",rep,"rel_4_inv_1_1")


def rel_4_inv_1_2(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eComplementarDe é simétrica"
    """

    return checkSimetrico(allClasses,"eComplementarDe",rep,"rel_4_inv_1_2")


def rel_4_inv_3(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSintetizadoPor é antisimétrica."
    """

    return checkAntissimetrico(allClasses,"eSintetizadoPor",rep,"rel_4_inv_3")


def rel_4_inv_4(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSucessorDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,"eSucessorDe",rep,"rel_4_inv_4")


def rel_4_inv_11(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto
    do processo que tem essa justificação (Classes de nível 3)"
    """

    return checkJustRef(allClasses,3,rep,"rel_4_inv_12")


def rel_4_inv_13(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto do
    processo que tem essa justificação (Classes de nível 4)"
    """

    return checkJustRef(allClasses,4,rep,"rel_4_inv_13")


def rel_4_inv_5(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,"eSuplementoDe",rep,"rel_4_inv_5")


def rel_4_inv_6(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoPara é antisimétrica."
    """

    return checkAntissimetrico(allClasses,"eSuplementoPara",rep,"rel_4_inv_6")


def rel_4_inv_2(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSinteseDe é antisimétrica."
    """

    return checkAntissimetrico(allClasses,"eSinteseDe",rep,"rel_4_inv_2")


def rel_3_inv_6(allClasses,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

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


def rel_5_inv_1(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Quando o PN em causa é suplemento para outro,
    deve ser acrescentado um critério de utilidade
    administrativa na justificação do respetivo PCA"
    """
    # FIXME: ver a coisa dos filhos que estava na query "MINUS {?s :temFilho ?f}"
    global allErros
    erros = []
    for cod,classe in sheet.items():
        if classe["nivel"] == 3: # FIXME fazer isto?
            if not classe.get("filhos"): # FIXME porquê?
                proRel = classe.get("proRel")
                if proRel and "eSuplementoPara" in proRel:
                    just = classe.get("pca",{}).get("justificacao")
                    if just:
                        justUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                        if not justUtilidade:
                            erros.append(cod)
                    else:
                        erros.append(cod)

    allErros+=erros
    return erros


def rel_7_inv_2(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Quando o PN em causa é complementar de outro,
    a justificação do DF deverá conter o critério 
    de complementaridade informacional"
    """
    # TODO: faltam as coisas dos (?crit :critTemProcRel ?o)?
    global allErros
    erros = []
    for cod,classe in sheet.items():
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eComplementarDe" in proRel:
                just = classe.get("df",{}).get("justificacao")
                if just:
                    justComplementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    # TODO: faltam erros melhores aqui
                    if not justComplementaridade:
                        erros.append(cod)
                else:
                    erros.append(cod)

    allErros += erros
    return erros


def rel_6_inv_2(sheet,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Quando o PN em causa é síntetizado por outro,
    o DF deve ter o valor de 'Eliminação'"
    """

    for cod,classe in sheet.items():
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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
    A função devolve a lista de classes que não cumprem
    com este invariante:

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
                

def rel_4_inv_10(termosIndice,rep: Report):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

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


t0 = time.time()
rep = Report()

allClasses = processClasses(rep)
with open("files/ti.json",'r') as f:
    termosIndice = json.load(f)
ok = rep.checkStruct()
if not ok:
    rep.fixMissingRels(allClasses)
    

# folha a folha
# for sheetName in sheets:
#     with open(f"files/{sheetName}.json",'r') as f:
#         file = json.load(f)
#     rel_4_inv_0(file,rep)
#     rel_4_inv_11(file,rep)
#     rel_4_inv_12(file,rep)
#     rel_4_inv_13(file,rep)
#     rel_3_inv_6(file,rep)



    # rel_9_inv_2(file,rep)

    # rel_6_inv_2(file,rep)
    # rel_5_inv_3(file)

    # rel_5_inv_1(file)
    # rel_7_inv_2(file)

    # --------------------------
    # "Sem erros"
    # --------------------------

    # rel_3_inv_1(file,rep)
    # rel_3_inv_5(file,rep)


    # rel_4_inv_1_1(file,sheetName,rep)
    # rel_4_inv_1_2(file,sheetName,rep)
    # rel_4_inv_2(file,sheetName,rep)
    # rel_4_inv_3(file,sheetName,rep)
    # rel_4_inv_4(file,sheetName,rep)
    # rel_4_inv_5(file,sheetName,rep)
    # rel_4_inv_6(file,sheetName,rep)

# tudo de uma vez
checkUniqueInst(rep)


rep.printInv()
rep.dumpReport()
t1 = time.time()
print(t1-t0)