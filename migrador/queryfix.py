import re
from .report import ErroInv, Report
from . import checkInvariantes as check
from utils.log_utils import FIX
import logging
import copy

logger = logging.getLogger(FIX)

def rel_2_inv_12_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_2_inv_12.
    """
    errFixed = 0
    logger.info("Correção do invariante rel_2_inv_12")
    for err in erros:
        classe = allClasses.get(err.cod)
        if classe:
            if "legislacao" not in classe:
                classe["legislacao"] = [err.info["leg"]]
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{err.cod}</b>")
                errFixed += 1
            elif err.info["leg"] not in classe["legislacao"]:
                # Aqui evitam-se adicionar legislações repetidas
                classe["legislacao"].append(err.info["leg"])
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{err.cod}</b>")
                errFixed += 1
            else:
                # Aqui o erro já se encontra corrigido
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{err.cod}</b>")
                errFixed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_2_inv_12")


def rel_2_inv_13_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_2_inv_13.
    """

    logger.info("Correção do invariante rel_2_inv_13")
    errFixed = 0
    errFailed = 0

    for err in erros:
        # Neste caso, como os erros são acerca de classes de
        # nível 4, a correção acontece na classe pai
        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', err.cod).group(1)
        classePai = allClasses.get(pai)

        if classePai:
            if "legislacao" not in classePai:
                classePai["legislacao"] = [err.info["leg"]]
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{pai}</b>")
                errFixed += 1
            # Aqui evitam-se adicionar legislações repetidas
            elif err.info["leg"] not in classePai["legislacao"]:
                classePai["legislacao"].append(err.info["leg"])
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{pai}</b>")
                errFixed += 1
            # Aqui o erro já se encontra corrigido,
            # provavelmente durante a correção de um processo "irmão"
            else:
                err.fix(f"A legislação <b>{err.info["leg"]}</b> foi adicionada à zona de contexto do processo <b>{pai}</b>")
                errFixed += 1

        else:
            err.fail(f"Processo <b>{pai}</b> não encontrado")
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_2_inv_13")
    logger.info(f"Falharam {errFailed} correções do invariante rel_2_inv_13")


