import json
import time
import re
from errorReport import ErrorReport

sheets = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']

allErros = []
i=0


def checkClasses(err: ErrorReport):
    """
    Função que verifica se existem códigos de classe repetidas
    e se todas as classes mencionadas (em relações) existem de facto.

    A função produz um relatório destes erros e retorna `False` se
    encontrar algo e `True` se não houver inconsistências deste tipo.
    """

    for sheet in sheets:
        with open(f"files/{sheet}.json",'r') as f:
            data = json.load(f)
            for classe in data:

                cod = classe['codigo']
                err.addDecl(cod,sheet)

                proRels = classe.get("processosRelacionados")
                rels = classe.get("proRel")
                df = classe.get("df")
                pca = classe.get("pca")
                if proRels:
                    for i,proRel in enumerate(proRels):
                        rel = None
                        if rels and len(rels)==len(proRels):
                            rel = rels[i]
                        err.addRelacao(proRel,rel,cod)
                    
                if df:
                    justificacao = df.get("justificacao")
                    if justificacao:
                        for j in justificacao:
                            procRefs = j.get("procRefs")
                            if procRefs:
                                for p in procRefs:
                                    err.addRelacao(p,"procRef",cod,"df")

                if pca:
                    justificacao = pca.get("justificacao")
                    if justificacao:
                        for j in justificacao:
                            procRefs = j.get("procRefs")
                            if procRefs:
                                for p in procRefs:
                                    err.addRelacao(p,"procRef",cod,"pca")

    return err.evalStruct()


