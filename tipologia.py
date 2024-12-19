from itertools import islice
import pandas as pd
import json

import re
brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
sepExtra = re.compile(r'#$|^#')

def processSheet(sheet, nome):
    print("# Migração do Catálogo de Tipologias -------------------")
    # Load one worksheet.
    fnome = nome.split("_")[0]
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
                print("ERRO: Tipologia duplicada --> ", myReg["sigla"])
            
            if row["Designação"]:
                myReg["designacao"] = brancos.sub('', row["Designação"])
            myTipologia.append(myReg)

    outFile = open("./files/tip.json", "w", encoding="utf-8")
    
    json.dump(myTipologia, outFile, indent = 4, ensure_ascii=False)
    print("Tipologias extraídas: ", len(myTipologia))
    outFile.close()
    catalog = open("./files/tipCatalog.json", "w", encoding="utf-8")
    json.dump(tipCatalog, catalog, indent = 4, ensure_ascii=False)
    print("Catálogo de tipologias criado.")
    print("# FIM: Migração do Catálogo de Tipologias -----------------")
    return len(myTipologia)