from .excel2json import excel2json
from . import checkInvariantes as c
from .report import Report
from . import genTTL as g
import json
import os
from . import queryfix as fix
from path_utils import FILES_DIR
import logging
from log_utils import FIX, GEN, INV, PROC

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

    loggerProc.info("Verificação da estrutura dos dados")
    ok = rep.checkStruct()

    # Inferências de relações
    loggerProc.info("Inferências de relações")
    rep.fixMissingRels(allClasses)

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

    c.rel_4_inv_2(allClasses,rep)
    c.rel_4_inv_3(allClasses,rep)
    c.rel_4_inv_4(allClasses,rep)
    c.rel_4_inv_12(allClasses,rep)
    c.rel_4_inv_13(allClasses,rep)
    c.rel_5_inv_1(allClasses,rep)
    c.rel_5_inv_3(allClasses,rep)
    c.rel_3_inv_4(allClasses,termosIndice,rep)
    c.rel_7_inv_2(allClasses,rep)
    c.rel_4_inv_0(allClasses,rep)
    c.rel_7_inv_3(allClasses,rep)
    c.rel_6_inv_4(allClasses,rep)
    c.rel_6_inv_3(allClasses,rep)
    c.rel_3_inv_3(allClasses,rep)
    c.rel_3_inv_1(allClasses,rep)
    c.rel_3_inv_5(allClasses,rep)
    c.rel_4_inv_5(allClasses,rep)
    c.rel_4_inv_6(allClasses,rep)
    c.rel_4_inv_11(allClasses,rep)
    c.rel_3_inv_6(allClasses,rep)
    c.rel_9_inv_2(allClasses,rep)
    c.rel_6_inv_2(allClasses,rep)
    c.rel_3_inv_7(allClasses,rep)
    c.rel_6_inv_1(allClasses,rep)
    c.rel_4_inv_7(allClasses,rep)
    c.rel_5_inv_2(allClasses,rep)
    c.rel_4_inv_8(allClasses,rep)
    c.rel_4_inv_1_0(allClasses,rep)
    c.rel_4_inv_14(allClasses,rep)
    c.rel_8_inv_1(allClasses,rep)
    c.rel_3_inv_9(allClasses,harmonizacao,rep)

    c.rel_9_inv_4(allClasses,rep)
    c.rel_9_inv_5(allClasses,rep)
    c.rel_9_inv_6(allClasses,rep)
    c.rel_9_inv_7(allClasses,rep)
    c.rel_10_inv_1(allClasses,rep)
    c.rel_8_inv_2(allClasses,rep)

    c.checkUniqueInst(allClasses,rep)

    loggerInv.info("-"*80)
    loggerInv.info("Verificação dos invariantes terminada")
    loggerInv.info("-"*80)

    # --------------------------------------------
    # Correções
    # --------------------------------------------

    rep.dumpReport()
    loggerCorr.info("-"*80)
    loggerCorr.info("Correção automática dos erros")
    loggerCorr.info("-"*80)
    fix.rel_4_inv_12_fix(allClasses,rep.globalErrors["erroInv"]["rel_4_inv_12"])
    fix.rel_4_inv_13_fix(allClasses,rep.globalErrors["erroInv"]["rel_4_inv_13"])
    fix.rel_5_inv_2_fix(allClasses,rep.globalErrors["erroInv"]["rel_5_inv_2"])
    fix.rel_6_inv_4_fix(allClasses,rep.globalErrors["erroInv"]["rel_6_inv_4"])
    fix.rel_7_inv_3_fix(allClasses,rep.globalErrors["erroInv"]["rel_7_inv_3"])
    loggerCorr.info("-"*80)
    loggerCorr.info("Correção automática dos erros terminada")
    loggerCorr.info("-"*80)
    rep.dumpReport(dumpFileName="dump-fixed.json")

    # --------------------------------------------
    # Geração da ontologia final
    # --------------------------------------------

    # A ontologia só é gerada se nenhum erro "grave" for encontrado
    if ok:
        loggerGen.info("-"*80)
        loggerGen.info("Geração dos ficheiros de ontologia")
        loggerGen.info("-"*80)

        g.tiGenTTL()
        g.entidadeGenTTL()
        g.tipologiaGenTTL()
        g.legGenTTL()

        classes = ['100','150','200','250','300','350','400','450','500','550','600',
                    '650','700','710','750','800','850','900','950']
        for classe in classes:
            g.classeGenTTL(classe)

        loggerGen.info("-"*80)
        loggerGen.info("Geração dos ficheiros de ontologia terminada")
        loggerGen.info("-"*80)
    else:
        loggerGen.info("-"*80)
        loggerGen.warning("Ontologia não foi criada devido à existência de erros graves")
        loggerGen.info("-"*80)

    return rep,ok

