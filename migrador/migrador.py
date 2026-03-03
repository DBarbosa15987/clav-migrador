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
    classes, harmonizacao, outros = c.processClasses(rep)

    # Inferências de relações
    loggerProc.info("Inferências de relações")
    rep.fixMissingRels(classes)

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

    with open(os.path.join(FILES_DIR,"ti.json")) as f:
        termosIndice = json.load(f)

    c.rel_2_inv_3(classes,rep)
    c.rel_2_inv_4(classes,rep)
    c.rel_2_inv_5(classes,rep)
    c.rel_2_inv_12(classes,rep)
    c.rel_2_inv_13(classes,rep)
    c.rel_3_inv_1(classes,rep)
    c.rel_3_inv_3(classes,rep)
    c.rel_1_inv_3(classes,termosIndice,rep)
    c.rel_5_inv_1(classes,rep)
    c.rel_2_inv_1(classes,rep)
    c.rel_5_inv_2(classes,rep)
    c.rel_4_inv_2(classes,rep)
    c.rel_1_inv_2(classes,rep)
    c.rel_1_inv_1(classes,rep)
    c.rel_1_inv_4(classes,rep)
    c.rel_2_inv_6(classes,rep)
    c.rel_2_inv_7(classes,rep)
    c.rel_2_inv_11(classes,rep)
    c.rel_1_inv_5(classes,rep)
    c.rel_8_inv_2(classes,rep)
    c.rel_4_inv_1(classes,rep)
    c.rel_1_inv_6(classes,rep)
    c.rel_2_inv_8(classes,rep)
    c.rel_3_inv_2(classes,rep)
    c.rel_2_inv_9(classes,rep)
    c.rel_2_inv_2(classes,rep)
    c.rel_2_inv_14(classes,rep)
    c.rel_1_inv_7(classes,harmonizacao,rep)
    c.rel_8_inv_1(classes,rep)
    c.rel_2_inv_10(termosIndice,rep)
    c.rel_8_inv_3(classes,rep)
    c.rel_8_inv_4(classes,rep)
    c.rel_8_inv_5(classes,rep)
    c.rel_8_inv_6(classes,rep)
    c.rel_8_inv_7(classes,rep)
    c.rel_7_inv_1(classes,rep)
    c.rel_6_inv_1(classes,rep)

    loggerInv.info("-"*80)
    loggerInv.info("Verificação dos invariantes terminada")
    loggerInv.info("-"*80)

    rep.dumpClasses(classes)

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
    errosInv = rep.globalErrors.get("erroInv",{})
    if "rel_2_inv_12" in errosInv:
        fix.rel_2_inv_12_fix(classes,rep.globalErrors["erroInv"]["rel_2_inv_12"])
    if "rel_2_inv_13" in errosInv:
        fix.rel_2_inv_13_fix(classes,rep.globalErrors["erroInv"]["rel_2_inv_13"])
    if "rel_3_inv_2" in errosInv:
        fix.rel_3_inv_2_fix(classes,rep.globalErrors["erroInv"]["rel_3_inv_2"])
    if "rel_3_inv_3" in errosInv:
        fix.rel_3_inv_3_fix(classes,rep.globalErrors["erroInv"]["rel_3_inv_3"])
    if "rel_4_inv_2" in errosInv:
        fix.rel_4_inv_2_fix(classes,rep.globalErrors["erroInv"]["rel_4_inv_2"])
    if "rel_5_inv_2" in errosInv:
        fix.rel_5_inv_2_fix(classes,rep.globalErrors["erroInv"]["rel_5_inv_2"])
    if "rel_1_inv_3" in errosInv:
        fix.rel_1_inv_3_fix(termosIndice,rep.globalErrors["erroInv"]["rel_1_inv_3"])
    if "rel_8_inv_6" in errosInv:
        fix.rel_8_inv_6_fix(classes,rep.globalErrors["erroInv"]["rel_8_inv_6"],invs)
    if "rel_8_inv_7" in errosInv:
        fix.rel_8_inv_7_fix(classes,rep.globalErrors["erroInv"]["rel_8_inv_7"],invs)
    loggerCorr.info("-"*80)
    loggerCorr.info("Correção automática dos erros terminada")
    loggerCorr.info("-"*80)
    rep.dumpReport()
    rep.dumpClasses(classes,dumpFileName="allClassesFixed.json")

    # --------------------------------------------
    # Geração da ontologia final
    # --------------------------------------------

    # A ontologia só é gerada se nenhum erro "grave" for encontrado
    if ok:

        # Reorganização dos dados
        finalClasses = { c:{} for c in rep.classesN1}
        allClasses = {}
        allClasses.update(classes)
        allClasses.update(harmonizacao)
        allClasses.update(outros)
        for cod,proc in allClasses.items():
            # Aqui não faz mal ir buscar o cod desta
            # forma porque não existem erros graves
            codN1 = rep.declaracoes[cod][0].replace('_csv','')
            finalClasses[codN1][cod] = proc

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