def rel_3_inv_2_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_3_inv_2.
    """

    logger.info("Correção do invariante rel_3_inv_2")
    errFixed = 0
    errFailed = 0

    for err in erros:
        classe = allClasses.get(err.cod)
        if classe:
            pca = classe.get("pca",{})
            just = pca.get("justificacao",[])
            # Para efetuar a correção é necessário que haja um pca
            if pca:

                critCod = ""
                # Verifica-se primeiro se existe apenas um critério do tipo "utilidade"
                # Se existir mais do que 1, não é possível realizar a correção
                utilidade = [j for j in just if j.get("tipo") == "utilidade"]
                if len(utilidade) > 1:
                    err.fail(f"O processo <b>{err.cod}</b> contém mais do que uma justificação de critério do tipo \"<b>utilidade</b>\" no seu PCA")
                    errFailed += 1
                    continue

                # Se já existe um critério do tipo "utilidade",
                # o processo em falta é acrescentado nele
                elif len(utilidade) == 1:
                    procRefs = utilidade[0].get("procRefs",[])
                    procRefs.append(err.info["proc"])
                    critCod = utilidade[0]["critCodigo"]
                    for crit in just:
                        if crit["tipo"] == "utilidade":
                            crit["conteudo"] = crit["conteudo"].strip()
                            # Adicionar o conteúdo de acordo com o que já lá está
                            if crit["conteudo"] and not crit["conteudo"].endswith((';','.')):
                                crit["conteudo"] += f". É suplemento para o PN {err.info["proc"]} - {classe.get("titulo","")}."
                            elif crit["conteudo"]:
                                crit["conteudo"] += f" É suplemento para o PN {err.info["proc"]} - {classe.get("titulo","")}."
                            else:
                                crit["conteudo"] += f"É suplemento para o PN {err.info["proc"]} - {classe.get("titulo","")}."

                            crit["procRefs"] = procRefs
                            break
                    err.fix(f"O processo <b>{err.info["proc"]}</b> foi adicionado no critério de justificação <b>{critCod}</b> do PCA do processo <b>{err.cod}</b>")
                    errFixed += 1

                # Se ainda não existe um critério do tipo "utilidade",
                # é criado um novo critério de acordo com o padrão
                elif len(utilidade) == 0:
                    critCod = genCritCod("pca",err.cod,classe)
                    newCrit = {
                        "critCodigo": critCod,
                        "tipo": "utilidade",
                        "conteudo": f"É suplemento para o PN {err.info["proc"]} - {classe.get("titulo","")}.",
                        "procRefs": [err.info["proc"]]
                    }
                    just.append(newCrit)
                    # Caso a justificação não exista
                    pca["justificacao"] = just
                    err.fix(f"Um novo critério de utilidade da justificação do PCA do processo <b>{err.cod}</b> foi gerado automaticamente com o código <b>{critCod}</b>. O processo <b>{err.info["proc"]}</b> foi adicionado ao critério criado.")
                    errFixed += 1
            else:
                err.fail(f"O processo <b>{err.cod}</b> não tem PCA")
                errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_3_inv_2")
    logger.info(f"Falharam {errFailed} correções do invariante rel_3_inv_2")


def rel_4_inv_2_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_4_inv_2.
    """

    errFixed = 0
    errFailed = 0
    logger.info("Correção do invariante rel_4_inv_2")
    for err in erros:
        classe = allClasses[err.cod]
        df = classe.get("df",{})
        just = df.get("justificacao",[])
        # Para efetuar a correção é necessário que haja um df
        if df:
            critCod = ""
            rel = ""
            if err.info["rel"] == "eSinteseDe":
                rel = "É síntese do"
            elif err.info["rel"] == "eSintetizadoPor":
                rel = "É sintetizado pelo"
            # Verifica-se primeiro se existe apenas um critério do tipo "densidade"
            # Se existir mais do que 1, não é possível realizar a correção
            densidade = [j for j in just if j.get("tipo") == "densidade"]
            if len(densidade) > 1:
                err.fail(f"O processo <b>{err.cod}</b> contém mais do que uma justificação de critério do tipo \"<b>densidade</b>\" no seu DF")
                errFailed += 1
                continue

            # Se já existe um critério do tipo "densidade",
            # o processo em falta é acrescentado nele
            elif len(densidade) == 1:
                procRefs = densidade[0].get("procRefs",[])
                procRefs.append(err.info["proc"])
                critCod = densidade[0]["critCodigo"]
                for crit in just:
                    if crit["tipo"] == "densidade":
                        crit["conteudo"] = crit["conteudo"].strip()
                        # Adicionar o conteúdo de acordo com o que já lá está
                        if crit["conteudo"] and not crit["conteudo"].endswith((';','.')):
                            crit["conteudo"] += f". {rel} PN {err.info["proc"]} - {classe.get("titulo","")}."
                        elif crit["conteudo"]:
                            crit["conteudo"] += f" {rel} PN {err.info["proc"]} - {classe.get("titulo","")}."
                        else:
                            crit["conteudo"] += f"{rel} PN {err.info["proc"]} - {classe.get("titulo","")}."

                        crit["procRefs"] = procRefs
                        break
                err.fix(f"O processo <b>{err.info["proc"]}</b> foi adicionado no critério de justificação <b>{critCod}</b> do DF do processo <b>{err.cod}</b>")
                errFixed += 1

            # Se ainda não existe um critério do tipo "densidade",
            # é criado um novo critério de acordo com o padrão
            elif len(densidade) == 0:

                critCod = genCritCod("df",err.cod,classe)
                newCrit = {
                    "critCodigo": critCod,
                    "tipo": "densidade",
                    "conteudo": f"{rel} PN {err.info["proc"]} - {classe.get("titulo","")}.",
                    "procRefs": [err.info["proc"]]
                }
                just.append(newCrit)
                # Caso a justificação não exista
                df["justificacao"] = just
                err.fix(f"Um novo critério de densidade da justificação do DF do processo <b>{err.cod}</b> foi gerado automaticamente com o código <b>{critCod}</b>. O processo <b>{err.info["proc"]}</b> foi adicionado ao critério criado.")
                errFixed += 1
        else:
            err.fail(f"O processo <b>{err.cod}</b> não tem DF")
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_4_inv_2")
    logger.info(f"Falharam {errFailed} correções do invariante rel_4_inv_2")


