import xlwt

wb = xlwt.Workbook()
ws = wb.add_sheet('test')


def add(row, line, value):
    ws.write(line, row, value)
    wb.save('test.xls')
