# -*- coding: utf-8 -*-
import re
import time

import xlwt
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

wb = xlwt.Workbook()
ws = wb.add_sheet('test')


def add(row, line, value):
    ws.write(line, row, value)
    wb.save('test.xls')


driver = webdriver.Chrome(
    '/home/geroge/Documents/Work/Wod_parser/exercices/chromedriver')


class ExerciceLink():
    """docstring for ExerciceLink"""

    def __init__(self, link, line):
        self.link = link
        self.line = line

    def parseEx(self):
        driver.get('https://wodcat.com/exercises/' + self.link)
        time.sleep(2)
        rus_name = driver.find_element_by_class_name('main-header')
        add(0, self.line, rus_name.text)
        en_name = re.sub('-', ' ', self.link)
        add(1, self.line, en_name)
        descr = driver.find_element_by_class_name(
            'task-section__training-description')
        if descr:
            descr = descr.text
        else:
            descr = 'Null'
        add(2, self.line, descr)
        y_link = re.findall('https://www.youtube.com/embed/\w+',
                            driver.find_element_by_tag_name('body').get_attribute('innerHTML'))
        if y_link:
            y_link = y_link[0]
        else:
            y_link = 'Null'
        add(3, self.line, y_link)
        inventory = driver.find_element_by_class_name(
            'task-section__training-duration')
        if inventory:
            inventory = inventory.text
        else:
            inventory = 'Null'
        add(4, self.line, inventory)


driver.get('https://wodcat.com/exercises/')
time.sleep(5)

elements = driver.find_elements_by_class_name('ng-scope')
element = elements[0]
for i in range(20):
    element.send_keys(Keys.PAGE_DOWN)
    time.sleep(2)

element = driver.find_element_by_tag_name('body')
text = element.get_attribute('innerHTML')

links = re.findall('href="exercises/.+" d', text)
i = 1
for link in links:
    a = ExerciceLink(link[16:-3], i)
    a.parseEx()
    print(1)
    i += 1
