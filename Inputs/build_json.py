
#
# Parses out the path and the file from the given line
#
def getLineInfo(inString):
    inString = inString.strip(' "\n,')
    slashIndex = inString.index("/")
    path = inString[:slashIndex + 1]
    file = inString[slashIndex + 1:]
    return path, file


#
# Opens the inFile and writes its contents to the outFile.
# If/when a json file is encountered it opens that file, and continues writing
# its contents to the same outFile.
#
def open_and_expand(inFile, outFile, indent, curPath):
    with open(inFile, "r") as readFile:

        for line in readFile:
            if ".json" not in line:
                outFile.write(indent + line)

            else:
                path, fileName = getLineInfo(line)
                newPath = curPath + path
                open_and_expand(newPath + fileName, outFile, indent + "\t", newPath)

                if "," in line:
                    outFile.write(",")
                outFile.write("\n\n")



finalSettings = open("settings.json", "w")
inputSettings = "parameters2.txt"

try:
    open_and_expand(inputSettings, finalSettings, "", "")
finally:
    finalSettings.close()