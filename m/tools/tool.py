
def createTool(name, url, version="0", build="", description=""):
    toolData = { "url":url, "version": version, "build": build, "description": description }
    t = Tool(name, toolData)
    return t

class Tool(object):
    def __init__(self, name, toolData):
        self.name = name
        self.url = toolData["url"] if "url" in toolData else toolData["path"]
        self.version = toolData["version"]
        self.build = toolData.get("build", "")
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
        try:
            selfBuild = int(self.build)
            otherBuilld = int(other.build)
        except:
            # builds are not integer, so
            # we assume that if the build changed then tool is newer
            if self.build != other.build:
                return False
            else:
                return True
        
        return selfBuild>otherBuild
    def install(self, store):
        pass
    def update(self, store):
        pass
    def installLibs(self, store):
        libs = self.toolData.get("libs")
        if not libs:
            return
        for lib in libs:
            libName  = lib["name"]
            if store.isLibInstalled(libName):
                store.addReferenceToLib(libName, self.name)
                continue
            self._installLib(lib, store, tryNumber=1)
                
            
    def _installLib(self, lib, store, tryNumber):
        # first check if library is already installed
        if self._testImport(lib):
            store.addReferenceToLib(libName, self.name)
            return True
        print " Tool %s requires library %s" % (self.name, lin["name"])
        refLocation = " from " + (lib["url"] if "url" in lib else "")
        installAvailable = ("intsall" in lib) and \
            (sys.platform in lib["install"] or "*" in lib["install"])
        downloadAvailable = ("download" in lib) and \
            (sys.platform in lib["download"] or "*" in lib["download"])
        
        if not (installAvailable or downloadAvailable):
            print "You should install the library by yourself%s" % refLocation
            t = input("Press enter when done or A for abort: ")
            if t.lower().startswith('a'):
                return False
            else:
                return self._installLib(lib, store, tryNumber+1)
        print "You can install it manually%s" % refLocation
        options = "(m)anual install"
        if installAvailable:
            print "You can use automatic install"
            options+="/automatic (i)nstall"
        if downloadAvailable:
            print "I can download it for you"
            options+="/(d)ownload"
        while True:
            t = input("Select "+options+" or (a)bort")
            if len(t) != 1:
                continue
            t = t[0].lower()
            if t=='m':
                # manual
                tt = input("Press enter when done or 'A' for abort: ")
                if tt.lower().startswith('a'):
                    return False
                else:
                    return self._installLib(lib, store, tryNumber+1)
            elif t=='i':
                if not installAvailable:
                    return self._installLib(lib, store, tryNumber+1)
            break
        
            print ""
        print "You can install "
        
    def _testImport(self, lib):
            libImportName = lib["import_name"]
            try:
                importedModule = __import__(libImportName)
                # import succeeded no need to install library
                return True
            except:
                # continue to lib installation
                return False
            self._installLib(lib, store)
        