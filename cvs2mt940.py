import sys

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
    
    date    = array[0]
    year    = date[8:10]
    month   = date[3:5]
    day     = date[0:2]
    comment = array[2]
    amount  = (array[3])
    amountTyp = "C"     # Credit
    if amount[0] == "-":
        amount = amount[1:]
        amountTyp = "D" # Debit
    amount = amount.replace(".","") # remove thousand-points
    
    # debugging:
    #print(date)
    #print(comment)
    #print(amount)
    #print("----")
    
    # write to file
    mt940File.write(":61:"+year+month+day+month+day+amountTyp+"R"+amount+"NOREF"+"\n")
    mt940File.write(":86:"+comment+"\n")
    mt940File.write("\n")
