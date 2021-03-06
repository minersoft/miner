import re
import os
import collections

import miner_globals
import runtime

from data_provider import DataProvider
from file_data_provider import FileDataProvider
from repository_data_provider import RepositoryDataProvider

miner_globals.addImportModule("re", value=re, resolveModule=False)
miner_globals.addImportModule("runtime", realName="m.runtime", value=runtime, resolveModule=False)
miner_globals.addImportModule("collections", realName="collections", value=collections, resolveModule=False)
miner_globals.addImportModule("os", realName="os", value=os, resolveModule=False)

miner_globals.addAggregator("sum", "aggregate.Sum", "sum expression evaluated for each entry")
miner_globals.addAggregator("sumIf", "aggregate.SumIf", "sumIf(cond, exp) calculates sum of expression for which condition is True")
miner_globals.addAggregator("fractionSum", "aggregate.FractionSum", "fractionSum(cond, exp) returns fraction value of sum of expressions for which condition is True")
miner_globals.addAggregator("avg", "aggregate.Avg", "average value of expression")
miner_globals.addAggregator("avgIf", "aggregate.AvgIf", "avgIf(cond,exp) calculates average value of expression for which condition is True")
miner_globals.addAggregator("count", "aggregate.Count", "counts all occurrences when expression evaluates to True")
miner_globals.addAggregator("fraction", "aggregate.Fraction", "returns fraction of all occurrences when expression evaluates to True")
miner_globals.addAggregator("ratio", "aggregate.Ratio", "ratio(nominator,denominator) - returns nominator/denominator after summing all values of both")
miner_globals.addAggregator("number", "aggregate.Number", "counts number of distinct values of expression")
miner_globals.addAggregator("numberIf", "aggregate.NumberIf", "counts number(condition, exp) of distinct values of expression for which condition evaluates to true")
miner_globals.addAggregator("stats", "aggregate.Stats", "calculates full set of statistical data for variable")
miner_globals.addAggregator("statsIf", "aggregate.StatsIf", "calculates full set of statistical data for variable if condition is true")
miner_globals.addAggregator("superset", "aggregate.Superset", "Merge values to the set")
miner_globals.addAggregator("first", "aggregate.First", "returns first seen value of expression")
miner_globals.addAggregator("last", "aggregate.Last", "returns last seen value of expression")
miner_globals.addAggregator("append", "aggregate.Append", "appends values to a list")
miner_globals.addAggregator("concat", "aggregate.Concat", "Concatenates lists to a single one")
miner_globals.addAggregator("min", "aggregate.Min", "returns minimum of all elements")
miner_globals.addAggregator("max", "aggregate.Max", "returns maximum of all elements")
miner_globals.addAggregator("valueAtMin", "aggregate.ValueAtMin", "valueAtMin(test, value) returns value at minimum of test")
miner_globals.addAggregator("valueAtMax", "aggregate.ValueAtMax", "valueAtMax(test, value) returns value at maximum of test")
miner_globals.addAggregator("segments", "aggregate.Segments", "segments(start, size) returns aggregate.Segments object")
miner_globals.addAggregator("rate", "aggregate.Rate", "rate(period)(value) gets the rates of the value over defined period")
miner_globals.addAggregator("rateIf", "aggregate.RateIf", "rateIf(period)(cond, exp) gets the rates of the value over defined period filtered by the condition")

miner_globals.addTargetToClassMapping("csv", "io_targets.iCSV", "io_targets.oCSV", "comma separated value text (unicode=True flag preserves unicode indication in output)")
miner_globals.addTargetToClassMapping("pickle", "io_targets.iPickle", "io_targets.oPickle", "python object native serialization format")
miner_globals.addTargetToClassMapping("stdout", None, "io_targets.oStdout", "dumps user friendly formatted output to stdout")
miner_globals.addTargetToClassMapping("less", None, "io_targets.oLess", "dumps user friendly formatted output to less pager")
miner_globals.addTargetToClassMapping("log", "io_targets.iLog", "io_targets.oLog", "Processes text file by splitting it to words. Created record is (line, words, NR).\nFS= may specify alternative regular regular expression for splitting.")
miner_globals.addTargetToClassMapping("raw", "io_targets.iRaw", "io_targets.oRaw", "Processes text file without splitting into words. Record is (line,).")
miner_globals.addTargetToClassMapping("json", "io_targets.iJson", "io_targets.oJson", "Reads json files to 'obj' variable or writes all variables to json list")
miner_globals.addTargetToClassMapping("tsv", "io_targets.iTsv", "io_targets.oTsv", "tab separated value text")

miner_globals.addExtensionToTargetMapping(".csv", "csv")
miner_globals.addExtensionToTargetMapping(".tsv", "tsv")
miner_globals.addExtensionToTargetMapping(".pic", "pickle")
miner_globals.addExtensionToTargetMapping(".txt", "stdout")
miner_globals.addExtensionToTargetMapping(".log", "log")
miner_globals.addExtensionToTargetMapping(".json", "json")
miner_globals.addExtensionToTargetMapping("stdout", "csv")

DataProvider.registerDataProvider("file", FileDataProvider)
DataProvider.registerDataProvider("repository", RepositoryDataProvider)

import m.db
import m.db.sqlite_engine
sqliteEngine = m.db.sqlite_engine.SQLiteEngine()
m.db.registerEngine("file.db", sqliteEngine)
m.db.registerEngine("file.sqlite", sqliteEngine)

