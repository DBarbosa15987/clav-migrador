from excel2json import excel2json
import checkInvariantes as c
from report import Report
import genTTL as g
import json

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

allClasses,harmonizacao = c.processClasses(rep)
# TODO: Falta decidir exatamente o que fazer de acordo com o output da função
ok = rep.checkStruct()

rep.fixMissingRels(allClasses)

# --------------------------------------------
# Verificação dos invariantes
# --------------------------------------------

print("\nVerificação dos invariantes\n")

with open("files/ti.json",'r') as f:
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
c.rel_9_inv_3(allClasses,rep)
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

c.checkUniqueInst(allClasses,rep)

# TODO: Aqui seriam adicionadas as "queryfix" possíveis

rep.printInv()
rep.dumpReport()

# --------------------------------------------
# Geração da ontologia final
# --------------------------------------------

print("\nGeração da ontologia final\n")

g.tiGenTTL()
g.entidadeGenTTL()
g.tipologiaGenTTL()
g.legGenTTL()

classes = ['100','150','200','250','300','350','400','450','500','550','600',
            '650','700','710','750','800','850','900','950']
for classe in classes:
    print('Classe: ', classe)
    g.classeGenTTL(classe)
