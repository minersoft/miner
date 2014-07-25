#
# Copyright Michael Groys, 2012-2014
#

#
# This file contains definition of different commands used in mining statement
# Each command is responsible to create code text for its generator function
#

from base import *
from async_command import *
from accumulate import *
from expand import *
from for_command import *
from if_command import *
from io_command import *
from limit_command import *
from match import *
from map_reduce import *
from merge_command import *
from parse_command import *
from pareto import *
from pass_command import *
from reorder import *
from pie_command import *
from select import *
from sortby import *
from top_command import *

__all__ = ['createTupleString', 'createNamedParameters', 'CommandBase', 'TypicalCommand']


all_p_commands = filter(lambda var: var.startswith("p_"), dir())

__all__ += all_p_commands

SOURCE_COMMAND_NAMES = ["READ", "RREAD", "ITERATE", "MERGE", "GLUE", "MAP"]

DESTINATION_COMMAND_NAMES = ["WRITE", "STDOUT", "STORE"]


