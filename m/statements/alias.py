import miner_globals
import m.common as common
import base

def p_alias_statement(p):
    '''statement : ALIAS ID '=' command_chain
                 | ALIAS ALIAS_ID '=' command_chain'''
    Alias.add(p[2], p[4])

def p_alias_statement_described(p):
    '''statement : ALIAS STRING ID '=' command_chain
                 | ALIAS STRING ALIAS_ID '=' command_chain'''
    Alias.add(p[3], p[5], p[2][1:-1])

def p_alias_show(p):
    '''statement : ALIAS'''
    Alias.show()

def p_alias_remove(p):
    '''statement : ALIAS '-' ALIAS_ID'''
    Alias.remove(p[3])

######

class Alias(base.StatementBase):
    NAME = "ALIAS"
    SHORT_HELP = "ALIAS <name> = command | ... | -  creates named alias to the chain of mining commands"
    LONG_HELP = """ALIAS <name> = command | ... |
ALIAS "description" <name> = command | ... | 
ALIAS          - lists defined aliases
ALIAS - <name> - removes specified alias
    Create named alias to the chain of mining commands
    Aliased chain cannot have any parameters and is substituted as is.
    The only way to control behavior of aliased comand is using variables
"""
    COMPLETION_STATE = common.COMPLETE_COMMANDS

    aliasDescriptions = {}
    @staticmethod
    def add(name, commandChain, description=None):
        miner_globals.aliasCommands[name] = commandChain
        if description:
            Alias.aliasDescriptions[name] = description
    @staticmethod
    def show():
        for name,value in miner_globals.aliasCommands.iteritems():
            print "%-6s - %s" % (name, Alias.aliasDescriptions.get(name, ""))
    @staticmethod
    def remove(name):
        try:
            del miner_globals.aliasCommands[name]
            del Alias.aliasDescriptions[name]
        except:
            pass

miner_globals.addHelpClass(Alias)
miner_globals.addKeyWord(statement="ALIAS")

