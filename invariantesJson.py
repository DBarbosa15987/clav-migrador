import json
import time
import re

sheets = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']

allErros = []
i=0


def checkClasses():
    """
    Função que verifica se existem códigos de classe repetidas
    e se todas as classes mencionadas (em relações) existem de facto.

    A função produz um relatório destes erros e retorna `False` se
    encontrar algo e `True` se não houver inconsistências deste tipo.
    """

    declaracoes = {} # {"100":["100.ttl"], "200":["100.ttl","200.ttl"]}
    relacoes = {} # {"200":["100.10.001"]} -> "200" é mencionado por "100.10.001"
    report = {
        "declaracoesRepetidas" : [],
        "relacoesInvalidas" : []
    }

    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
            data = json.load(f)
            for classe in data:

                cod = classe['codigo']
                # TODO: remover?
                if cod in declaracoes:
                    declaracoes[cod].append(sheet+".ttl")
                else:
                    declaracoes[cod] = [sheet+".ttl"]

                proRels = classe.get("processosRelacionados")
                df = classe.get("df")
                pca = classe.get("pca")
                if proRels:
                    for proRel in proRels:
                        if proRel in relacoes:
                            relacoes[proRel].append(cod)
                        else:
                            relacoes[proRel] = [cod]
                    
                if df:
                    justificacao = df.get("justificacao")
                    if justificacao:
                        for j in justificacao:
                            procRefs = j.get("procRefs")
                            if procRefs:
                                for p in procRefs:
                                    if p in relacoes:
                                        relacoes[proRel].append(cod)
                                    else:
                                        relacoes[proRel] = [cod]

                if pca:
                    justificacao = pca.get("justificacao")
                    if justificacao:
                        for j in justificacao:
                            procRefs = j.get("procRefs")
                            if procRefs:
                                for p in procRefs:
                                    if p in relacoes:
                                        relacoes[proRel].append(cod)
                                    else:
                                        relacoes[proRel] = [cod]

    print([(k,v) for k,v in declaracoes.items() if len(v)>1])
    print('\n'.join([str((k,v,len(relacoes[k]))) for k,v in relacoes.items() if k not in declaracoes]))


