import os
import sys

import miner_globals
import miner_version

import tool

class ToolContainer:
    def __init__(self):
        self.tools = {}
        self.wasModified = True
    def add(self, tool):
        self.tools[tool.name] = tool
        self.wasModified = True
    def __contains__(self, name):
        return name in self.tools
    def get(self, name):
        return self.tools.get(name)
    def save(self, fileName):
        from m.runtime import saveToJson
        toolsDict = {}
        for name, t in self.tools.iteritems():
            toolsDict[name] = t.toolData
        self.wasModified = False
        return saveToJson(toolsDict, fileName)
    def load(self, fileName):
        from m.runtime import loadFromJson
        toolsDict = loadFromJson(fileName)
        if not toolsDict:
            return False
        self.tools = {}
        for name, data in toolsDict.iteritems():
            self.tools[name] = tool.Tool(name, data)
        self.wasModified = False
        return True
    def __getitem__(self, key):
        return self.tools[key]
    def __setitem__(self, key, val):
        self.tools[key] = val
        self.wasModified = True
    def __delitem__(self, key):
        del self.tools[key]
        self.wasModified = True
        
    def keys(self):
        return self.tools.keys()

class ToolBox(object):
    def __init__(self):
        self.createToolsPath()
        self.knownToolsPath = os.path.join(self.getToolsPath(), "known_tools.json")
        self.installedToolsPath = os.path.join(self.getToolsPath(), "installed_tools.json")
        self._knownTools = None
        self._installedTools = None
    
    def getToolsPath(self):
        return miner_globals.getToolsPath()
    
    def getToolPath(self, toolName):
        return miner_globals.getToolPath(toolName)
    
    def getLibsPath(self):
        return os.path.join(getToolsPath(), "Libs")
    
    def getDownloadsPath(self):
        return os.path.join(getToolsPath(), "Downloads")
    
    def getRecoveryPath(self):
        return os.path.join(getToolsPath(), "Recovery")
    
    def createToolsPath(self):
        path = self.getToolsPath()
        if not os.path.isdir(path):
            os.mkdir(path)
        return path
    
    def createLibsPath(self):
        path = self.getLibsPath()
        if not os.path.isdir(path):
            os.mkdir(path)
        return path
    
    def createDownloadsPath(self):
        path = self.getDownloadsPath()
        if not os.path.isdir(path):
            os.mkdir(path)
        return path
    
    def createRecoveryPath(self):
        path = self.getRecoveryPath()
        if not os.path.isdir(path):
            os.mkdir(path)
        return path
    
    def createKnownTools(self):
        self._knownTools = ToolContainer()
            # create empty known tools file
        self._knownTools.save(self.knownToolsPath)
    def getKnownTools(self):
        if self._knownTools is not None:
            return self._knownTools
        if not os.path.isfile(self.knownToolsPath):
            self.createKnownTools()
        else:
            self._knownTools = ToolContainer()
            self._knownTools.load(self.knownToolsPath)
        return self._knownTools
    def getInstalledTools(self):
        if self._installedTools is not None:
            return self._installedTools
        self._installedTools = ToolContainer()
        self._installedTools.load(self.installedToolsPath)
        return self._installedTools
    
    def isLibInstalled(self, libName):
        pass
    def addReferenceToLib(self, libName):
        pass
    def commit(self):
        if (self._installedTools is not None) and self._installedTools.wasModified:
            self._installedTools.save(self.installedToolsPath)
    def install(self, toolName, url=None, version=None):
        from source_base import SourceBase
        from source_local_dir import SourceLocalDir
        from source_archive import SourceArchive
        installedTools = self.getInstalledTools()
        if toolName in installedTools:
            print "Tool %s already installed" % toolName
            return False
        if not url:
            knownTools = self.getKnownTools()
            if toolName not in knownTools:
                print "Unknown tool %s" % tool
                return False
            raise NotImplemented
        method, path = SourceBase.spliturl(url)
        if (method=="" or method=="file") and os.path.isfile(path):
            res = SourceArchive().install("file", path, toolName, self)
        elif (method=="" or method=="dir" or method=="file") and os.path.isdir(path):
            res = SourceLocalDir().install("dir", path, toolName, self)
        elif method=="" or method=="file" or method=="dir":
            print "File %s is of invalid type or doesn't exist" % path
            return False
        else:
            print "Unsupported URL scheme: %s" % url
            return False
        if res:
            t = tool.createTool(toolName, "local", description="local")
            installedTools.add(t)
            self.commit()
        return res
    def uninstall(self, toolName):
        installedTools = self.getInstalledTools()
        if (toolName not in installedTools) and (not os.path.exists(self.getToolPath(toolName))):
            print "Tool %s is not installed" % toolName 
            return False
        if (toolName in installedTools) and os.path.exists(self.getToolPath(toolName)):
            if self._removeInstalledTool(toolName):
                del installedTools[toolName]
                print "Tool '%s' was uninstalled" % toolName
            else:
                print "Uninstallation of tool '%s' failed" % toolName
                return False
        elif toolName in installedTools:
            print "Uninstalling registered tool '%s' that doesn't appear on disk" % toolName 
            del installedTools[toolName]
        else:
            print "Uninstalling tool '%s' that appears on disk but isn't registered" % toolName
            self._removeInstalledTool(toolName)
            return True
        self.commit()
        return True
    
    def update(self, toolName, url=None, version=None):
        res = self.uninstall(toolName)
        if not res:
            return False
        return self.install(toolName, url, version)

    def _removeInstalledTool(self, toolName):
        if sys.platform.startswith("win32"):
            import subprocess
            cmd = ["rd", "/S", "/Q", self.getToolPath(toolName)]
            try:
                subprocess.check_call(" ".join(cmd), shell=True)
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            import shutil
            try:
                shutil.rmtree(self.getToolPath(toolName), ignore_errors=True)
                return True
            except:
                return False
    def printKnownTools(self):
        installedTools = self.getInstalledTools()
        knownTools = self.getKnownTools()
        for toolName in sorted(set(knownTools.keys())|set(installedTools.keys())):
            if toolName in installedTools:
                isInstalled = "installed"
            elif os.path.exists(miner_globals.getToolPath(toolName)):
                isInstalled = "local"
            else:
                isInstalled = ""
            if toolName in installedTools:
                description = installedTools[toolName].description
            else:
                description = knownTools[toolName].description
            print "  %-11s %-14s - %s" % (isInstalled, toolName, description)


    def getMinerTool():
        return {"path": "local", "version": miner_version.version, "build": miner_version.build }
    
    def isToolInstalled(self, toolName):
         installedTools = self.getInstalledTools()
         if toolName in installedTools:
             return True
         if os.path.exists(self.getToolPath(toolName)):
             print "Path %s exists but tool %s was not installed" % (self.getToolPath(toolName), toolName)
             return True
         return False

    def updateKnownTools(self):
        pass
    def printAvailableUpdates(self):
        installedTools = self.getInstalledTools()
        knownTools = self.getKnownTools()
        cnt = 0
        for toolName in sorted(installedTools.keys()):
            installedTool = installedTools[toolName]
            if (toolName in knownTools) and installedTool.version!='0':
                knownTool = knownTools[toolName]
                if knownTool.isNewer(installedTool):
                    installedBuildStr = ("/" + installedTool.build) if installedTool.build else ''
                    knownBuildStr = ("/" + knownTool.build) if knownTool.build else ''
                    print "UPDATE %-14s from %s%s to %s%s" % (toolName, installedTool.version, installedBuildStr, knownTool.version, knownBuildStr)
                    cnt += 1
        if cnt:
            print "%d updates available" % cnt
        else:
            print "Nothing to update"

