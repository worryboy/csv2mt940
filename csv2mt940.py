#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
import datetime
import io

if len(sys.argv) == 1:
    print("usage: csv2mt940 input.csv output.mt940.sta")
    exit()

# TopCard delivers a CSV as iso but this includes utf chars
csvFile   = open(sys.argv[1], 'r', encoding='iso-8859-1')
mt940File = io.open(sys.argv[2], 'w', encoding='utf-8')

now = datetime.datetime.now()

lineNumber = 0
idBodyArray = 0
BodyArray = []
Headder = ""
Body = ""
print("----- > Start processing ") # info output 

for line in csvFile:
    # skip header:
    lineNumber = lineNumber + 1
    if lineNumber < 3:
        #print("skip") #skip line        
        continue
    line = line.rstrip()
    # skip empty
    if line == "":
        #print("skip") #skip line
        continue 
    
    # skip footer
    if line.startswith(";;;;Total"):
        #print("skip") #skip line
        continue  
    #line = line[1:-1] #  remove last char
    array = line.split(";")
    #debug 
    #print("The Linenumber		is: ", lineNumber) #printing the array 
    #print("The Array dateBuchung			is: ", array[3]) #printing the array    
    #print("The Array dateWertstellung		is: ", array[12]) #printing the array
    #print("The Array comment			is: ", array[4]) #printing the array
    #print("The Array nummer			is: ", array[1]) #printing the array        
    #print("The Array Value 10		is: ", array[10]) #printing the array 
    #print("The Array Value 11		is: ", array[11]) #printing the array 
        
    dateBuchung    = array[12]
    yearBuchung    = dateBuchung[8:10]
    monthBuchung   = dateBuchung[3:5]
    dayBuchung     = dateBuchung[0:2]
    dateWertstellung  = array[3]
    yearWertstellung  = dateWertstellung[8:10]
    monthWertstellung = dateWertstellung[3:5]
    dayWertstellung   = dateWertstellung[0:2]
    comment = array[4]
    comment = (re.sub("(.{25})", "\\1\r\n", comment, 0, re.DOTALL))
    commentList = comment.split("\r\n")
    commentListLen = len(commentList)
    for i in range(0,commentListLen,+1):
    	#remove double spaces
    	commentList[i] = " ".join(commentList[i].split())
    	#each row must have 26 chars
    	commentList[i] = commentList[i].ljust(27)
    comment = "\r\n".join(commentList)

    tag = array[5]
    tagList = tag.split(",")
    tagListLen = len(tagList)
    for i in range(0,tagListLen,+1):
    	#remove double spaces
    	tagList[i] = " ".join(tagList[i].split())
    	#each row must have 26 chars
    	tagList[i] = tagList[i].ljust(27)
    tag = "\r\n".join(tagList)
        
    nummer = array[1]
    currency = array[7]    
    amount  = (array[10])
    amountC  = (array[11])
    amountTyp = "D"     # Credit
    if amount == " ":
    	 amount = amountC
    	 amountTyp = "C" # Debit
        
    amount = amount.replace(".",",") # change comma to points    
    
    # write MT940 headder
    # https://quickstream.westpac.com.au/bankrec-docs/statements/mt940/#mt940-statement-format
    # https://deutschebank.nl/nl/docs/MT94042_EN.pdf
    if lineNumber == 3:
        Headder = (":20:"+"DateOfConversion"+now.strftime("%Y%m%d%H%M%S")+"\r\n")	
        Headder = Headder + (":25:"+nummer+"\r\n")
        Headder = Headder + (":28C:00001/001\r\n")
        ClosingDate = dayWertstellung+monthWertstellung+yearWertstellung
                
    # write content to file
    # Type CHG Charges and other expenses
    Body = (":61:"+yearWertstellung+monthWertstellung+dayWertstellung+monthBuchung+dayBuchung+amountTyp+amount+"FCHG"+"NONREF//NONREF"+"\r\n")
    # comments not exepteted on my accounting software
    #Body = Body + (tag+"\r\n")
    Body = Body + (":86:" + comment + "\r\n" + tag + "\r\n")
    BodyArray.append(Body)
    idBodyArray = idBodyArray + 1;
    OpeningDate = dayWertstellung+monthWertstellung+yearWertstellung

print("----- < end processing ") # info output 

mt940File.write('\ufeff')
mt940File.write(Headder)
mt940File.write(":60F"+":C" + OpeningDate+currency+"0,0"+"\r\n")

for i in range(idBodyArray,0,-1):
    mt940File.write(BodyArray[i-1])
   
mt940File.write(":62F"+":C" + ClosingDate + currency+"0,0"+"\r\n")
print("----- | end conversion ") # info output 
mt940File.write("\r\n")
mt940File.close()
