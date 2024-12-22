import json
import time
import re

sheets = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']

allErros = []

def rel_4_inv_0(sheet):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "Um processo sem desdobramento ao 4º nível
    tem de ter uma justificação associada ao PCA."
    """

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
    # global allErros
    # allErros += erros
    return erros

def rel_4_inv_1_1(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eCruzadoCom é simétrica."
    """
    cache = {sheetName:sheet}
    erros = []
    for classe in sheet:
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            eCruzadoCom = [proRelCods[i] for i,x in enumerate(proRels) if x=="eCruzadoCom"]
            for c in eCruzadoCom:
                fileName = re.search(r'^\d{3}', c).group(0)
                if fileName not in cache:
                    with open(f"files/{fileName}.json","r") as f:
                        cache[fileName] = json.load(f)
                # Econtrar o processo em questão
                cruzado = [x for x in cache[fileName] if x["codigo"]==c]

                # FIXME: A classe menciona uma classe que não existe!
                if len(cruzado) == 0:
                    print("-"*15)
                    print(classe["codigo"])
                    print("eCruzadoCom")
                    print(c)
                    print("-"*15)
                    # Por enquanto ignora-se quando não existe
                    continue
                # cruzadoCod = cruzado[0]["codigo"]
                proRels2 = cruzado[0].get("proRel")
                proRelCods2 = cruzado[0].get("processosRelacionados")
                if proRelCods2 and proRels2 and (len(proRelCods2)==len(proRels2)):
                    eCruzadoCom2 = [proRelCods2[i] for i,x in enumerate(proRels2) if x=="eCruzadoCom"]
                    # Se não eCruzadoCom de volta então não cumpre com o invariante
                    if classe["codigo"] not in eCruzadoCom2:
                        erros.append(classe["codigo"])
                # Se não existe então também não contém eCruzadoCom,
                # e por isso não cumpre com o invariante
                else:
                    erros.append(classe["codigo"])
    # print(f"Erros:{len(erros)}")
    return erros




def rel_4_inv_3(sheet,sheetName):
    """
    A função devolve a lista de classes que não cumprem
    com este invariante:

    "A relação eSintetizadoPor é antisimétrica."
    """

    cache = {sheetName:sheet}
    erros = []
    for classe in sheet:
        proRels = classe.get("proRel")
        proRelCods = classe.get("processosRelacionados")
        if proRels and proRelCods:
            eSintetizadoPor = [proRelCods[i] for i,x in enumerate(proRels) if x=="eSintetizadoPor"]
            for c in eSintetizadoPor:
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
                    print("eSintetizadoPor")
                    print(c)
                    print("-"*15)
                    # Por enquanto ignora-se quando não existe
                    continue

                proRels2 = sintetizado[0].get("proRel")
                proRelCods2 = sintetizado[0].get("processosRelacionados")
                if proRelCods2 and proRels2 and (len(proRelCods2)==len(proRels2)):
                    eSintetizadoPor2 = [proRelCods2[i] for i,x in enumerate(proRels2) if x=="eSintetizadoPor"]
                    # Se existe a relação eSintetizadoPor aqui também, não cumpre com o invariante
                    if classe["codigo"] in eSintetizadoPor2:
                        erros.append(classe["codigo"])

    print(f"Erros:{len(erros)}")
    return erros



t0 = time.time()
for sheetName in sheets:
    with open(f"files/{sheetName}.json",'r') as f:
        file = json.load(f)
    rel_4_inv_0(file)
    rel_4_inv_1_1(file,sheetName)
    rel_4_inv_3(file,sheetName)

t1 = time.time()
print(t1-t0)
