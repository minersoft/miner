
def createTool(name, url, version=None, build=0, description=""):
    if not version:
        version = "0.0"
    toolData = { "name":name, "url":url, "version": version, "build": build, "description": description }
    t = Tool(toolData)
    return t

class Tool(object):
    def __init__(self, toolData):
        self.name = toolData["name"]
        self.url = toolData["url"] if "url" in toolData else toolData["path"]
        self.version = toolData["version"]
        self.build = toolData.get("build", 0)
        self.toolData = toolData
    @property
    def description(self):
        return self.toolData.get("description", "")
    def __eq__(self, other):
        return (self.name==other.name) and (self.version==other.version) and (self.build==other.build)
    def isNewer(self, other):
        if self.name != other.name:
            return False
        try:
            selfVersion = map(int, self.version.split("."))
            otherVersion = map(int, other.version.split("."))
        except:
            print "Failed to compare versions: %s vs %s" % (selfVersion, otherVersion)
            return False
        if selfVersion > otherVersion:
            return True
        elif selfVersion < otherVersion:
            return False
        # version is equal, check builds
        return self.build>other.build
    def isNewerOrSameVersion(self, version):
        try:
            selfVersion = map(int, self.version.split("."))
            otherVersion = map(int, version.split("."))
        except:
            # TODO: should raise exception
            print "Failed to compare versions: %s vs %s" % (self.version, version)
            return False
        return selfVersion >= otherVersion
        
    def checkDepndencies(self, toolBox):
        res = True
        for module in self.toolData.get("external_modules", []):
            if not self._testImport(module):
                res = False
                s = "Please install module " + module["name"]
                if "url" in module:
                    s += ", from " + module["url"]
                print s
        for tool in self.toolData.get("dependencies", []):
            version = tool.get("version")
            if not toolBox.checkToolVersin(tool["name"], version):
                res = False
                s = "Depends on module " + tool["name"]
                if version:
                    s += " version " + version
                print s
        return res

    def _testImport(self, module):
            libImportName = module["import_name"]
            try:
                importedModule = __import__(libImportName)
                # import succeeded no need to install library
                return True
            except:
                # continue to lib installation
                return False
        