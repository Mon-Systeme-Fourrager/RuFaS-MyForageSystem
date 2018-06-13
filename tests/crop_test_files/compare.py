import sys


def main():
    expectedFileName = sys.argv[1]
    resultFileName = sys.argv[2]

    expectedFile = open(expectedFileName, "r")
    resultFile = open(resultFileName, "r")

    day = 0
    cut_off = .00015
    show_errors = 5

    passed = "PASSED"
    skipFirst = True
    for rowExpected, rowResult in zip(expectedFile, resultFile):
        if skipFirst:
            skipFirst = False
            continue

        cellsExpected = rowExpected.split(",")
        cellsResult = rowResult.split(",")
        day += 1

        for i in range(len(cellsExpected)):
            try:
                valueExpected = float(cellsExpected[i])
                valueResult = float(cellsResult[i])
            except Exception as e:
                print("error")

            if abs(valueExpected - valueResult) > cut_off:
                passed = "FAILED"
                print("error on day %i col %i in csv"% (day, i+1))
                print("Expected : %f \nResult  :  %f" % (valueExpected, valueResult))
                show_errors -= 1
                if show_errors == 0:
                    print("%s %s %s\n" % (passed, expectedFileName, resultFileName))
                    exit()

    print("%s %s %s\n" % (passed, expectedFileName, resultFileName))

    expectedFile.close()
    resultFile.close()



if __name__ == "__main__":
    main()