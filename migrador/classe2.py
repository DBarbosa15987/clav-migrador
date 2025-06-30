from itertools import islice
import logging
from nanoid import generate
import pandas as pd
import json
import re
from . import contexto
from . import decisao
from .report import Report
import os
from path_utils import FILES_DIR
from log_utils import PROC

hreg = re.compile(r'[hH][aA][rR][mM][oO]?[nN]?')
ireg = re.compile(r'[iI][nN][Aa][tT]?[iI]?[vV]?')
n4 = re.compile(r'^\d{3}\.\d{1,3}\.\d{1,3}\.\d{1,4}$')
n3 = re.compile(r'^\d{3}\.\d{1,3}\.\d{1,3}$')
n2 = re.compile(r'^\d{3}\.\d{1,3}$')
n1 = re.compile(r'^\d{3}$')

brancos = re.compile(r'\r\n|\n|\r|[ \u202F\u00A0]+$|^[ \u202F\u00A0]+')
norm_brancos = re.compile(r'(\r\n|\n|\r|[ \u202F\u00A0])+')
sepExtra = re.compile(r'#$|^#')

# Calcula e normaliza o estado da classe
def calcEstado(cod,e,rep:Report):
    global hreg, ireg
    if e.strip() == '':
        return 'A'
    elif hreg.search(e):
        return 'H'
    elif ireg.search(e):
        return 'I'
    else:
        # ERRO: O estado da classe inválido
        rep.addErro(cod,f"O estado da classe inválido ({e})")
        return 'Erro'
# --------------------------------------------------
#
# Calcula o nível da classe
def calcNivel(cod,rep:Report):
    res = 0
    if n4.fullmatch(cod):
        res = 4
    elif n3.fullmatch(cod):
        res = 3
    elif n2.fullmatch(cod):
        res = 2
    elif n1.fullmatch(cod):
        res = 1
    else:
        # ERRO: O formato do código é inválido
        rep.addErro(cod,f"O formato do código \"{cod}\" é inválido")
    return res
# --------------------------------------------------
#
# Processa as notas de aplicação

def procNotas(notas, codClasse, chave1=None, chave2=None):
    res = []
    if not chave1:
        chave1 = 'idNota'
    if not chave2:
        chave2 = 'nota'
    notas = brancos.sub('', notas)
    notas = sepExtra.sub('', notas)
    filtradas = notas.split('#')
    for na in filtradas:
        res.append({
            chave1: chave2 + '_' + codClasse + '_' + generate('1234567890abcdef', 12),
            chave2: na
        })
    return res
# --------------------------------------------------
#
# Calcula um array de booleanos para as N3 com subdivisão
def calcSubdivisoes(df,rep:Report):
    indN3 = {}
    for index, row in df.iterrows():
        if row["Código"]:
            # Código -----
            codigo = re.sub(r'(\r\n|\n|\r|[ \u202F\u00A0])','', str(row["Código"]))
            # Nível -----
            nivel = calcNivel(codigo,rep)
            if nivel == 3:
                indN3[codigo] = False
            elif nivel == 4:
                pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', codigo).group(1)
                indN3[pai] = True
    return indN3

def processSheet(sheet, nome, rep:Report, classesN1):

    loggerProc = logging.getLogger(PROC)
    # Carregam-se os catálogos
    # --------------------------------------------------
    ecatalog = open(os.path.join(FILES_DIR,'entCatalog.json'))
    tcatalog = open(os.path.join(FILES_DIR,'tipCatalog.json'))
    lcatalog = open(os.path.join(FILES_DIR,'legCatalog.json'))
    entCatalog = json.load(ecatalog)
    tipCatalog = json.load(tcatalog)
    legCatalog = json.load(lcatalog)

    # Load one worksheet.
    # --------------------------------------------------
    fnome = nome.split("_")[0]
    loggerProc.info("# Migração da Classe  " + fnome + "----------------------")
    ws = sheet
    data = ws.values
    cols = next(data)[0:]
    data = list(data)
    idx = list(range(len(data)))
    data = (islice(r, 0, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)

    myClasse = {}
    indN3 = calcSubdivisoes(df,rep)

    for _, row in df.iterrows():
        myReg = {}
        if row["Código"]:
            # Código -----
            cod = re.sub(r'(\r\n|\n|\r|[ \u202F\u00A0])','', str(row["Código"]))
            # Nível -----
            myReg["nivel"] = calcNivel(cod,rep)
            # Estado -----
            if row["Estado"]:
                myReg["estado"] = calcEstado(cod,row["Estado"],rep)
            else:
                myReg["estado"] = 'A'
            # Título -----
            if row["Título"]:
                myReg["titulo"] = brancos.sub('', row["Título"])
            else:
                if myReg["estado"] != 'H':
                    rep.addErro(cod,"Classe sem título")

            # Descrição -----
            if row["Descrição"]:
                myReg["descricao"] = norm_brancos.sub(' ', str(row["Descrição"]))
            else:
                myReg["descricao"] = ""
            # Notas de aplicação -----
            if row["Notas de aplicação"]:
                myReg["notasAp"] = procNotas(row["Notas de aplicação"], cod)
            # Exemplos de notas de aplicação -----
            if row["Exemplos de NA"]:
                myReg["exemplosNotasAp"] = procNotas(row["Exemplos de NA"], cod, 'idExemplo', 'exemplo')
            # Notas de exclusão -----
            if row["Notas de exclusão"]:
                myReg["notasEx"] = procNotas(row["Notas de exclusão"], cod)

            # Registo das classes de nível 1
            if myReg["nivel"] == 1:
                classesN1[cod] = {
                    "titulo": myReg.get("titulo",""),
                    "descricao": myReg["descricao"]
                }
            # Processamento do Contexto para classes de nível 3
            if myReg["nivel"] == 3:
                contexto.procContexto(row,cod, myReg, entCatalog, tipCatalog, legCatalog,rep)

            # Processamento das Decisões
            if (myReg["nivel"] == 3 and not indN3[cod]) or myReg["nivel"] == 4:
                decisao.procDecisoes(row,cod, myReg, legCatalog,rep)

            rep.addDecl(cod,nome)
            myClasse[cod] = myReg

    outFilePath = os.path.join(FILES_DIR,f"{fnome}.json")
    outFile = open(outFilePath, "w", encoding="utf-8")

    json.dump(myClasse, outFile, indent = 4, ensure_ascii=False)
    loggerProc.info("Classe extraída: ", nome, " :: ", len(myClasse))
    outFile.close()
    loggerProc.info("# FIM: Migração da Classe  " + fnome + "-----------------")