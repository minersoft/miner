import miner_globals
import miner_version
import base
import sys
import m.common as common
import os
import os.path
import subprocess
import json
import traceback
import shutil

def p_install_statement(p):
    r"""statement : INSTALL
                  | INSTALL FILENAME
                  | INSTALL FILENAME FILENAME
                  | INSTALL FILENAME FILENAME FILENAME"""
    if len(p) == 2:
        p[0] = InstallStatement(None, None, None)
        return
    toolName = p[2]
    if len(p) >= 4:
        path = p[3]
    else:
        path = None
    if len(p) >= 5:
        version = p[4]
    else:
        version = "0"
    p[0] = InstallStatement(toolName, path, version)

def p_uninstall_statement(p):
    r"""statement : UNINSTALL FILENAME"""
    p[0] = UninstallStatement(p[2])

def p_update_statement(p):
    r"""statement : UPDATE
                  | UPDATE ID"""
    if len(p) == 3:
        toolName = p[2]
        if toolName == "miner":
            p[0] = UpdateMiner()
        else:
            p[0] = UpdateStatement(toolName)
    else:
        p[0] = UpdateStatement()

class InstallStatement(base.StatementBase):
    NAME = "INSTALL"
    SHORT_HELP = "INSTALL <tool-name> [<url>] [<version>] - installs tool"
    LONG_HELP = """INSTALL <tool-name> [<url>] [<version>]
    Installs tool specified by url or one of the known tools
    <uri> - can be path to the folder (absolute, or starting from ~),
            or one of supported install sources
    <version> - specifies latest version and/or build of the tool
"""
    @staticmethod
    def COMPLETION_STATE():
        return []

    INSTALLED_TOOLS = {}
    KNOWN_TOOLS = {}

    @staticmethod
    def getKnownToolsFileName():
        return miner_globals.getToolPath("known_tools.json")
    
    @staticmethod
    def getInstalledToolsFileName():
        return miner_globals.getToolPath("installed_tools.json")

    def __init__(self, toolName, path, version):
        base.StatementBase.__init__(self)
        self.toolName = toolName
        self.path = path
        InstallStatement.loadKnownTools()
        InstallStatement.loadInstalledTools()
        if not path:
            if self.toolName in InstallStatement.KNOWN_TOOLS:
                self.path = InstallStatement.KNOWN_TOOLS[self.toolName]['path']
                self.version = InstallStatement.KNOWN_TOOLS[self.toolName]['version']
                self.build = InstallStatement.KNOWN_TOOLS[self.toolName].get("build", "0")

        else:
            # version may be of format "<version>/<build>"
            if version and "/" in version:
                self.version, self.build = version.split("/")
            else:
                self.version = version
                self.build = "0"
            
    @staticmethod
    def loadKnownTools():
        try:
            fh = open(InstallStatement.getKnownToolsFileName(), "r")
            InstallStatement.KNOWN_TOOLS = json.load(fh)
            fh.close()
        except IOError:
            InstallStatement.KNOWN_TOOLS = {}
    @staticmethod
    def updateKnownTools(knownToolsData):
        return False

    @staticmethod
    def loadInstalledTools():
        if not os.path.exists(miner_globals.getToolsPath()):
            os.mkdir(miner_globals.getToolsPath())
        try:
            fh = open(InstallStatement.getInstalledToolsFileName(), "r")
            InstallStatement.INSTALLED_TOOLS = json.load(fh)
            fh.close()
        except IOError:
            InstallStatement.INSTALLED_TOOLS = {}
        InstallStatement.INSTALLED_TOOLS['miner'] = InstallStatement.getMinerVersion()

    @staticmethod
    def getMinerVersion():
        return {"path": "local", "version": miner_version.version, "build": miner_version.build }

    @staticmethod
    def getToolVersion(toolName):
        tool = InstallStatement.INSTALLED_TOOLS.get(toolName)
        if not tool:
            if os.path.exists(miner_globals.getToolPath(toolName)):
                return "local"
            else:
                return None
        version = tool["version"]
        if tool["build"]:
            version += "." + tool["build"]
        return version
    
    @staticmethod
    def saveInstalledTools():
        try:
            fh = open(InstallStatement.getInstalledToolsFileName(), "w")
            json.dump(InstallStatement.INSTALLED_TOOLS, fh, indent=4)
            fh.close()
        except IOError:
            print "Failed to saved installed tools file"

    def getToolLocation(self):
        return miner_globals.getToolPath(self.toolName)

    def installLocal(self, path):
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            print "Error: %s is not an existing directory" % path
            return
        os.symlink(path, self.getToolLocation())
        InstallStatement.INSTALLED_TOOLS[self.toolName] = {'path': path,
                                                           'version': 'local',
                                                           'build': '0'
                                                           }

    
    def printKnownTools(self):
        for toolName in sorted(set(InstallStatement.KNOWN_TOOLS.keys())|set(InstallStatement.INSTALLED_TOOLS.keys())):
            if toolName in InstallStatement.INSTALLED_TOOLS:
                isInstalled = "installed"
            elif os.path.exists(miner_globals.getToolPath(toolName)):
                isInstalled = "local"
            else:
                isInstalled = ""
            unknownTool = {'description': 'unknown'}
            print "  %-11s %-14s - %s" % (isInstalled, toolName, InstallStatement.KNOWN_TOOLS.get(toolName, unknownTool)['description'])
        
    def execute(self):
        if not self.toolName:
            # dump all known tools
            self.printKnownTools()
            return
        if os.path.exists(self.getToolLocation()):
            print "Tool %s is already installed" % self.toolName
            return
        if not self.path:
            print "Don't know %s location" % self.toolName
            return
        if ":" not in self.path:
            self.installLocal(self.path)
            InstallStatement.saveInstalledTools()
            return
        method, path = self.path.split(":", 1)
        if method == "file":
            self.installLocal(path)
        else:
            print "unsupported installation method: ", method
            return
        InstallStatement.saveInstalledTools()
 
