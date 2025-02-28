from excel2json import excel2json
from checkInvariantes import *
from report import Report
from genTTL import *
import sys

rep = Report()

# --------------------------------------------
# Criação dos ficheiros JSON intermédios
# --------------------------------------------

print("\nCriação dos ficheiros JSON intermédios\n")
excel2json(rep)

# --------------------------------------------
# Processamento inicial dos dados
# --------------------------------------------

print("\nProcessamento inicial dos dados\n")

allClasses,harmonizacao = processClasses(rep)
ok = rep.checkStruct()

if not ok:
    rep.fixMissingRels(allClasses)

# --------------------------------------------
# Verificação dos invariantes
# --------------------------------------------

print("\nVerificação dos invariantes\n")

with open("files/ti.json",'r') as f:
    termosIndice = json.load(f)

rel_4_inv_2(allClasses,harmonizacao,rep)
rel_4_inv_3(allClasses,harmonizacao,rep)
rel_4_inv_4(allClasses,harmonizacao,rep)
rel_4_inv_12(allClasses,rep)
rel_4_inv_13(allClasses,rep)
rel_5_inv_1(allClasses,rep)
rel_5_inv_3(allClasses,rep)
rel_3_inv_4(allClasses,termosIndice,rep)
rel_7_inv_2(allClasses,rep)
rel_4_inv_0(allClasses,rep)
rel_7_inv_3(allClasses,rep)
rel_6_inv_4(allClasses,rep)
rel_9_inv_3(allClasses,rep)
rel_6_inv_3(allClasses,rep)
rel_3_inv_3(allClasses,rep)
rel_3_inv_1(allClasses,rep)
rel_3_inv_5(allClasses,rep)
rel_4_inv_5(allClasses,harmonizacao,rep)
rel_4_inv_6(allClasses,harmonizacao,rep)
rel_4_inv_11(allClasses,rep)
rel_3_inv_6(allClasses,rep)
rel_9_inv_2(allClasses,rep)
rel_6_inv_2(allClasses,rep)
rel_3_inv_7(allClasses,rep)
rel_6_inv_1(allClasses,rep)
rel_4_inv_7(allClasses,rep)
rel_5_inv_2(allClasses,rep)
rel_4_inv_8(allClasses,rep)
rel_4_inv_1_0(allClasses,rep)
rel_4_inv_13(allClasses,rep)
rel_8_inv_1(allClasses,rep)

checkUniqueInst(rep)

rep.printInv()
rep.dumpReport()

# --------------------------------------------
# Geração da ontologia final
# --------------------------------------------

print("\nGeração da ontologia final\n")

tiGenTTL()
entidadeGenTTL()
tipologiaGenTTL()
legGenTTL()

classes = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']
for c in classes:
    print('Classe: ', c)
    classeGenTTL(c)