def rel_5_inv_2_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_5_inv_2.
    """

    errFixed = 0
    errFailed = 0
    logger.info("Correção do invariante rel_5_inv_2")
    for err in erros:
        classe = allClasses[err.cod]
        df = classe.get("df",{})
        just = df.get("justificacao",[])
        # Para efetuar a correção é necessário que haja um df
        if df:
            critCod = ""

            # Verifica-se primeiro se existe apenas um critério do tipo "complementaridade"
            # Se existir mais do que 1, não é possível realizar a correção
            compls = [j for j in just if j.get("tipo") == "complementaridade"]
            if len(compls) > 1:
                err.fail(f"O processo <b>{err.cod}</b> contém mais do que uma justificação de critério do tipo \"<b>complementaridade</b>\" no seu DF")
                errFailed += 1
                continue

            # Se já existe um critério do tipo "complementaridade",
            # o processo em falta é acrescentado nele
            elif len(compls) == 1:
                procRefs = compls[0].get("procRefs",[])
                procRefs.append(err.info["proc"])
                critCod = compls[0]["critCodigo"]
                for crit in just:
                    if crit["tipo"] == "complementaridade":
                        crit["conteudo"] = crit["conteudo"].strip()
                        # Adicionar o conteúdo de acordo com o que já lá está
                        if crit["conteudo"] and not crit["conteudo"].endswith((';','.')):
                            crit["conteudo"] += f". É complementar do PN {err.info["proc"]} - {classe.get("titulo","")}."
                        elif crit["conteudo"]:
                            crit["conteudo"] += f" É complementar do PN {err.info["proc"]} - {classe.get("titulo","")}."
                        else:
                            crit["conteudo"] += f"É complementar do PN {err.info["proc"]} - {classe.get("titulo","")}."

                        crit["procRefs"] = procRefs
                        break
                err.fix(f"O processo <b>{err.info["proc"]}</b> foi adicionado no critério de justificação <b>{critCod}</b> do DF do processo <b>{err.cod}</b>")
                errFixed += 1

            # Se ainda não existe um critério do tipo "complementaridade",
            # é criado um novo critério de acordo com o padrão
            elif len(compls) == 0:

                critCod = genCritCod("df",err.cod,classe)
                newCrit = {
                    "critCodigo": critCod,
                    "tipo": "complementaridade",
                    "conteudo": f"É complementar do PN {err.info["proc"]} - {classe.get("titulo","")}.",
                    "procRefs": [err.info["proc"]]
                }
                just.append(newCrit)
                # Caso a justificação não exista
                df["justificacao"] = just
                err.fix(f"Um novo critério de complementaridade da justificação do DF do processo <b>{err.cod}</b> foi gerado automaticamente com o código <b>{critCod}</b>. O processo <b>{err.info["proc"]}</b> foi adicionado ao critério criado.")
                errFixed += 1
        else:
            err.fail(f"O processo <b>{err.cod}</b> não tem DF")
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_5_inv_2")
    logger.info(f"Falharam {errFailed} correções do invariante rel_5_inv_2")


def rel_1_inv_3_fix(termosIndice,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_1_inv_3.
    """

    errFixed = 0
    errFailed = 0
    logger.info("Correção do invariante rel_1_inv_3")
    for err in erros:
        # Formulação do novo termo índice
        termo = {
            "codigo" : err.info["filho"],
            "termo": err.info["termo"]
        }
        termosIndice.append(termo)
        err.fix(f"O termo índice \"<b>{err.info["termo"]}</b>\" foi adicionado ao processo <b>{err.info["filho"]}</b>")
        errFixed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_1_inv_3")
    logger.info(f"Falharam {errFailed} correções do invariante rel_1_inv_3")


def rel_8_inv_6_fix(allClasses,erros: list[ErroInv],invs):
    """
    Faz a correção das falhas do invariante rel_8_inv_6.
    """

    deps = [
        "rel_1_inv_6",
        "rel_2_inv_8",
        "rel_2_inv_9",
        "rel_5_inv_1",
        "rel_5_inv_2",
        "rel_8_inv_1"
    ]

    logger.info("Correção do invariante rel_8_inv_6")
    errFixed = 0
    errFailed = 0

    for err in erros:
        # Verificação dos erros já existentes na classe,
        # antes da correção
        c = allClasses[err.cod]
        classesTestBefore = {err.cod: c}
        codFilhos = c.get("filhos",[])
        for f in codFilhos:
            classesTestBefore[f] = allClasses.get(f,{})
        repBefore = testDepends(deps,classesTestBefore)

        # Aplicação da correção numa cópia da classe
        classeCopy = copy.deepcopy(allClasses[err.cod])
        proRelCods = classeCopy.get("processosRelacionados",[])
        proRels = classeCopy.get("proRel",[])
        if len(proRelCods) == len(proRels):
            proRelCods.append(err.info["proc"])
            proRels.append("eComplementarDe")

            # Verificação dos erros depois de aplicar a correção
            classesTestAfter = {err.cod: classeCopy}
            repAfter = testDepends(deps,classesTestAfter)
            diff = diffReports(repBefore,repAfter)

            if diff:
                invDesc = []
                for i in diff:
                    desc = f"({invs.get(i,{}).get("desc")})" or ""
                    s = f"<b>{i}</b> {desc}"
                    invDesc.append(s)
                err.fail(f"A tentativa de correção automática falhou porque arriscava violar o(s) invariante(s): {'; '.join(invDesc)}")
                errFailed += 1
            else:
                err.fix(f"A relação \"<b>{err.cod}</b> <b><i>eComplementarDe</b></i> <b>{err.info["proc"]}</b>\" foi adicionada à zona de contexto do processo <b>{err.cod}</b>")
                errFixed += 1
        else:
            err.fail("A tentativa de correção automática falhou porque os processos relacionados e respetivas relações não têm a mesma cardinalidade")
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_8_inv_6")
    logger.info(f"Falharam {errFailed} correções do invariante rel_8_inv_6")