class UninstallStatement(base.StatementBase):
    NAME = "UNINSTALL"
    SHORT_HELP = "UNINSTALL <tool-name> - removes tool"
    LONG_HELP = """UNINSTALL <tool-name>
    removes installed tool
"""
    COMPLETION_STATE = common.COMPLETE_TOOLS
    def __init__(self, toolName):
        base.StatementBase.__init__(self)
        self.toolName = toolName
    
    def execute(self):
        InstallStatement.loadInstalledTools()
        if self.toolName not in InstallStatement.INSTALLED_TOOLS:
            print "%s is not installed" % self.toolName
            return
        toolPath = miner_globals.getToolPath(self.toolName)
        if not os.path.exists(toolPath):
            print "Tool %s was not installed properly" % self.toolName
        elif os.path.islink(toolPath):
            os.unlink(toolPath)
        else:
            shutil.rmtree(toolPath, True)
        del InstallStatement.INSTALLED_TOOLS[self.toolName]
        InstallStatement.saveInstalledTools()

class UpdateStatement(InstallStatement):
    NAME = "UPDATE"
    SHORT_HELP = "UPDATE <tool-name> - updates tool"
    LONG_HELP = """UPDATE <tool-name>
UPDATE
    updates tool.
    second version shows all available updates
"""
    def __init__(self, toolName=None):
        InstallStatement.__init__(self, toolName, None, None)
    
    
    def updateKnownTools(self):
        return False

    def execute(self):
        if not self.updateKnownTools():
            return
        if not self.toolName:
            InstallStatement.loadInstalledTools()
            cnt = 0
            for toolName in sorted(InstallStatement.INSTALLED_TOOLS.keys()):
                installedTool = InstallStatement.INSTALLED_TOOLS[toolName]
                if (toolName in InstallStatement.KNOWN_TOOLS) and installedTool['version']!='local':
                    knownTool = InstallStatement.KNOWN_TOOLS[toolName]
                    if self.versionLess(installedTool, knownTool):
                        installedBuildStr = ("/" + installedTool['build']) if installedTool.get('build', 0) else ''
                        knownBuildStr = ("/" + knownTool['build']) if knownTool.get('build', 0) else ''
                        print "UPDATE %-14s from %s%s to %s%s" % (toolName, installedTool['version'], installedBuildStr, knownTool['version'], knownBuildStr)
                        cnt += 1
            if cnt:
                print "%d updates available" % cnt
            else:
                print "Nothing to update"
        else:
            installedTool = InstallStatement.INSTALLED_TOOLS.get(self.toolName, None)
            if not installedTool:
                print "Cannot update not installed tool %s" % self.toolName
                return
            if installedTool['version'] == 'local':
                print "Cannot update local tool %s" % self.toolName
                return
            knownTool = InstallStatement.KNOWN_TOOLS.get(self.toolName, None)
            if not knownTool:
                print "%s is not registered in miner warehouse" % self.toolName
                return
            if not self.versionLess(installedTool, knownTool):
                print "No need to update %s" % self.toolName
                return
            if os.path.islink(self.getToolLocation()):
                os.unlink(self.getToolLocation())
            else:
                shutil.rmtree(self.getToolLocation(), True)
            self.path = knownTool['path']
            self.version = knownTool['version']
            self.build = knownTool.get('build', 0)
            InstallStatement.execute(self)
            
    def versionLess(self, tool1, tool2):
        #print "versionsDiffer: tool1", tool1, "tool2", tool2
        
        if tool1["version"]=="local" or tool2["version"]=="local":
            return True
        tool1version = map(int, tool1['version'].split("."))
        tool2version = map(int, tool2['version'].split("."))
        if tool1version != tool2version:
            return tool1version < tool2version
        
        build1Str = tool1.get('build')
        build1 = int(build1Str) if build1Str else 0
        build2Str = tool2.get('build')
        build2 = int(build2Str) if build2Str else 0
        return build1 < build2


class UpdateMiner(UpdateStatement):
    def __init__(self):
        UpdateStatement.__init__(self, "miner")
    def execute(self):
        pass

def getToolVersion(toolName):
    InstallStatement.loadInstalledTools()
    return InstallStatement.getToolVersion(toolName)
 
miner_globals.getToolVersion = getToolVersion     
miner_globals.addStatementName("INSTALL")
miner_globals.addHelpClass(InstallStatement)

miner_globals.addStatementName("UNINSTALL")
miner_globals.addHelpClass(UninstallStatement)

miner_globals.addStatementName("UPDATE")
miner_globals.addHelpClass(UpdateStatement)

