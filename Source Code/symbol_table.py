from data_types import *


class SymbolTable():
    def __init__(self):
        self.SYMBOL_TABLE = {}

    def add(self, name, metadata):
        self.SYMBOL_TABLE[name] = metadata

    def lookup(self, var_name):
        value = self.SYMBOL_TABLE.get(var_name).var_type
        return value
