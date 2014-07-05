import miner_globals
import m.common as common
import base
from eval_statement import EvalStatement

def p_doc_statement(p):
    '''statement : DOC import_name'''
    p[0] = DocStatement(p[2])

class DocStatement(EvalStatement):
    """
    Get documentation for python modules, classes or functions
    """
    NAME = "DOC"
    SHORT_HELP = "DOC <id> - gets documentation for id"
    LONG_HELP = """DOC <id>
DOC <module_name.id>
    Gets documentation for python modules, classes or fumctions if available
    Module should be imported before use or it should be preloaded module "runtime"
"""
    COMPLETION_STATE = common.COMPLETE_SYMBOLS

    def __init__(self, docId):
        EvalStatement.__init__(self)
        self.myDocId = docId;
    def getCommand(self):
        s = self.getImports()
        s += "def getDocString():\n"
        s += """
    try:
        return %s.__doc__
    except:
        return "No documentation specified for %s"\n
""" % (self.myDocId, self.myDocId)
        s += "print getDocString()\n"
        return s


miner_globals.addHelpClass(DocStatement)
miner_globals.addStatementName("DOC")

