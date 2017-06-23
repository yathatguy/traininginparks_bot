# -*- coding: utf-8 -*-
import re

import requests
import xlwt

wb = xlwt.Workbook()
ws = wb.add_sheet('test')


def add(row, line, value):
    ws.write(line, row, value)
    wb.save('test.xls')


# Парсим тренировки


class TrainLink():
    """docstring for TrainLink"""

    def __init__(self, link, line, name):
        self.link = link
        self.line = line
        self.name = name

    def parseTrain(self):
        globaLink = 'https://wodcat.com/'
        page = requests.get(globaLink + self.link)
        add(0, self.line, self.name)
        # Парсим modality
        modalityPattern = 'task-section__info-logo">\w+<'
        if re.findall(modalityPattern, page.text):
            modality = re.findall(modalityPattern, page.text)[0][25:-1]
            modality = ','.join(list(modality))
        else:
            modality = 'Null'
        add(1, self.line, modality)
        # Парсим упражения
        descrPrefix = 'task-section__info-item">[\w, ", \n, \-, \%, :, /]+</li'
        description = ''
        if re.findall(descrPrefix, page.text):
            a = re.findall(descrPrefix, page.text)
            i = 0
            repeats = []
            names = []
            weights = []
            addCur = False
            for b in a:
                if re.findall('>.+<', re.sub('\s{2,}', '', b)):
                    ex = re.findall('>.+<', re.sub('\s{2,}', '', b))[0][1:-1]
                    if len(re.findall('\d+', ex)) == 0:
                        repeats.append('-')
                        weights.append('-')
                        names.append(ex)
                    if len(re.findall('\d+', ex)) == 1:
                        repeats.append(re.findall('\d+', ex)[0])
                        weights.append('-')
                        names.append(re.sub(repeats[-1], '', ex))
                    if len(re.findall('\d+', ex)) >= 2:
                        repeats.append(re.findall('\d+', ex)[0])
                        if re.findall('lb', ex.lower()):
                            weights.append(re.findall('\d+', ex)[1])
                            name = re.sub(re.findall('\d+', ex)[0], '', ex)
                            name = re.sub('lbs*', '', name)
                            names.append(
                                re.sub(re.findall('\d+', ex)[1], '', name))
                        else:
                            weights.append('-')
                            names.append(
                                re.sub(re.findall('\d+', ex)[0], '', ex))
                    description += ex + "\n"
                    if i == 0:
                        if re.findall(':', ex):
                            add(2, self.line, ex)
                        else:
                            add(2, self.line, '-')
                            addCur = True
                    i += 1
            if addCur:
                toAdd3 = ''
                for repeat in repeats:
                    toAdd3 += repeat + "\n"
                add(3, self.line, toAdd3)
                toAdd4 = ''
                for name in names:
                    toAdd4 += name + "\n"
                add(4, self.line, toAdd4)
                toAdd5 = ''
                for weight in weights:
                    toAdd5 += weight + "\n"
                add(5, self.line, toAdd5)
            else:
                toAdd3 = ''
                for repeat in repeats[1:]:
                    toAdd3 += repeat + "\n"
                add(3, self.line, toAdd3)
                toAdd4 = ''
                for name in names[1:]:
                    toAdd4 += name + "\n"
                add(4, self.line, toAdd4)
                toAdd5 = ''
                for weight in weights[1:]:
                    toAdd5 += weight + "\n"
                add(5, self.line, toAdd5)
            print(repeats, names, weights)

        # Парсим снаряжение
        inventoryPattern = 'product-list__item-title">[\w, -]+<'
        inv = re.findall(inventoryPattern, page.text)
        inventory = ""
        for item in inv:
            inventory += item[26:-1] + ','
        if not inventory:
            inventory = 'Null'
        add(6, self.line, inventory)
        # Парсим mode
        modePattern = 'task-section__training-type">.+<'
        modes = re.findall(modePattern, page.text)
        mode = ''
        if modes:
            mode += modes[0][29:-1]
        if not mode:
            mode = 'Null'
        add(7, self.line, mode)


class Trains():
    """docstring for Trains"""

    def __init__(self, firstLink):
        self.firstLink = firstLink

    def getHtmls(self):
        # Смотрим, сколько страниц
        pattern = '/wod/\?page=\d+'
        numbers = requests.get(self.firstLink)
        num = re.findall(pattern, numbers.text)[-1]
        num = int(re.findall('\d+', num)[0])
        # Перебираем все страницы
        add = '?page='
        j = 1
        for i in range(1, num):
            link = self.firstLink + add + str(i)
            page = requests.get(link)
            trainLinks = re.findall('href="wod/[\w, -]+">.+</a>', page.text)
            for trainLink in trainLinks:
                trainName = re.findall('>.+<', trainLink)[0][1:-1]
                trainLink = re.findall('href="wod/.+">', trainLink)[0][6:-2]
                train = TrainLink(trainLink, j, trainName)
                train.parseTrain()
                j += 1


a = Trains('https://wodcat.com/wod/')
a.getHtmls()
