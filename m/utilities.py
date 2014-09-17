def loadFromJson(fileName):
    """Loads python object from json file"""
    import json
    try:
        handler = open(fileName, "rb")
        try:
            obj = json.load(handler)
        except:
            obj = None
        handler.close()
        return obj
    except:
        return None

def saveToJson(obj, fileName):
    """Saves python object to json file"""
    import json
    res = False
    try:
        handler = open(fileName, "wb")
        try:
            json.dump(obj, handler, indent=4)
            res = True
        except:
            print "Failed to save to file", fileName
        handler.close()
    except:
        print "Failed to open file:", fileName
    return res
