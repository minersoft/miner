import miner_globals
import base
import sys
import os.path
import m.common as common

def p_use_statement(p):
    '''statement : USE ID '''
    UseStatement.execute(p[2])

class UseStatement(base.StatementBase):
    NAME = "USE"
    SHORT_HELP = "USE <tool-name> - initializes tool"
    LONG_HELP = """USE <tool-name>
    Initializes tool specified by <tool-name>
    Initialization is specified by tool's init.miner script
    It may performs necessary imports, define aliases, IO targets and aggregators
"""
    COMPLETION_STATE = common.COMPLETE_TOOLS
    
    @staticmethod
    def execute(toolName):
        miner_globals.useTool(toolName)
    
miner_globals.addStatementName("USE")
miner_globals.addHelpClass(UseStatement)