def rel_8_inv_7_fix(allClasses,erros: list[ErroInv],invs):
    """
    Faz a correção das falhas do invariante rel_8_inv_7.
    """

    deps = [
        "rel_2_inv_7",
        "rel_2_inv_8",
        "rel_2_inv_9",
        "rel_3_inv_1",
        "rel_3_inv_2"
    ]

    logger.info("Correção do invariante rel_8_inv_7")
    errFixed = 0
    errFailed = 0

    for err in erros:
        # Verificação dos erros já existentes na classe,
        # antes da correção
        classesTestBefore = {err.cod: allClasses[err.cod]}
        repBefore = testDepends(deps,classesTestBefore)

        # Aplicação da correção numa cópia da classe
        classeCopy = copy.deepcopy(allClasses[err.cod])
        proRelCods = classeCopy.get("processosRelacionados",[])
        proRels = classeCopy.get("proRel",[])
        if len(proRelCods) == len(proRels):
            proRelCods.append(err.info["proc"])
            proRels.append("eSuplementoPara")

            # Verificação dos erros depois de aplicar a correção
            classesTestAfter = {err.cod: classeCopy}
            repAfter = testDepends(deps,classesTestAfter)
            diff = diffReports(repBefore,repAfter)

            if diff:
                invDesc = []
                for i in diff:
                    desc = f"({invs.get(i,{}).get("desc")})" or ""
                    s = f"<b>{i}</b> {desc}"
                    invDesc.append(s)
                err.fail(f"A tentativa de correção automática falhou porque arriscava violar o(s) invariante(s): {'; '.join(invDesc)}")
                errFailed += 1
            else:
                err.fix(f"A relação \"<b>{err.cod}</b> <b><i>eSuplementoPara</b></i> <b>{err.info["proc"]}</b>\" foi adicionada à zona de contexto do processo <b>{err.cod}</b>")
                errFixed += 1
        else:
            err.fail("A tentativa de correção automática falhou porque os processos relacionados e respetivas relações não têm a mesma cardinalidade")
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_8_inv_7")
    logger.info(f"Falharam {errFailed} correções do invariante rel_8_inv_7")


def testDepends(deps,classes):
    """
    Faz a verificação dos invariantes em `deps`
    para `classes` e retorna um Report com os
    erros encontrados.
    """

    # Desabilitação temporária dos logs
    logger.disabled = True
    rep = Report()
    for dep in deps:
        # Não funciona para alguns invariantes
        # que não recebem estes argumentos, está
        # muito hardcoded
        func =  getattr(check,dep)
        func(classes,rep)
    logger.disabled = False
    return rep


def diffReports(repBefore: Report, repAfter: Report):
    """
    Calcula se foram adicionados erros de falha de invariantes
    entre o `repBefore` e o `repAfter`. Serve para averiguar se
    a correção automática de um invariante é viável.

    Retorna a lista de invariantes que seriam
    violados caso as alterações fossem aplicadas.
    """

    invs = set()
    errosInvItems = repBefore.globalErrors["erroInv"].items()
    errInvBefore = {k:set([x.msg for x in v]) for k,v in errosInvItems}
    for inv, err in repAfter.globalErrors["erroInv"].items():
        for e in err:
            if e.msg not in errInvBefore:
                invs.add(inv)
                break
    return invs


def genCritCod(tipo, cod, classe):
    """
    Calcula o próximo código do critério de
    justificação do PCA ou do DF de um dado processo.
    """

    just = classe.get(tipo,{}).get("justificacao")
    critCod = ""
    if just:
        # O critCod é criado de forma incremental por isso
        # vai-se buscar o último critério e incrementa-se
        # para obter o novo critCod
        lastCritCod = just[-1]["critCodigo"][-1]
        critCod = f"just_{tipo}_c{cod}_{int(lastCritCod)+1}"
    else:
        critCod = f"just_{tipo}_c{cod}_{0}"

    return critCod
