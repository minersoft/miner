# 
# Copyright Michael Groys, 2014
#
import std_engine

class SQLiteEngine(std_engine.Engine):
    def __init__(self):
        std_engine.Engine.__init__(self)
    def connect(self, dbtype, parsedUrl, **kwargs):
        import sqlite3
        return std_engine.Connection(sqlite3.connect(parsedUrl), self)
    def getTableNamesQuery(self):
        return """SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"""
