import os
from numpy import nan
from openpyxl import load_workbook
from . import classe2 as c
from . import tindice as ti
from . import entidade as e
from . import tipologia as tip
from . import leg
from .report import Report
from path_utils import FILES_DIR
import json

def excel2json(rep: Report,filename):

    sheets = ['100_csv','150_csv','200_csv','250_csv','300_csv','350_csv','400_csv','450_csv','500_csv','550_csv','600_csv',
                '650_csv','700_csv','710_csv','750_csv','800_csv','850_csv','900_csv','950_csv']

    # Leitura do Excel
    wb = load_workbook(filename)

    ti.processSheet(wb['ti_csv'], 'ti_csv')
    e.processSheet(wb['ent_sioe_csv'], rep)
    tip.processSheet(wb['tip_ent_csv'], rep)
    leg.processSheet(wb['leg_csv'], 'leg_csv',rep)

    classesN1 = {}
    for s in sheets:
        c.processSheet(wb[s], s, rep, classesN1)

    # Registo das classes de nível 1 para futuro agrupamento
    with open(os.path.join(FILES_DIR,'classesN1.json'),'w') as f:
        json.dump(classesN1,f,indent=4,ensure_ascii=False)

    return classesN1
