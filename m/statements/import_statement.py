import miner_globals
import base
import m.common as common

def p_import_statement(p):
    '''statement : IMPORT import_name'''
    Import.add(p[2])

def p_import_as_statement(p):
    '''statement : IMPORT import_name AS ID'''
    Import.addAs(p[2], p[4])

def p_import_show(p):
    '''statement : IMPORT'''
    Import.show()

def p_import_remove(p):
    '''statement : IMPORT '-' import_name'''
    Import.remove(p[3])

class Import(base.StatementBase):
    NAME = "IMPORT"
    SHORT_HELP = "IMPORT <import-path> - adds additional import path to execution"
    LONG_HELP = """IMPORT <import-path>
IMPORT <import-path> as <alias> - imports module by some other name
IMPORT                 - lists defined import-pathes
IMPORT - <import-path> - removes specified import-path
    Adds additional import path to mining execution
    Allows to use custom commands
"""
    COMPLETION_STATE = common.COMPLETE_IMPORT
    @staticmethod
    def add(path):
        miner_globals.addImportModule(path, resolveModule=True)
    @staticmethod
    def addAs(path,alias):
        miner_globals.addImportModule(alias, realName=path, resolveModule=True)
    @staticmethod
    def show():
        for i in miner_globals.importMap.keys():
            print i

    @staticmethod
    def remove(path):
        miner_globals.removeImportModule(path)


miner_globals.addHelpClass(Import)
miner_globals.addKeyWord(statement="IMPORT")

