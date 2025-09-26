from itertools import islice
import logging
import pandas as pd
import json
import re
import os
from path_utils import FILES_DIR
from log_utils import PROC
from .report import Report

brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
sepExtra = re.compile(r'#$|^#')

def processSheet(sheet, rep: Report):
    loggerProc = logging.getLogger(PROC)
    loggerProc.info("# Migração do Catálogo de Tipologias -------------------")
    # Load one worksheet.
    ws = sheet
    data = ws.values
    cols = next(data)[0:]
    data = list(data)
    idx = list(range(len(data)))
    data = (islice(r, 0, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)

    tipCatalog = []
    myTipologia = []
    for index, row in df.iterrows():
        myReg = {}
        if row['Sigla']:
            myReg["sigla"] = brancos.sub('', row['Sigla'])
            if myReg["sigla"] not in tipCatalog:
                tipCatalog.append(myReg["sigla"])
            else:
                rep.addErroNoCod(f"Tipologia duplicada::<b>{myReg["sigla"]}</b>","tipologia")

            if row["Designação"]:
                myReg["designacao"] = brancos.sub('', row["Designação"])
            else:
                rep.addWarning(info={"msg":f"A tipologia <b>{myReg["sigla"]}</b> não tem designação definida."})
            myTipologia.append(myReg)

    outFilePath = os.path.join(FILES_DIR, "tip.json")
    outFile = open(outFilePath, "w", encoding="utf-8")

    json.dump(myTipologia, outFile, indent = 4, ensure_ascii=False)
    loggerProc.info(f"Tipologias extraídas: {len(myTipologia)}")
    outFile.close()
    catalogPath = os.path.join(FILES_DIR, "tipCatalog.json")
    catalog = open(catalogPath, "w", encoding="utf-8")
    json.dump(tipCatalog, catalog, indent = 4, ensure_ascii=False)
    loggerProc.info("Catálogo de tipologias criado.")
    loggerProc.info("# FIM: Migração do Catálogo de Tipologias -----------------")
    return len(myTipologia)