def loadFromJson(fileName, printErrors=False):
    """loadFromJson(fileName, printErrors=False): Loads python object from json file"""
    import json
    try:
        handler = open(fileName, "rb")
        try:
            obj = json.load(handler)
        except Exception as e:
            if printErrors:
                print "Failed to load json from '%s' - %s" % (fileName, str(e))
            obj = None
        handler.close()
        return obj
    except Exception as e:
        if printErrors:
            print "Failed to open '%s' - %s" % (fileName, str(e))
        return None

def saveToJson(obj, fileName):
    """saveToJson(obj, fileName): Saves python object to json file"""
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

def loadFromPickle(fileName):
    """loadFromPickle(fileName): Loads python object from pickle file"""
    import pickle
    try:
        handler = open(fileName, "rb")
        try:
            obj = pickle.load(handler)
        except:
            raise
            obj = None
        handler.close()
        return obj
    except:
        raise
        return None

def saveToPickle(obj, fileName):
    """saveToPickle(obj, fileName): Saves python object to pickle file"""
    import pickle
    try:
        handler = open(fileName, "wb")
        try:
            pickle.dump(obj, handler)
        except:
            print "Failed to save to file", fileName
            raise
        handler.close()
    except:
        print "Failed to open file:", fileName
        raise


def mergeDictionaries(*dicts):
    """mergeDictionaries(*dicts): merge dictionaries into a new one"""
    merged = {}
    for d in dicts:
        merged.update(d)
    return merged
