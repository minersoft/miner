import os
import sys

import miner_globals
import miner_version
from m.utilities import loadFromJson, saveToJson
import m.loggers as loggers

import tool

class ToolContainer:
    def __init__(self):
        self.tools = {}
        self.wasModified = True
        self.warehouses = {}
    def add(self, name, tool):
        self.tools[name] = tool
        self.wasModified = True
    def __contains__(self, name):
        return name in self.tools
    def get(self, name):
        return self.tools.get(name)
    def save(self, fileName):
        toolList = {}
        for name, t in self.tools.iteritems():
            toolList[name] = t.toolData
        warehouseList = []
        for url, w in self.warehouses.iteritems():
            warehouseList.append(dict(w.iteritems(), url=url))
        jsonObj = {"tools": toolList, "warehouses": warehouseList }
        self.wasModified = False
        return saveToJson(jsonObj, fileName)
    def load(self, fileName):
        jsonObj = loadFromJson(fileName)
        if not jsonObj:
            return False
        self.tools = {}
        for name, data in jsonObj["tools"].iteritems():
            self.tools[name] = tool.Tool(data)
        for data in jsonObj.get("warehouses", []):
            self.warehouses[data["url"]] = data
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
    def merge(self, other):
        cnt = 0
        for name, tool in other.tools.iteritems():
            if name in self.tools:
                myTool = self.tools[name]
                if not tool.isNewer(myTool):
                    continue
            self.tools[name] = tool
            cnt += 1
        if cnt > 0:
            self.wasModified = True
    def keys(self):
        return self.tools.keys()
    def getWarehouse(self, warehousePath):
        w = self.warehouses.get(warehousePath)
        if w is None:
            w = {'url': warehousePath, 'last-modified': None, 'etag': None}
            self.warehouses[warehousePath] = w
            self.wasModified = True
        return w
    def __len__(self):
        return len(self.tools)
        

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
        return os.path.join(self.getToolsPath(), "Libs")
    
    def getDownloadsPath(self):
        return os.path.join(self.getToolsPath(), "Downloads")
    
    def getRecoveryPath(self):
        return os.path.join(self.getToolsPath(), "Recovery")
    
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
        self._knownTools.add("miner", self.getMinerTool())
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
        minerTool = self._installedTools.get("miner")
        if not minerTool or not minerTool.isNewerOrSameVersion(miner_version.version) or (minerTool.build < miner_version.build):
            self._installedTools["miner"] = self.getMinerTool()
        return self._installedTools
    
    def isLibInstalled(self, libName):
        pass
    def addReferenceToLib(self, libName):
        pass
    def commit(self):
        if (self._installedTools is not None) and self._installedTools.wasModified:
            loggers.mainLog.info("committing installed tools")
            self._installedTools.save(self.installedToolsPath)
        if (self._knownTools is not None) and self._knownTools.wasModified:
            loggers.mainLog.info("committing known tools")
            self._knownTools.save(self.knownToolsPath)
    def _createSource(self, url, version, build):
        from source_base import SourceBase
        from source_local_dir import SourceLocalDir
        from source_archive import SourceArchive
        from source_http import SourceHttp
        from source_github import SourceGithub
        method, path = SourceBase.spliturl(url)
        if (method=="" or method=="file") and os.path.isfile(path):
            return SourceArchive("file", path, version, build)
        elif (method=="" or method=="dir" or method=="file") and os.path.isdir(path):
            return SourceLocalDir("dir", path, version, build)
        elif method=="" or method=="file" or method=="dir":
            print "File %s is of invalid type or doesn't exist" % path
            return False
        elif method in ["http", "https", "ftp"]:
            return SourceHttp(method, path, version, build)
        elif method == "github":
            return SourceGithub(method, path, version, build)
        else:
            print "Unsupported URL scheme: %s" % url
            return None
        
    def install(self, toolName, url=None, version=None, build=None):
        if toolName[0].isupper():
            print "Tool name (%s) should start with lowercase letter" % toolName
            return False
        installedTools = self.getInstalledTools()
        if toolName in installedTools:
            print "Tool %s already installed" % toolName
            return False
        t = None
        if not url:
            knownTools = self.getKnownTools()
            if toolName not in knownTools:
                print "Unknown tool %s" % tool
                return False
            t = knownTools[toolName]
            if not t.checkDepndencies(self):
                return False
            url = t.url
            version = t.version
            build = t.build

        src = self._createSource(url, version, build)
        if not src:
            print "Unsupported URL scheme: %s" % url
            return False
        res = src.install(toolName, self)
        if res:
            if url:
                # tool is installed manually - check if it includes tool description file
                toolDescriptionFile = os.path.join(self.getToolPath(toolName), "tool-description.json")
                if os.path.isfile(toolDescriptionFile):
                    toolJson = loadFromJson(toolDescriptionFile, printErrors=True)
                    if toolJson:
                        t = tool.Tool(toolJson)
                        if not t.checkDepndencies(self):
                            self.uninstall(toolName)
                            return False
                    else:
                        print "Invalid tool-description file detected, ignored"
                if not t:
                    t = tool.createTool(toolName, url, description="manually installed", version=version)        
                    
            installedTools.add(toolName, t)
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
        if toolName == "miner":
            return self.updateMiner(url, version)
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
        knownTools = self.getKnownTools()
        if len(knownTools) <= 1:
            # only miner is known - try to get more tools
            self.updateKnownTools()
        installedTools = self.getInstalledTools()
        for toolName in sorted(set(knownTools.keys())|set(installedTools.keys())):
            if toolName in installedTools:
                isInstalled = "installed"
            elif os.path.exists(miner_globals.getToolPath(toolName)):
                isInstalled = "local"
            else:
                isInstalled = ""
            if toolName in installedTools:
                description = installedTools[toolName].description
                version = installedTools[toolName].version
            else:
                description = knownTools[toolName].description
                version = knownTools[toolName].version
            print "  %-11s %-14s %-6s - %s" % (isInstalled, toolName, version, description)


    def getMinerTool(self):
        return tool.Tool({"name": "miner", "path": "local", "version": miner_version.version, "build": miner_version.build, "description": "The Miner" })
    
    def isToolInstalled(self, toolName):
        installedTools = self.getInstalledTools()
        if toolName in installedTools:
            return True
        if os.path.exists(self.getToolPath(toolName)):
            print "Path %s exists but tool %s was not installed" % (self.getToolPath(toolName), toolName)
            return True
        return False

    def printAvailableUpdates(self):
        self.updateKnownTools()
        installedTools = self.getInstalledTools()
        knownTools = self.getKnownTools()
        cnt = 0
        for toolName in sorted(installedTools.keys()):
            installedTool = installedTools[toolName]
            if (toolName in knownTools) and installedTool.version!='0':
                knownTool = knownTools[toolName]
                if knownTool.isNewer(installedTool):
                    installedBuildStr = ("/" + str(installedTool.build)) if installedTool.build else ''
                    knownBuildStr = ("/" + str(knownTool.build)) if knownTool.build else ''
                    print "UPDATE %-14s from %s%s to %s%s" % (toolName, installedTool.version, installedBuildStr, knownTool.version, knownBuildStr)
                    cnt += 1
        if cnt:
            print "%d updates available" % cnt
        else:
            print "Nothing to update"

    def updateMiner(self, url=None, version=None, build=None):
        minerSrc = self._createSource(url, version, build)
        if not minerSrc:
            print "Unsupported URL scheme: %s" % url
            return False
        res = minerSrc.prepare("miner", self)
        if not res:
            print "Miner upgrade failed"
            return False
        newMinerPath = minerSrc.getPreparedToolRootDir()
        if not newMinerPath:
            print "Miner upgrade failed - invalid miner package"
            return False
        self._updateMinerFromPath(newMinerPath)
    def _updateMinerFromPath(self, newMinerPath):
        self.createRecoveryPath()
        os.execl(sys.executable, os.path.join(newMinerPath,"miner_upgrade.py"), \
                 "-v", miner_version.version, "-b", str(miner_version.build), \
                 "-d", miner_globals.minerBaseDir, "-r", self.getRecoveryPath())
        
    def checkToolVersion(self, toolName, version):
        installedTools = self.getInstalledTools()
        tool = installedTools.get(toolName)
        if not tool:
            return False
        if not version:
            return True
        return tool.isNewerOrSameVersion(version)
    
    def updateKnownTools(self):
        warehousePath = miner_globals.getScriptParameter("MINER_WAREHOUSE", None)
        if not warehousePath:
            print "Warehouse Url is not defined"
            return False
        knownTools = self.getKnownTools()
        warehouseData = knownTools.getWarehouse(warehousePath) 
        src = self._createSource(warehousePath, version=None, build=None)
        if not src:
            print "Invalid warehouse path"
            return False
        res = src.prepare("warehouse", self, if_differs_from=warehouseData)
        if not res:
            return False
        warehouseData.update(src.toolIdentity)
        loggers.installLog.info("Warehouse data=%s", warehouseData)
        knownTools.wasModified = True
        toolsDir = src.getPreparedToolRootDir()
        warehouseTools = ToolContainer()
        for toolFileName in os.listdir(toolsDir):
            if toolFileName.endswith(".json"):
                json = loadFromJson(os.path.join(toolsDir, toolFileName))
                if json:
                    warehouseTools.add(toolFileName[:-5], tool.Tool(json))
        src.clearPrepare()
        knownTools.merge(warehouseTools)
        loggers.installLog.info("UPDATE from warehouse: known tools were %s modified", "" if knownTools.wasModified else "not") 
        self.commit()
        return True