def rel_4_inv_0(sheet,err: ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA."
    """

    for classe in sheet:
        if classe["nivel"] == 3:
            filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
            # Se não tem filhos tem de ter uma justificação associada ao PCA
            if len(filhos) == 0:
                if classe.get("pca"):
                    if not classe["pca"].get("justificacao"):
                        err.addFalhaInv("rel_4_inv_0",classe["codigo"])
                else:
                    err.addFalhaInv("rel_4_inv_0",classe["codigo"])


def checkAntissimetrico(sheet,sheetName,rel,err: ErrorReport,invName):
    """
    Verifica para uma `sheet` se uma dada relação
    é antisimétrica.

    Retorna a lista das classes em que isto não se verifica.
    """

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
                        err.addFalhaInv(invName,classe["codigo"],rel,sintetizado[0]["codigo"])


def checkJustRef(sheet,nivel,err:ErrorReport,invName):
    """
    Verifica se as classes do `nível` passado por input (3 ou 4)
    referenciam as legislações mencionadas nas justificações de pca e df.

    No caso da classe ser de nível 4 a legislação é mencionada
    apenas na classe pai.

    Retorna a lista das classes em que isto não se verifica.
    """

    for classe in sheet:
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
                            err.addFalhaInv(invName,classe["codigo"])

                        # Se a classe for de nível 4 verifica-se se 
                        # a legislação é mencionada no pai
                        elif nivel == 4:
                            pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', classe["codigo"]).group(1)
                            # TODO: fazer um search pela lista melhor
                            classePai = [x for x in sheet if x["codigo"] == pai]
                            if classePai:
                                classePai = classePai[0]
                                # TODO: dar mais detalhe sobre o erro
                                if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                    err.addFalhaInv(invName,classe["codigo"])

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
                            err.addFalhaInv(invName,classe["codigo"])

                        # Se a classe for de nível 4 verifica-se se 
                        # a legislação é mencionada no pai
                        if nivel == 4:
                            pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', classe["codigo"]).group(1)
                            classePai = [x for x in sheet if x["codigo"] == pai]
                            if classePai:
                                classePai = classePai[0]
                                if "legislacao" not in classePai or leg not in classePai["legislacao"]:
                                    err.addFalhaInv(invName,classe["codigo"])


def checkUniqueInst(err:ErrorReport):
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
            for classe in data:
                if classe["nivel"] in [1,2,3]:
                    for nota,idNota,invName in corr:
                        if classe.get(nota):
                            for n in classe[nota]:
                                if n[idNota] in notas[invName]:
                                    notas[invName][n[idNota]].append(classe["codigo"])
                                else:
                                    notas[invName][n[idNota]] = [classe["codigo"]]

    for inv,nota in notas.items():
        for id,cods in nota.items():
            # TODO: mais detalhe no erro
            if len(cods) > 1:
                err.addFalhaInv(inv,id)


def checkSimetrico(sheet,sheetName,rel,err: ErrorReport,invName):
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


def rel_4_inv_1_1(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eCruzadoCom é simétrica."
    """

    return checkSimetrico(sheet,sheetName,"eCruzadoCom",err,"rel_4_inv_1_1")


def rel_4_inv_1_2(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eComplementarDe é simétrica"
    """

    return checkSimetrico(sheet,sheetName,"eComplementarDe",err,"rel_4_inv_1_2")


def rel_4_inv_3(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSintetizadoPor é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSintetizadoPor",err,"rel_4_inv_3")


def rel_4_inv_4(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSucessorDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSucessorDe",err,"rel_4_inv_4")


def rel_4_inv_11(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um PN não pode ter em simultâneo relações de 
    'éSínteseDe' e 'éSintetizadoPor' com outros PNs"
    """

    for classe in sheet:
        # TODO: saber aqui quais é que "quebram o inv"
        proRels = classe.get("proRel")
        # proRelCods = classe.get("processosRelacionados")
        # Se a classe contém ambas as relações, não cumpre com o invariante
        if proRels and "eSinteseDe" in proRels and "eSintetizadoPor" in proRels:
            err.addFalhaInv("rel_4_inv_11",classe['codigo'])


def rel_4_inv_12(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto
    do processo que tem essa justificação (Classes de nível 3)"
    """

    return checkJustRef(sheet,3,err,"rel_4_inv_12")


def rel_4_inv_13(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um diploma legislativo referenciado num critério de
    justicação tem de estar associado na zona de contexto do
    processo que tem essa justificação (Classes de nível 4)"
    """

    return checkJustRef(sheet,4,err,"rel_4_inv_13")


def rel_4_inv_5(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSuplementoDe",err,"rel_4_inv_5")


def rel_4_inv_6(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSuplementoPara é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSuplementoPara",err,"rel_4_inv_6")


def rel_4_inv_2(sheet,sheetName,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:
    
    "A relação eSinteseDe é antisimétrica."
    """

    return checkAntissimetrico(sheet,sheetName,"eSinteseDe",err,"rel_4_inv_2")


def rel_3_inv_6(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "As relações temDF e temPCA, existem numa classe 3
    se esta não tiver filhos"
    """

    for classe in sheet:
        if classe["nivel"] == 3:
            # Verificar se tem filhos
            filhos = [c["codigo"] for c in sheet if c["codigo"].startswith(classe["codigo"]+".") ]
            if len(filhos) == 0:
                pca = classe.get("pca")
                df = classe.get("df")
                # TODO: especificar melhor os erros aqui
                if not pca or not df:
                    err.addFalhaInv("rel_3_inv_6",classe["codigo"])

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
    for classe in sheet:
        if classe["nivel"] == 3: # FIXME fazer isto?
            filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
            if not filhos: # FIXME porquê?
                proRel = classe.get("proRel")
                if proRel and "eSuplementoPara" in proRel:
                    just = classe.get("pca",{}).get("justificacao")
                    if just:
                        justUtilidade = [x for x in just if x["tipo"]=="utilidade"]
                        if not justUtilidade:
                            erros.append(classe["codigo"])
                    else:
                        erros.append(classe["codigo"])

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
    for classe in sheet:
        if classe["nivel"] == 3:
            proRel = classe.get("proRel")
            if proRel and "eComplementarDe" in proRel:
                just = classe.get("df",{}).get("justificacao")
                if just:
                    justComplementaridade = [x for x in just if x["tipo"]=="complementaridade"]
                    # TODO: faltam erros melhores aqui
                    if not justComplementaridade:
                        erros.append(classe["codigo"])
                else:
                    erros.append(classe["codigo"])

    allErros += erros
    return erros


def rel_3_inv_1(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Só existe desdobramento caso o PCA ou DF sejam distintos"
    """

    # FIXME notas
    for classe in sheet:
        if classe["nivel"] == 3:
            filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
            if filhos:
                valoresPca = [f["pca"]["valores"] for f in filhos if f.get("pca",{}).get("valores")]
                valoresDf = [f["df"]["valor"] for f in filhos if f.get("df",{}).get("valor")]
                # TODO: especificar melhor o erro
                # Se for diferente, então existem valores repetidos
                # E por isso não cumpre com o invariante
                if len(valoresPca) != set(valoresPca):
                    err.addFalhaInv("rel_3_inv_1",classe["codigo"])
                if len(valoresDf) != set(valoresDf):
                    err.addFalhaInv("rel_3_inv_1",classe["codigo"])


def rel_3_inv_5(sheet,err:ErrorReport):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "As relações temDF e temPCA, não existem numa
    classe 3 se esta tiver filhos"
    """

    # TODO: especificar melhor o erro
    for classe in sheet:
        if classe["nivel"] == 3:
            filhos = [x for x in sheet if x["codigo"].startswith(classe["codigo"] + ".")]
            if filhos and (classe.get("pca") or classe.get("df")):
                err.addFalhaInv("rel_3_inv_5",classe["codigo"])
   
t0 = time.time()
err = ErrorReport()

checkClasses(err)

# folha a folha
for sheetName in sheets:
    with open(f"files/{sheetName}.json",'r') as f:
        file = json.load(f)
    rel_4_inv_0(file,err)
    rel_4_inv_1_1(file,sheetName,err)
    rel_4_inv_1_2(file,sheetName,err)
    rel_4_inv_2(file,sheetName,err)
    rel_4_inv_3(file,sheetName,err)
    rel_4_inv_4(file,sheetName,err)
    rel_4_inv_5(file,sheetName,err)
    rel_4_inv_6(file,sheetName,err)
    rel_4_inv_11(file,err)
    rel_4_inv_12(file,err)
    rel_4_inv_13(file,err)

    rel_3_inv_6(file,err)


    # rel_6_inv_2(file)
    # rel_5_inv_3(file)
    # rel_9_inv_2(file)

    # rel_5_inv_1(file)
    # rel_7_inv_2(file)

# tudo de uma vez
checkUniqueInst(err)


t1 = time.time()
print(t1-t0)
err.printInv()
err.dumpReport()
