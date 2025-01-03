from numpy import nan
from openpyxl import load_workbook
import classe2 as c
import tindice as ti
import entidade as e
import tipologia as tip
import leg

data_file = 'Frecolha-20241007.xlsx'
sheets = ['100_csv','150_csv','200_csv','250_csv','300_csv','350_csv','400_csv','450_csv','500_csv','550_csv','600_csv',
            '650_csv','700_csv','710_csv','750_csv','800_csv','850_csv','900_csv','950_csv']

backsheets = ['ti_csv','leg_csv','ent_sioe_csv','tip_ent_csv']

# Leitura do Excel
wb = load_workbook(data_file)

ti.processSheet(wb['ti_csv'], 'ti_csv')
e.processSheet(wb['ent_sioe_csv'], 'ent_sioe_csv')
tip.processSheet(wb['tip_ent_csv'], 'tip_ent_csv')
leg.processSheet(wb['leg_csv'], 'leg_csv')

for s in sheets:
    c.processSheet(wb[s], s)

