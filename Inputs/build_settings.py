

def getParts(inString):
    inString = inString.strip("\n")
    colonIndex = inString.index(":")
    first = inString[:colonIndex + 1]
    second = inString[colonIndex+1:]

    return first, second

def getPathInfo(inString):
    inString = inString.strip('"\n')
    slashIndex = inString.index("/")
    path = inString[:slashIndex + 1]
    file = inString[slashIndex + 1:]
    return path, file


def generator(finalSettings, currFile, currPath, tabCount):
    orig_Indent = "\t" * tabCount
    #input(repr(orig_Indent + "{" + "\n"))
    finalSettings.write("\n" + orig_Indent + "{" + "\n")
    with open(currFile, "r") as readFile:
        tabCount += 1
        indent = "\t" * tabCount
        for row in readFile:
            try:
                title, value = getParts(row)
              #  input(repr(indent + title))
                finalSettings.write(indent + title)

                if ".txt" in value:
                    path, fileName = getPathInfo(value)
                    newPath = currPath + path
                    generator(finalSettings, newPath + fileName, newPath, tabCount)
                else:
                   # input(repr(value + "/n"))
                    finalSettings.write(value + "\n")
            except Exception:
              #  input((repr(indent+row)))
                finalSettings.write(indent + row.strip("\t\n") + "\n")

      #  input(repr(orig_Indent + "}\n"))
        finalSettings.write(orig_Indent + "}\n")


finalSettings = open("settings.json", "w")
try:
    generator(finalSettings, "parameters.txt", "", 0)
finally:
    finalSettings.close()
