from .excel2json import excel2json
from . import checkInvariantes as c
from .report import Report
from . import genTTL as g
import json
import os
from . import queryfix as fix
from utils.path_utils import FILES_DIR, PROJECT_ROOT
import logging
from utils.log_utils import FIX, GEN, INV, PROC

def migra(filename):

    loggerProc = logging.getLogger(PROC)
    loggerInv = logging.getLogger(INV)
    loggerCorr = logging.getLogger(FIX)
    loggerGen = logging.getLogger(GEN)
    rep = Report()

    loggerProc.info("-"*80)
    loggerProc.info(f"Inicio da migração do ficheiro {filename}")
    loggerProc.info("-"*80)

    # --------------------------------------------
    # Criação dos ficheiros JSON intermédios
    # --------------------------------------------

    loggerProc.info("Criação dos ficheiros JSON intermédios")
    excel2json(rep,filename)

    # --------------------------------------------
    # Processamento inicial dos dados
    # --------------------------------------------

    loggerProc.info("-"*80)
    loggerProc.info("Processamento inicial dos dados")
    loggerProc.info("-"*80)
    allClasses,harmonizacao = c.processClasses(rep)

    # Inferências de relações
    loggerProc.info("Inferências de relações")
    rep.fixMissingRels(allClasses)

    loggerProc.info("Verificação da estrutura dos dados")
    ok = rep.checkStruct()

    loggerProc.info("-"*80)
    loggerProc.info("Processamento Inicial de dados terminado")
    loggerProc.info("-"*80)

    # --------------------------------------------
    # Verificação dos invariantes
    # --------------------------------------------

    loggerInv.info("-"*80)
    loggerInv.info("Verificação dos invariantes")
    loggerInv.info("-"*80)

    with open(os.path.join(FILES_DIR,"ti.json"),'r') as f:
        termosIndice = json.load(f)

    c.rel_2_inv_3(allClasses,rep)
    c.rel_2_inv_4(allClasses,rep)
    c.rel_2_inv_5(allClasses,rep)
    c.rel_2_inv_12(allClasses,rep)
    c.rel_2_inv_13(allClasses,rep)
    c.rel_3_inv_1(allClasses,rep)
    c.rel_3_inv_3(allClasses,rep)
    c.rel_1_inv_3(allClasses,termosIndice,rep)
    c.rel_5_inv_1(allClasses,rep)
    c.rel_2_inv_1(allClasses,rep)
    c.rel_5_inv_2(allClasses,rep)
    c.rel_4_inv_3(allClasses,rep)
    c.rel_4_inv_2(allClasses,rep)
    c.rel_1_inv_2(allClasses,rep)
    c.rel_1_inv_1(allClasses,rep)
    c.rel_1_inv_4(allClasses,rep)
    c.rel_2_inv_6(allClasses,rep)
    c.rel_2_inv_7(allClasses,rep)
    c.rel_2_inv_11(allClasses,rep)
    c.rel_1_inv_5(allClasses,rep)
    c.rel_8_inv_2(allClasses,rep)
    c.rel_4_inv_1(allClasses,rep)
    c.rel_1_inv_6(allClasses,rep)
    c.rel_2_inv_8(allClasses,rep)
    c.rel_3_inv_2(allClasses,rep)
    c.rel_2_inv_9(allClasses,rep)
    c.rel_2_inv_2(allClasses,rep)
    c.rel_2_inv_14(allClasses,rep)
    c.rel_1_inv_7(allClasses,harmonizacao,rep)
    c.rel_8_inv_1(allClasses,rep)
    c.rel_2_inv_10(termosIndice,rep)

    c.rel_8_inv_3(allClasses,rep)
    c.rel_8_inv_4(allClasses,rep)
    c.rel_8_inv_5(allClasses,rep)
    c.rel_8_inv_6(allClasses,rep)
    c.rel_7_inv_1(allClasses,rep)
    c.rel_6_inv_1(allClasses,rep)

    loggerInv.info("-"*80)
    loggerInv.info("Verificação dos invariantes terminada")
    loggerInv.info("-"*80)

    # --------------------------------------------
    # Correções
    # --------------------------------------------


    with open(os.path.join(PROJECT_ROOT, "invariantes.json")) as f:
        invsJson = json.load(f)

    invs = {}
    for r in invsJson["invariantes"]:
        for i in r["inv"]:
            invs[f"{r["idRel"]}_{i["idInv"]}"] = {
                "desc": i["desc"],
                "clarificacao": i["clarificacao"]
            }

    loggerCorr.info("-"*80)
    loggerCorr.info("Correção automática dos erros")
    loggerCorr.info("-"*80)
    fix.rel_2_inv_12_fix(allClasses,rep.globalErrors["erroInv"]["rel_2_inv_12"])
    fix.rel_2_inv_13_fix(allClasses,rep.globalErrors["erroInv"]["rel_2_inv_13"])
    fix.rel_3_inv_2_fix(allClasses,rep.globalErrors["erroInv"]["rel_3_inv_2"])
    fix.rel_4_inv_3_fix(allClasses,rep.globalErrors["erroInv"]["rel_4_inv_3"])
    fix.rel_5_inv_2_fix(allClasses,rep.globalErrors["erroInv"]["rel_5_inv_2"])
    fix.rel_1_inv_3_fix(termosIndice,rep.globalErrors["erroInv"]["rel_1_inv_3"])
    fix.rel_8_inv_5_fix(allClasses,rep.globalErrors["erroInv"]["rel_8_inv_5"],invs)
    fix.rel_8_inv_6_fix(allClasses,rep.globalErrors["erroInv"]["rel_8_inv_6"],invs)
    loggerCorr.info("-"*80)
    loggerCorr.info("Correção automática dos erros terminada")
    loggerCorr.info("-"*80)
    rep.dumpReport()

    # --------------------------------------------
    # Geração da ontologia final
    # --------------------------------------------

    # A ontologia só é gerada se nenhum erro "grave" for encontrado
    if ok:

        # Reorganização dos dados
        finalClasses = { c:{} for c in rep.classesN1}
        for cod,proc in allClasses.items():
            # Aqui não faz mal ir buscar o cod desta
            # forma porque não existem erros graves
            if len(cod) >=3:
                classe = cod[:3]
                finalClasses[classe][cod] = proc

        loggerGen.info("-"*80)
        loggerGen.info("Geração dos ficheiros de ontologia")
        loggerGen.info("-"*80)

        g.tiGenTTL(termosIndice)
        g.entidadeGenTTL()
        g.tipologiaGenTTL()
        g.legGenTTL()

        for clN1,procs in finalClasses.items():
            g.classeGenTTL(clN1,procs)

        loggerGen.info("-"*80)
        loggerGen.info("Geração dos ficheiros de ontologia terminada")
        loggerGen.info("-"*80)
    else:
        loggerGen.info("-"*80)
        loggerGen.warning("Ontologia não foi criada devido à existência de erros graves")
        loggerGen.info("-"*80)

    return rep, ok, invs
