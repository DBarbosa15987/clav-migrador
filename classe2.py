from itertools import islice
from nanoid import generate
import pandas as pd
import json
import re

import contexto
import decisao
from report import Report

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
def calcEstado(e):
    global hreg, ireg
    if e.strip() == '':
        return 'A'
    elif hreg.search(e):
        return 'H'
    elif ireg.search(e):
        return 'I'
    else:
        # TODO: criar erro aqui?
        return 'Erro'
# --------------------------------------------------
#
# Calcula o nível da classe
def calcNivel(cod):
    res = 0
    if n4.fullmatch(cod):
        res = 4
    elif n3.fullmatch(cod):
        res = 3
    elif n2.fullmatch(cod):
        res = 2
    elif n1.fullmatch(cod):
        res = 1
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
def calcSubdivisoes(df):
    indN3 = {}
    for index, row in df.iterrows():
        if row["Código"]:
            # Código -----
            codigo = re.sub(r'(\r\n|\n|\r|[ \u202F\u00A0])','', str(row["Código"]))
            # Nível -----
            nivel = calcNivel(codigo)
            if nivel == 3:
                indN3[codigo] = False
            elif nivel == 4:
                pai = re.search(r'^(\d{3}\.\d{1,3}\.\d{1,3})\.\d{1,4}$', codigo).group(1)
                indN3[pai] = True
    return indN3

def processSheet(sheet, nome,rep:Report):
    # Carregam-se os catálogos
    # --------------------------------------------------
    ecatalog = open('./files/entCatalog.json')
    tcatalog = open('./files/tipCatalog.json')
    lcatalog = open('./files/legCatalog.json')
    entCatalog = json.load(ecatalog)
    tipCatalog = json.load(tcatalog)
    legCatalog = json.load(lcatalog)

    # Load one worksheet.
    # --------------------------------------------------
    fnome = nome.split("_")[0]
    print("# Migração da Classe  " + fnome + "----------------------")
    ws = sheet
    data = ws.values
    cols = next(data)[0:]
    data = list(data)
    idx = list(range(len(data)))
    data = (islice(r, 0, None) for r in data)
    df = pd.DataFrame(data, index=idx, columns=cols)

    myClasse = {}
    warningsDic = {}
    ProcHarmonizacao = []
    indN3 = calcSubdivisoes(df)

    for _, row in df.iterrows():
        myReg = {}
        if row["Código"]:
            # Código -----
            cod = re.sub(r'(\r\n|\n|\r|[ \u202F\u00A0])','', str(row["Código"]))
            # Nível -----
            myReg["nivel"] = calcNivel(cod)
            # Estado -----
            if row["Estado"]:
                myReg["estado"] = calcEstado(row["Estado"])
            else:
                myReg["estado"] = 'A'
            # Título -----
            if row["Título"]:
                myReg["titulo"] = brancos.sub('', row["Título"])
            else:
                if myReg["estado"] != 'H':
                    rep.addErro(cod,"Classe sem título")

            # Descrição -----
            myReg["descricao"] = norm_brancos.sub(' ', str(row["Descrição"]))
            # Notas de aplicação -----
            if row["Notas de aplicação"]:
                myReg["notasAp"] = procNotas(row["Notas de aplicação"], cod)
            # Exemplos de notas de aplicação -----
            if row["Exemplos de NA"]:
                myReg["exemplosNotasAp"] = procNotas(row["Exemplos de NA"], cod, 'idExemplo', 'exemplo')
            # Notas de exclusão -----
            if row["Notas de exclusão"]:
                myReg["notasEx"] = procNotas(row["Notas de exclusão"], cod)

            # Processamento do Contexto para classes de nível 3
            if myReg["nivel"] == 3:
                contexto.procContexto(row,cod, myReg, warningsDic, entCatalog, tipCatalog, legCatalog,rep)

            # Processamento das Decisões
            if (myReg["nivel"] == 3 and not indN3[cod]) or myReg["nivel"] == 4:
                decisao.procDecisoes(row,cod, myReg, legCatalog,rep)

            if myReg["estado"] == 'H' and cod not in warningsDic:
                ProcHarmonizacao.append(cod)

            rep.addDecl(cod,nome)
            myClasse[cod] = myReg

    outFile = open("./files/"+fnome+".json", "w", encoding="utf-8")

    json.dump(myClasse, outFile, indent = 4, ensure_ascii=False)
    print("Classe extraída: ", nome, " :: ", len(myClasse))
    if len(warningsDic) > 0:
        print("Warnigns: ")
        print('\n'.join(warningsDic.values()))
    if len(ProcHarmonizacao) > 0:
        print("Processos em Harmonização: ")
        print('\n'.join(ProcHarmonizacao))
    outFile.close()
    print("# FIM: Migração da Classe  " + fnome + "-----------------")