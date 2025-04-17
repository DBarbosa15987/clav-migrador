import re
from report import ErroInv

def rel_4_inv_12_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_4_inv_12.
    """

    for err in erros:
        classe = allClasses.get(err.cod)
        if classe:
            if "legislacao" not in classe:
                classe["legislacao"] = [err.info]
            # Aqui evitam-se adicionar legislações repetidas
            elif err.info not in classe["legislacao"]:
                classe["legislacao"].append(err.info)
            err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {err.cod}")


def rel_4_inv_13_fix(allClasses,erros: list[ErroInv]):
    """
    Faz a correção das falhas do invariante rel_4_inv_13.
    """

    for err in erros:
        # Neste caso, como os erros são acerca de classes de
        # nível 4, a correção acontece na classe pai
        pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', err.cod).group(1)
        classePai = allClasses.get(pai)
        if classePai:
            if "legislacao" not in classePai:
                classePai["legislacao"] = [err.info]
            # Aqui evitam-se adicionar legislações repetidas
            elif err.info not in classePai["legislacao"]:
                classePai["legislacao"].append(err.info)
            err.fix(f"A legislação {err.info} foi adicionada à zona de contexto do processo {pai}")