def rel_4_inv_0(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA."
    """

    # global allErros
    classesN3 = [x for x in sheet if x["nivel"] == 3]
    erros = []
    for classe in classesN3:
        filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
        # Se não tem filhos tem de ter uma justificação associada ao PCA
        if len(filhos) == 0:
            if classe.get("pca"):
                if not classe["pca"].get("justificacao"):
                    erros.append(classe["codigo"])
            else:
                erros.append(classe["codigo"])
    # print(erros)
    # allErros += erros
    return erros


def checkAntissimetrico(sheet,sheetName,rel):
    """
    Verifica para uma `sheet` se uma dada relação
    é antisimétrica.

    Retorna a lista das classes em que isto não se verifica.
    """

    global allErros
    cache = {sheetName:sheet}
    erros = []
    for classe in sheet:
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods and (len(proRelCods)==len(proRels)):
            relacao = [proRelCods[i] for i,x in enumerate(proRels) if x==rel]
            for c in relacao:
                fileName = re.search(r'^\d{3}', c).group(0)
                if fileName not in cache:
                    with open(f"files/{fileName}.json","r") as f:
                        cache[fileName] = json.load(f)
                # Econtrar o processo em questão
                sintetizado = [x for x in cache[fileName] if x["codigo"]==c]

                # FIXME: A classe menciona uma classe que não existe!
                if len(sintetizado) == 0:
                    print("-"*15)
                    print(classe["codigo"])
                    print(rel)
                    print(c)
                    print("-"*15)
                    # Por enquanto ignora-se quando não existe
                    continue

                proRels2 = sintetizado[0].get("proRel")
                proRelCods2 = sintetizado[0].get("processosRelacionados")
                if proRelCods2 and proRels2 and (len(proRelCods2)==len(proRels2)):
                    relacao2 = [proRelCods2[i] for i,x in enumerate(proRels2) if x==rel]
                    # Se existe a relação `rel` aqui também, não cumpre com o invariante
                    if classe["codigo"] in relacao2:
                        erros.append(classe["codigo"])

    # print(f"Erros:{len(erros)}")
    # allErros += erros
    return erros


def checkJustRef(sheet,nivel):
    """
    Verifica se as classes do `nível` passado por input (3 ou 4)
    referenciam as legislações mencionadas nas justificações de pca e df.

    No caso da classe ser de nível 4 a legislação é mencionada
    apenas na classe pai.

    Retorna a lista das classes em que isto não se verifica.
    """

    erros = []
    classesN = [x for x in sheet if x["nivel"] == nivel]
    for classe in classesN:
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
                        erros.append(classe["codigo"])

                    # Se a classe for de nível 4 verifica-se se 
                    # a legislação é mencionada no pai
                    elif nivel == 4:
                        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', classe["codigo"]).group(1)
                        # TODO: fazer um search pela lista melhor
                        classePai = [x for x in sheet if x["codigo"] == pai]
                        if classePai:
                            classePai = classePai[0]
                            if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                erros.append(classe["codigo"])

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
                        erros.append(classe["codigo"])

                    # Se a classe for de nível 4 verifica-se se 
                    # a legislação é mencionada no pai
                    if nivel == 4:
                        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', classe["codigo"]).group(1)
                        classePai = [x for x in sheet if x["codigo"] == pai]
                        if classePai:
                            classePai = classePai[0]
                            if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                erros.append(classe["codigo"])

    return erros


def checkUniqueInst():
    """
    Função que verifica a unicidade das instâncias
    mencionadas nos seguintes invariantes:

    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância NotaAplicacao;
    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância NotaExclusao;
    * 2 Classes (nível 1, 2 ou 3) não podem ter a mesma instância ExemploNotaAplicacao;
    """

    notas = {
        "notasAp":{}, # ex: {"nota_200.30.301_df9148e99f28": ["200.30.301","100"] }
        "exemplosNotasAp":{}, # ex: {"exemplo_200.30.301_bdd4fbd33603": ["200.30.301","100"] }
        "notasEx":{}, # ex: {"nota_200.30.301_4f1104c7755b": ["200.30.301","100"] }
    }

    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
            data = json.load(f)
            for classe in data:
                if classe["nivel"] in [1,2,3]:
                    for nota,k in [("notasAp","idNota"),("exemplosNotasAp","idExemplo"),("notasEx","idNota")]:
                        if classe.get(nota):
                            for n in classe[nota]:
                                if n[k] in notas[nota]:
                                    notas[nota][n[k]].append(classe["codigo"])
                                else:
                                    notas[nota][n[k]] = [classe["codigo"]]

    print(f"notasAp: {[(k,v) for k,v in notas["notasAp"].items() if len(v) > 1]}")
    print(f"exemplosNotasAp: {[(k,v) for k,v in notas["exemplosNotasAp"].items() if len(v) > 1]}")
    print(f"notasEx: {[(k,v) for k,v in notas["notasEx"].items() if len(v) > 1]}")


def checkSimetrico(sheet,sheetName,rel):
    """
    Verifica para uma `sheet` se uma dada relação
    é simétrica.

    Retorna a lista das classes em que isto não se verifica.
    """

    global i,allErros
    cache = {sheetName:sheet}
    erros = []
    for classe in sheet:
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            relacoes = [proRelCods[i] for i,x in enumerate(proRels) if x==rel]
            for r in relacoes:
                fileName = re.search(r'^\d{3}', r).group(0)
                if fileName not in cache:
                    with open(f"files/{fileName}.json","r") as f:
                        cache[fileName] = json.load(f)
                # Econtrar o processo em questão
                classeRel = [x for x in cache[fileName] if x["codigo"]==r]

                # FIXME: A classe menciona uma classe que não existe!
                if len(classeRel) == 0:
                    print("-"*15)
                    print(classe["codigo"])
                    print(rel)
                    print(r)
                    print("-"*15)
                    # Por enquanto ignora-se quando não existe
                    continue

                proRels2 = classeRel[0].get("proRel")
                proRelCods2 = classeRel[0].get("processosRelacionados")
                if proRelCods2 and proRels2 and (len(proRelCods2)==len(proRels2)):
                    relacoes2 = [proRelCods2[i] for i,x in enumerate(proRels2) if x==rel]
                    # Se a `rel` não se verifica de volta então não cumpre com o invariante
                    if classe["codigo"] not in relacoes2:
                        erros.append(classe["codigo"])
                    else:
                        i+=1
                # Se não existe, então também não contém `rel`,
                # e por isso não cumpre com o invariante
                else:
                    erros.append(classe["codigo"])

    # print(f"Erros:{len(erros)}")
    # allErros += erros
    return erros



def rel_4_inv_1_1(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eCruzadoCom é simétrica."
    """
    return checkSimetrico(sheet,sheetName,"eCruzadoCom")


def rel_4_inv_1_2(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eComplementarDe é simétrica"
    """

    return checkSimetrico(sheet,sheetName,"eComplementarDe")


def rel_4_inv_3(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSintetizadoPor é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSintetizadoPor")


def rel_4_inv_4(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSucessorDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSucessorDe")


def rel_4_inv_11(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um PN não pode ter em simultâneo relações de 
    'éSínteseDe' e 'éSintetizadoPor' com outros PNs"
    """

    erros = []
    for classe in sheet:
        # TODO: saber aqui quais é que "quebram o inv"
        proRels = classe.get("proRel")
        # proRelCods = classe.get("processosRelacionados")
        # Se a classe contém ambas as relações, nãp cumpre com o invariante
        if proRels and "eSinteseDe" in proRels and "eSintetizadoPor" in proRels:
            erros.append(classe['codigo'])
    return erros


def rel_4_inv_12(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto
    do processo que tem essa justificação (Classes de nível 3)"
    """

    return checkJustRef(sheet,3)


def rel_4_inv_13(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto do
    processo que tem essa justificação (Classes de nível 4)"
    """

    return checkJustRef(sheet,4)


def rel_4_inv_5(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSuplementoDe")


def rel_4_inv_6(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoPara é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSuplementoPara")


def rel_4_inv_2(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSinteseDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSinteseDe")


checkClasses()

t0 = time.time()
# folha a folha
for sheetName in sheets:
    with open(f"files/{sheetName}.json",'r') as f:
        file = json.load(f)
    rel_4_inv_0(file)
    rel_4_inv_1_1(file,sheetName)
    rel_4_inv_1_2(file,sheetName)
    rel_4_inv_2(file,sheetName)
    rel_4_inv_3(file,sheetName)
    rel_4_inv_4(file,sheetName)
    rel_4_inv_5(file,sheetName)
    rel_4_inv_6(file,sheetName)
    rel_4_inv_11(file)
    rel_4_inv_12(file)
    rel_4_inv_13(file)

# tudo de uma vez
# checkUniqueInst()


t1 = time.time()
print(t1-t0)
# print(allErros)
# print(len(allErros))
