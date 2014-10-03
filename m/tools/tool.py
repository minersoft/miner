from miner_globals import setGlobalCompletionState, resetGlobalCompletionState, updateRegistry, isScriptParameterDefined
import m.common as common
import os
from test.test_importhooks import PathImporter

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
                s = "Please install module '%s'" % module["name"]
                if "url" in module:
                    s += ", from " + module["url"]
                print s
                res = self._pollModuleInstallation(module)
                if not res:
                    return False
        for tool in self.toolData.get("dependencies", []):
            version = tool.get("version")
            if not toolBox.checkToolVersion(tool["name"], version):
                res = False
                s = "Depends on module " + tool["name"]
                if version:
                    s += " version " + version
                print s
                res = self._pollToolInstallation(tool, toolBox)
                if not res:
                    return False
        for ext in self.toolData.get("external_resources", []):
            parameter_name = "EXTERNAL_" + ext.get("parameter_name") + "_PATH"
            if not isScriptParameterDefined(parameter_name):
                s = "Requires external %s" % ext["name"]
                if "url" in ext:
                    s +=" (can be installed from %s)" % ext["url"]
                print s
                res = self._pollExternalInstallation(ext, parameter_name)
                if not res:
                    return False
        
                
        return res

    def _getUserSelection(self, prompt):
        setGlobalCompletionState(common.COMPLETE_NONE)
        userInput = raw_input(prompt)
        while len(userInput) == 0:
            userInput = raw_input("? ")
        resetGlobalCompletionState()
        return userInput[0].lower()

    def _getPathInput(self, prompt):
        print prompt
        setGlobalCompletionState(common.COMPLETE_FILE)
        userInput = raw_input("? ")
        while len(userInput) == 0:
            userInput = raw_input("? ")
        resetGlobalCompletionState()
        return userInput

    def _pollModuleInstallation(self, module):
        while True:
            userInput = self._getUserSelection("I fixed it (R)etry / I can't fix it, (A)bort / I will fix it (L)ater: ")
            if userInput == 'a':
                return False
            elif userInput == 'r':
                if self._testImport(module):
                    return True
                else:
                    print "Module '%s' is still not installed" % module["name"]
            elif userInput == 'l':
                return True
            
    def _pollToolInstallation(self, tool, toolBox):
        while True:
            userInput = self._getUserSelection("(I)nstall it automatically / I can't fix it, (A)bort / I will fix it (L)ater: ")
            if userInput == 'i':
                res = toolBox.install(tool["name"])
                if not res:
                    print "Failed to install '%s' automatically" % tool["name"]
                    continue
                return True
            elif userInput == 'a':
                return False
            elif userInput == 'l':
                return True
    def _pollExternalInstallation(self, ext, parameter_name):
        while True:
            pathInput = self._getPathInput("Please specify path for %s / I can't find it (A)bort / I'll set it manually (L)ater in %s parameter" % \
                                           (ext["path_to"], parameter_name) ) 
            if pathInput.lower() == 'a':
                return False
            elif pathInput.lower() == 'l':
                return True
            else:
                if os.path.exists(pathInput):
                    updateRegistry(parameter_name, os.path.abspath(pathInput))
                    return True
                else:
                    print "%s doesn't exist" % pathInput

    def _testImport(self, module):
            libImportName = module["import_name"]
            try:
                importedModule = __import__(libImportName)
                # import succeeded no need to install library
                return True
            except:
                # continue to lib installation
                return False
        