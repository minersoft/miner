import miner_globals
import base
import sys
import m.common as common
import os
import os.path
import traceback

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
                  | UPDATE FILENAME
                  | UPDATE FILENAME FILENAME
                  | UPDATE FILENAME FILENAME FILENAME"""
    toolName = None
    url = None
    version = "0"
    l = len(p)
    if l >= 5:
        version = p[4]
    if l >= 4:
        url = p[3]
    if l >= 3:
        toolName = p[2]
    p[0] = UpdateStatement(toolName, url, version)

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
    def COMPLETION_STATE(input, pos):
        from m.tools.toolbox import ToolBox
        if pos==0:
            return common.COMPLETE_NONE
        tokens = input[:pos].split()
        l = len(tokens)
        if input[pos-1].isspace():
            l += 1
        if l==3:
            return common.COMPLETE_FILE
        elif l==2:
            return list(ToolBox().getKnownTools().keys())
        else:
            return []

    INSTALLED_TOOLS = {}
    KNOWN_TOOLS = {}

    def __init__(self, toolName, path, version):
        base.StatementBase.__init__(self)
        self.toolName = toolName
        self.path = path
        self.version = version
        
    def execute(self):
        from m.tools.toolbox import ToolBox
        toolbox = ToolBox()
        if not self.toolName:
            # dump all known tools
            toolbox.printKnownTools()
            return
        if toolbox.isToolInstalled(self.toolName):
            print "Tool %s is already installed" % self.toolName
            return
        toolbox.install(self.toolName, self.path, self.version)
 
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
        from m.tools.toolbox import ToolBox
        ToolBox().uninstall(self.toolName)

class UpdateStatement(base.StatementBase):
    NAME = "UPDATE"
    SHORT_HELP = "UPDATE <tool-name> - updates tool"
    LONG_HELP = """UPDATE <tool-name> [<url>]
UPDATE
    updates tool.
    second version shows all available updates
"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        from m.tools.toolbox import ToolBox
        if pos==0:
            return common.COMPLETE_NONE
        tokens = input[:pos].split()
        l = len(tokens)
        if input[pos-1].isspace():
            l += 1
        if l==3:
            return common.COMPLETE_FILE
        elif l==2:
            return list(ToolBox().getInstalledTools().keys())
        else:
            return []
    
    def __init__(self, toolName=None, url=None, version="0"):
        base.StatementBase.__init__(self)
        self.toolName = toolName
        self.url = url
        self.version = version
    
    def execute(self):
        from m.tools.toolbox import ToolBox
        toolbox = ToolBox()
        if not self.toolName:
            toolbox.printAvailableUpdates()
        else:
            toolbox.update(self.toolName, self.url, self.version)


def getToolVersion(toolName):
    raise NotImplementedError()
 
miner_globals.getToolVersion = getToolVersion     
miner_globals.addKeyWord(statement="INSTALL", switchesToFileMode=True)
miner_globals.addHelpClass(InstallStatement)

miner_globals.addKeyWord(statement="UNINSTALL", switchesToFileMode=True)
miner_globals.addHelpClass(UninstallStatement)

miner_globals.addKeyWord(statement="UPDATE", switchesToFileMode=True)
miner_globals.addHelpClass(UpdateStatement)

