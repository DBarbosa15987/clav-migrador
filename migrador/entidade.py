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
    loggerProc.info("# Migração do Catálogo de Entidades ----------------------")
    # Load one worksheet.
    ws = sheet
    data = ws.values
    cols = next(data)[0:]
    data = list(data)
    idx = list(range(len(data)))
    data = (islice(r, 0, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)

    entCatalog = []
    myEntidade = []
    for index, row in df.iterrows():
        myReg = {}
        if row["Sigla"]:
            limpa = brancos.sub('', str(row["Sigla"]))
            myReg["sigla"] = re.sub(r'[ \u202F\u00A0,]+', '_', limpa)
            if myReg["sigla"] not in entCatalog:
                entCatalog.append(myReg["sigla"])
            else:
                rep.addErroNoCod(f"Linha {index}: Entidade duplicada --> <b>{myReg["sigla"]}</b>","entidade")
            if row["Estado"]:
               myReg["estado"] = brancos.sub('', str(row["Estado"]))
            if row["ID SIOE"]:
                myReg["sioe"] = brancos.sub('', str(row["ID SIOE"]))
            if row["Designação"]:
                myReg["designacao"] = brancos.sub('', str(row["Designação"]))
            if row["Tipologia de Entidade"]:
                tipologias = brancos.sub('', str(row["Tipologia de Entidade"]))
                tipologias = sepExtra.sub('', tipologias)
                lista = tipologias.split('#')
                myReg['tipologias'] = []
                for tip in lista:
                    myReg['tipologias'].append(brancos.sub('', tip))
            if row["Internacional"]:
                myReg["internacional"] = brancos.sub('', str(row["Internacional"]))
            else:
                myReg["internacional"] = "Não"
            if row["Data de criação"] and (not pd.isnull(row["Data de criação"])):
                myReg["dataCriacao"] = str(row["Data de criação"].isoformat())[:10]
            if row["Data de extinção"] and (not pd.isnull(row["Data de extinção"])):
                myReg["dataExtincao"] = str(row["Data de extinção"].isoformat())[:10]

            myEntidade.append(myReg)

    outFilePath = os.path.join(FILES_DIR, "ent.json")
    outFile = open(outFilePath, "w", encoding="utf-8")

    json.dump(myEntidade, outFile, indent = 4, ensure_ascii=False)
    loggerProc.info(f"Entidades extraídas: {len(myEntidade)}")
    outFile.close()
    catalogPath = os.path.join(FILES_DIR, "entCatalog.json")
    catalog = open(catalogPath, "w", encoding="utf-8")
    json.dump(entCatalog, catalog, indent = 4, ensure_ascii=False)
    loggerProc.info("Catálogo de entidades criado.")
    loggerProc.info("# FIM: Migração do Catálogo de Entidades -----------------")
    return len(myEntidade)