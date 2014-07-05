import miner_globals
import base
import os
import os.path
import m.common as common
import subprocess
import glob

def p_shell_statement(p):
    '''statement : SHELL filename_list'''
    ShellStatement.execute(p[2])
    p.lexer.begin('INITIAL')

def p_pwd_statement(p):
    '''statement : PWD'''
    print "Working directory is: " + os.getcwd()

def p_cd_statement(p):
    '''statement : CD FILENAME'''
    CDStatement.execute(p[2])
    p.lexer.begin('INITIAL')

def p_ls_statement_empty(p):
    '''statement : LS'''
    LSStatement.execute([])
    p.lexer.begin('INITIAL')

def p_ls_statement(p):
    '''statement : LS filename_list'''
    LSStatement.execute(p[2])
    p.lexer.begin('INITIAL')

class ShellStatement(base.StatementBase):
    NAME = "SHELL"
    SHORT_HELP = "SHELL <cmd> <arguments> - runs shell command"
    LONG_HELP = """SHELL <cmd> <arguments>
    Runs shell command under the current shell
"""
    COMPLETION_STATE = common.COMPLETE_FILE
    @staticmethod
    def execute(shellArgs):
        try:
            retcode = subprocess.call(" ".join(shellArgs), shell=True)
        except OSError as e:
            print "Execution of %s failed" % shellArgs[0]

class PwdStatement(base.StatementBase):
    NAME = "PWD"
    SHORT_HELP = "PWD - returns parent working directory"
    LONG_HELP = """PWD
    Returns parent working directory
"""

class CDStatement(base.StatementBase):
    NAME = "CD"
    SHORT_HELP = "CD <dir-name> - change the current working directory"
    LONG_HELP = """CD <dir-name>
    Change the current working directory
"""
    COMPLETION_STATE = common.COMPLETE_FILE
    @staticmethod
    def execute(newDir):
        try:
            os.chdir(newDir)
        except OSError as e:
            print "cd failed: %s" % str(e)

class LSStatement(base.StatementBase):
    NAME = "LS"
    SHORT_HELP = "LS <file> ... - list file information"
    LONG_HELP = """LS <file> ...
    list file information
"""
    COMPLETION_STATE = common.COMPLETE_FILE
    @staticmethod
    def execute(files):
        cumFiles = []
        for file in files:
            cumFiles += glob.glob(os.path.expanduser(file))
        try:
            subprocess.call(["/bin/ls", "-lh"] + cumFiles)
        except OSError as e:
            print "Execution of ls failed:", str(e)

miner_globals.addHelpClass(ShellStatement)
miner_globals.addStatementName("SHELL")
miner_globals.addHelpClass(PwdStatement)
miner_globals.addStatementName("PWD")
miner_globals.addHelpClass(CDStatement)
miner_globals.addStatementName("CD")
miner_globals.addHelpClass(LSStatement)
miner_globals.addStatementName("LS")

