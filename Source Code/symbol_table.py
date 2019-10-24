class SymbolTable():
    def __init__(self):
        self.SYMBOL_TABLE = {}

    def add(self, var_name, var_type):
        self.SYMBOL_TABLE[var_name] = var_type

    def lookup(self, var_name):
        value = self.SYMBOL_TABLE.get(var_name)
        return value
