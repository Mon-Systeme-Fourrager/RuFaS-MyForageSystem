


def generator(finalSettings, headFile, tabCount):
    finalSettings.write("{" + "\t"*tabCount + "\n")
    with open(headFile, "r") as readFile:
        tabCount+=1
        for row in readFile:
            print(row)
            colonIndex = row.index(":")
            finalSettings.write("\t"*tabCount + row[:colonIndex+1])

            restOfLine = row[colonIndex+1:]
            print(repr(restOfLine))
            if restOfLine[-5:-2] == "txt":
                generator(finalSettings, restOfLine.strip('\n"'), tabCount)
            else:
                finalSettings.write(restOfLine)
        finalSettings.write("\t"*tabCount + "}")



finalSettings = open("settings.json", "w")
try:
    generator(finalSettings, "parameters.txt", 0)
finally:
    finalSettings.close()
