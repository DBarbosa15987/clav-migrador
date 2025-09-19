import re
from .report import ErroInv
from log_utils import FIX
import logging

logger = logging.getLogger(FIX)

def rel_2_inv_12_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_2_inv_12.
    """
    errFixed = 0
    errFailed = 0
    logger.info("Correção do invariante rel_2_inv_12")
    for err in erros:
        classe = allClasses.get(err.cod)
        if classe:
            if "legislacao" not in classe:
                classe["legislacao"] = [err.info]
                err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {err.cod}")
                errFixed += 1
            # Aqui evitam-se adicionar legislações repetidas
            elif err.info not in classe["legislacao"]:
                classe["legislacao"].append(err.info)
                err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {err.cod}")
                errFixed += 1
        else:
            err.fix(f"Processo {err.cod} não encontrado",failed=True)
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_2_inv_12")
    logger.info(f"Falharam {errFailed} correções do invariante rel_2_inv_12")


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
                classePai["legislacao"] = [err.info]
                err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {pai}")
                errFixed += 1
            # Aqui evitam-se adicionar legislações repetidas
            elif err.info not in classePai["legislacao"]:
                classePai["legislacao"].append(err.info)
                err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {pai}")
                errFixed += 1
            # Aqui o erro já se encontra corrrigido,
            # provavelmente durrante a correção de um processo "irmão"
            else:
                err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {pai}")
                errFixed += 1

        else:
            err.fix(f"Processo {pai} não encontrado",failed=True)
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
        classe = allClasses[err.cod]
        pca = classe.get("pca",{})
        just = pca.get("justificacao",[])
        # Para efetuar a correção é necessário que haja um pca
        if pca:

            critCod = ""
            # Verifica-se primeiro se existe apenas um critério do tipo "utilidade"
            # Se existir mais do que 1, não é possível realizar a correção
            utilidade = [j for j in just if j.get("tipo") == "utilidade"]
            if len(utilidade) > 1:
                err.fix(f"O processo {err.cod} contém mais do que uma justificação de critério do tipo \"utilidade\" no seu PCA",failed=True)
                errFailed += 1
                continue


            # Se já existe um critério do tipo "utilidade",
            # o processo em falta é acrescentado nele
            elif len(utilidade) == 1:
                procRefs = utilidade[0].get("procRefs",[])
                procRefs.append(err.info)
                critCod = utilidade[0]["critCodigo"]
                for crit in just:
                    if crit["tipo"] == "utilidade":
                        # Adicionar o conteúdo de acordo com o que já lá está
                        if crit["conteudo"] and crit["conteudo"][-1] != ';':
                            crit["conteudo"] += f";É suplemento para {err.info};"
                        else:
                            crit["conteudo"] += f"É suplemento para {err.info};"

                        crit["procRefs"] = procRefs
                        break
                err.fix(f"O processo {err.info} foi adicionado no critério de justificação {critCod} do PCA do processo {err.cod}")
                errFixed += 1

            # Se ainda não existe um critério do tipo "utilidade",
            # é criado um novo critério de acordo com o padrão
            elif len(utilidade) == 0:
                critCod = genCritCod("pca",err.cod,classe)
                newCrit = {
                    "critCodigo": critCod,
                    "tipo": "utilidade",
                    "conteudo": f"É suplemento para {err.info};",
                    "procRefs": [err.info]
                }
                just.append(newCrit)
                # Caso a justifição não exista
                pca["justificacao"] = just
                err.fix(f"Um novo critério de utilidade da justificação do PCA do processo {err.cod} foi gerado automaticamente com o código {critCod}. O processo {err.info} foi adicionado ao critério criado.")
                errFixed += 1
        else:
            err.fix(f"O processo {err.cod} não tem PCA", failed=True)
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_3_inv_2")
    logger.info(f"Falharam {errFailed} correções do invariante rel_3_inv_2")


def rel_4_inv_3_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_4_inv_3.
    """

    errFixed = 0
    errFailed = 0
    logger.info("Correção do invariante rel_4_inv_3")
    for err in erros:
        classe = allClasses[err.cod]
        df = classe.get("df",{})
        just = df.get("justificacao",[])
        # Para efetuar a correção é necessário que haja um df
        if df:
            critCod = ""
            rel = ""
            if err.info["rel"] == "eSinteseDe":
                rel = "É síntese de"
            elif err.info["rel"] == "eSintetizadoPor":
                rel = "É sintetizado por"
            # Verifica-se primeiro se existe apenas um critério do tipo "densidade"
            # Se existir mais do que 1, não é possível realizar a correção
            densidade = [j for j in just if j.get("tipo") == "densidade"]
            if len(densidade) > 1:
                err.fix(f"O processo {err.cod} contém mais do que uma justificação de critério do tipo \"densidade\" no seu DF",failed=True)
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
                        # Adicionar o conteúdo de acordo com o que já lá está
                        if crit["conteudo"] and crit["conteudo"][-1] != ';':
                            crit["conteudo"] += f";{rel} {err.info};"
                        else:
                            crit["conteudo"] += f"{rel} {err.info};"

                        crit["procRefs"] = procRefs
                        break
                err.fix(f"O processo {err.info["proc"]} foi adicionado no critério de justificação {critCod} do DF do processo {err.cod}")
                errFixed += 1

            # Se ainda não existe um critério do tipo "densidade",
            # é criado um novo critério de acordo com o padrão
            elif len(densidade) == 0:

                critCod = genCritCod("df",err.cod,classe)
                newCrit = {
                    "critCodigo": critCod,
                    "tipo": "densidade",
                    "conteudo": f"{rel} {err.info["proc"]};",
                    "procRefs": [err.info["proc"]]
                }
                just.append(newCrit)
                # Caso a justifição não exista
                df["justificacao"] = just
                err.fix(f"Um novo critério de densidade da justificação do DF do processo {err.cod} foi gerado automaticamente com o código {critCod}. O processo {err.info["proc"]} foi adicionado ao critério criado.")
                errFixed += 1
        else:
            err.fix(f"O processo {err.cod} não tem DF", failed=True)
            errFailed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_4_inv_3")
    logger.info(f"Falharam {errFailed} correções do invariante rel_4_inv_3")


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
                err.fix(f"O processo {err.cod} contém mais do que uma justificação de critério do tipo \"complementaridade\" no seu DF",failed=True)
                errFailed += 1
                continue

            # Se já existe um critério do tipo "complementaridade",
            # o processo em falta é acrescentado nele
            elif len(compls) == 1:
                procRefs = compls[0].get("procRefs",[])
                procRefs.append(err.info)
                critCod = compls[0]["critCodigo"]
                for crit in just:
                    if crit["tipo"] == "complementaridade":
                        # Adicionar o conteúdo de acordo com o que já lá está
                        if crit["conteudo"] and crit["conteudo"][-1] != ';':
                            crit["conteudo"] += f";É complementar de {err.info};"
                        else:
                            crit["conteudo"] += f"É complementar de {err.info};"

                        crit["procRefs"] = procRefs
                        break
                err.fix(f"O processo {err.info} foi adicionado no critério de justificação {critCod} do DF do processo {err.cod}")
                errFixed += 1

            # Se ainda não existe um critério do tipo "complementaridade",
            # é criado um novo critério de acordo com o padrão
            elif len(compls) == 0:

                critCod = genCritCod("df",err.cod,classe)
                newCrit = {
                    "critCodigo": critCod,
                    "tipo": "complementaridade",
                    "conteudo": f"É complementar de {err.info};",
                    "procRefs": [err.info]
                }
                just.append(newCrit)
                # Caso a justifição não exista
                df["justificacao"] = just
                err.fix(f"Um novo critério de complementaridade da justificação do DF do processo {err.cod} foi gerado automaticamente com o código {critCod}. O processo {err.info} foi adicionado ao critério criado.")
                errFixed += 1
        else:
            err.fix(f"O processo {err.cod} não tem DF", failed=True)
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
        err.fix(f"O termo índice \"{err.info["termo"]}\" foi adicionado ao processo {err.info["filho"]}")
        errFixed += 1

    logger.info(f"Foram corrigidas {errFixed} falhas do invariante rel_1_inv_3")
    logger.info(f"Falharam {errFailed} correções do invariante rel_1_inv_3")


def rel_8_inv_4_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_8_inv_4.
    """
    # TODO: esperar pelas notas


def rel_8_inv_5_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_8_inv_5.
    """
    # TODO: esperar pelas notas


def rel_8_inv_6_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_8_inv_6.
    """
    # TODO: esperar pelas notas


def genCritCod(tipo, cod, classe):
    """
    Calcula o próximo código do critério de
    justificação do PCA ou do DF de um dado processo.
    """

    just = classe.get(tipo,{}).get("justificacao")
    critCod = ""
    if just:
        # O critCod é criado de forma incremental por isso vai-se buscar
        # o último critério e incrementa-se para obter o novo critCod
        lastCritCod = just[-1]["critCodigo"][-1]
        critCod = f"just_{tipo}_c{cod}_{int(lastCritCod)+1}"
    else:
        critCod = f"just_{tipo}_c{cod}_{0}"

    return critCod
