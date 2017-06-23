# -*- coding: utf-8 -*-

import sys

import pymongo
import xlrd

reload(sys)
sys.setdefaultencoding('utf-8')

# connection = pymongo.MongoClient(os.environ['MONGODB_URI'])
# db = connection["heroku_r261ww1k"]

connection = pymongo.MongoClient()
db = connection["wod"]

addArray = []

# rb = xlrd.open_workbook('data/train_example.xlsx', encoding_override="utf_16_le")
rb = xlrd.open_workbook('train_example.xlsx', encoding_override="utf_16_le")
sheet = rb.sheet_by_index(0)

for rowNum in range(sheet.nrows):
    row = sheet.row_values(rowNum)
    toAdd = {}
    toAdd['name'] = row[0]
    toAdd['modality'] = row[1].split(',')
    toAdd['description'] = row[2]
    exces = []
    if len(str(row[3]).split("\n")) == len(str(row[4]).split("\n")) == len(str(row[5]).split("\n")):
        for i in range(len(str(row[3]).split("\n"))):
            if len(str(row[5]).split("\n")[i].split('/')) > 1:
                weights = {
                    'men': row[5].split("\n")[i].split('/')[0],
                    'women': row[5].split("\n")[i].split('/')[1]
                }
            else:
                weights = row[5].split("\n")[i]
            exces.append({
                'reps': str(row[3]).split("\n")[i],
                'movements': row[4].split("\n")[i],
                'weights': weights
            })
    toAdd['exces'] = exces
    if row[6] == 'Null':
        toAdd['inventory'] = None
    else:
        toAdd['inventory'] = row[6].split(',')
    toAdd['mode'] = row[7]
    addArray.append(toAdd)
print(addArray)
result = db.wod.insert_many(addArray)
