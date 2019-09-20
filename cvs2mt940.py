import sys
import re

if len(sys.argv) == 1:
    print("usage: csv2mt940 input.cvs output.mt940")
    exit()

csvFile   = open(sys.argv[1], 'r', encoding='latin-1')
mt940File = open(sys.argv[2], 'w', encoding='latin-1')

lineNumber = 1
for line in csvFile:
    # skip header:
    if lineNumber < 12:
        lineNumber = lineNumber + 1
        continue
    line = line.rstrip()
    # skip footer
    if line == "\"* noch nicht ausgeführte Umsätze\"":
        continue
    # split into array
    line = line[1:-1]
    array = line.split("\";\"")
    
    dateBuchung    = array[0]
    yearBuchung    = dateBuchung[8:10]
    monthBuchung   = dateBuchung[3:5]
    dayBuchung     = dateBuchung[0:2]
    dateWertstellung  = array[1]
    yearWertstellung  = dateWertstellung[8:10]
    monthWertstellung = dateWertstellung[3:5]
    dayWertstellung   = dateWertstellung[0:2]
    comment = array[2]

    # nummer = extract BIC und IBAN, ab KREF+:
    nummer = ""
    mo = re.search( "K\s?R\s?E\s?F\s?\+ [\w\s]*" , comment)
    if mo: 
        nummer = comment[mo.start():mo.end()]
        mo = re.search("\+[\w\s]*", nummer)
        nummer = nummer[mo.start()+1:mo.end()]
        if nummer[0] == " ":
            nummer = nummer[1:]
        nummer = nummer.replace(" ","")
        
    amount  = (array[3])
    amountTyp = "C"     # Credit
    if amount[0] == "-":
        amount = amount[1:]
        amountTyp = "D" # Debit
    amount = amount.replace(".","") # remove thousand-points
    
    # write to file
    mt940File.write(":25:"+nummer+"\n")
    mt940File.write(":61:"+yearWertstellung+monthWertstellung+dayWertstellung+monthBuchung+dayBuchung+amountTyp+"R"+amount+"Nxxx"+nummer+"\n")
    mt940File.write(":86:"+comment+"\n")
    mt940File.write("\n")
