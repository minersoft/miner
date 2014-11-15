import miner_globals
import m.commands as commands
import m.common as common
import base

# Generic help
def p_help_statement(p):
    '''statement : HELP'''
    Help.printHelp()

# Get help with single keyword (use filename as HACK to skip specifying all keywords explicitly)
def p_help_statement_ID(p):
    '''statement : HELP FILENAME'''
    Help.printHelp(p[2])

# Get help for 2 part keyword (e.g. "FOR DISTINCT")
def p_help_statement_ID_ID(p):
    '''statement : HELP FILENAME FILENAME'''
    Help.printHelp("%s %s" % (p[2], p[3]))

class Help(base.StatementBase):
    NAME = "HELP"
    SHORT_HELP = "HELP [command] - provides help information about command"
    LONG_HELP = """HELP [command]
    Provides help information about command(s)
"""
    COMPLETION_STATE = common.COMPLETE_FOR_HELP
    @staticmethod
    def printHelp(commandName=None):
        if not commandName:
            print "Format of mining command is:"
            print "READ <filename> | comand1 | command2 ... | WRITE filename/STDOUT"
            print "Where minning command is one of:"
            for commandClass in miner_globals.getHelpClasses():
                if common.class_isinstance(commandClass, commands.CommandBase):
                    print "    %s" % commandClass.SHORT_HELP
            print "\nAdditional commands are:"
            for commandClass in miner_globals.getHelpClasses():
                if not common.class_isinstance(commandClass, commands.CommandBase):
                    print "    %s" % commandClass.SHORT_HELP
        else:
            for commandClass in miner_globals.getHelpClasses():
                if commandName == commandClass.NAME:
                    print common.HelpClass.getLongHelp(commandClass)
                    return
            countMatches = 0
            for commandClass in miner_globals.getHelpClasses():
                if  commandClass.NAME.startswith(commandName):
                    print "    %s" % commandClass.SHORT_HELP
                    countMatches += 1
            if countMatches == 0:
                print "Unknown command %s" % commandName


miner_globals.addHelpClass(Help)
miner_globals.addKeyWord(statement="HELP", switchesToFileMode=True)


