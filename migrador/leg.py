from itertools import islice
import pandas as pd
import json
from datetime import datetime
import re
import os
from path_utils import FILES_DIR
from .report import Report

brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
sepExtra = re.compile(r'#$|^#')

def processSheet(sheet, nome, rep: Report):
    print("# Migração do Catálogo Legislativo ---------------------------")
    # Carregam-se os catálogos de entidades e tipologias
    # --------------------------------------------------
    ecatalog = open(os.path.join(FILES_DIR, "entCatalog.json"))
    tcatalog = open(os.path.join(FILES_DIR, "tipCatalog.json"))
    entCatalog = json.load(ecatalog)
    tipCatalog = json.load(tcatalog)
    # Load one worksheet.
    fnome = nome.split("_")[0]
    ws = sheet
    data = ws.values
    cols = next(data)[0:]
    data = list(data)
    idx = list(range(len(data)))
    data = (islice(r, 0, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)

    legCatalog = []
    myLeg = []
    for index, row in df.iterrows():
        myReg = {}
        if row["Tipo"] and str(row["Tipo"]) != 'NaT':
            # Tipo: ------------------------------------------------------
            limpa = brancos.sub('', str(row["Tipo"]))
            myReg["tipo"] = re.sub(r'[/ \u202F\u00A0()\-]+', '_', limpa)
            # Número: ----------------------------------------------------
            if row["Número"] and row["Número"] != '':
                myReg["numero"] = brancos.sub('', str(row["Número"]))
                myReg["numero"] = re.sub(r'[/ \u202F\u00A0()\-\u2010]+', '_', myReg["numero"])

            else:
                rep.addWarning("",f"legindex {str(index+2)}::Legislação sem número")
                myReg["numero"] = 'NE'
            # Entidades:--------------------------------------------------
            filtradas = []
            if row["Entidade"]:
                entidades = brancos.sub('', str(row["Entidade"])).split(',')
                filtradas = list(filter(lambda e: e != '' and e != 'NaT', entidades))
                if len(filtradas)> 0:
                    myReg["entidade"] = []
                    for e in filtradas:
                        limpa = brancos.sub('', e)
                        limpa = re.sub(r'[/ \u202F\u00A0()]+', '_', limpa)
                        myReg["entidade"].append(limpa)
            if len(filtradas)> 0:
            # Cálculo do id/código da legislação: tipo + entidades + numero -------------------------
                legCod = re.sub(r'[ ]+', '_', myReg["tipo"]) + '_' + '_'.join(myReg["entidade"])
            # ERRO: Verificação da existência das entidades no catálogo de entidades e/ou tipologias
                for e in myReg['entidade']:
                    if (e not in entCatalog) and (e not in tipCatalog):
                        rep.addErro("",f"{legCod}::Entidade não está no catálogo de entidades ou tipologias::{e}")
            else:
                legCod = re.sub(r'[ \u202F\u00A0]+', '_', myReg["tipo"])
            if myReg["numero"] != 'NE':
                legCod += '_' + myReg["numero"]
            # ERRO: Legislação duplicada ---------------------------------
            myReg['codigo'] = legCod
            if legCod not in legCatalog:
                legCatalog.append(legCod)
            else:
                rep.addErro("",f"{legCod}::Legislação duplicada::{str(index)}.")
            # Estado: ----------------------------------------------------
            if row['Estado'] and str(row['Estado']).strip() != "":
                myReg["estado"] = 'Revogado'
            else:
                myReg["estado"] = 'Ativo'
            # Data:-------------------------------------------------------
            if row["Data"] and (not pd.isnull(row["Data"])):
                if isinstance(row["Data"], str):
                    dataISO = datetime.strptime(row["Data"], '%d/%m/%Y')
                    myReg["data"] = dataISO.isoformat()[:10]
                else:
                    myReg["data"] = row["Data"].isoformat()[:10]
            # Sumário:----------------------------------------------------
            if row["Sumário"]:
                mySum = brancos.sub('', str(row["Sumário"]))
                myReg["sumario"] = mySum
            # Fonte:------------------------------------------------------
            if row["Fonte"]:
                myReg["fonte"] = brancos.sub('', str(row["Fonte"])).strip()
            # Link:-------------------------------------------------------
            if row["Link"]:
                myReg["link"] = brancos.sub('', str(row["Link"])).strip()

            myLeg.append(myReg)

    outFilePath = os.path.join(FILES_DIR, f"{fnome}.json")
    outFile = open(outFilePath, "w", encoding="utf-8")

    json.dump(myLeg, outFile, indent = 4, ensure_ascii=False)
    print("Documentos legislativos extraídos: ", len(myLeg))
    outFile.close()

    catalogPath = os.path.join(FILES_DIR, "legCatalog.json")
    catalog = open(catalogPath, "w", encoding="utf-8")
    json.dump(legCatalog, catalog, indent = 4, ensure_ascii=False)
    print("Catálogo de legislação criado.")
    print("# FIM: Migração do Catálogo Legislativo ----------------------")