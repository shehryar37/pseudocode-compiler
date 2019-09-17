from symbol_table import SymbolTable


class Scope():
    def __init__(self, PARENT_SCOPE, parameters, return_type, block):
        self.SYMBOL_TABLE = SymbolTable()
        self.PARENT_SCOPE = PARENT_SCOPE
        self.parameters = parameters
        self.block = block
        self.return_type = return_type
        self.DATA_TYPES = {}

        if self.PARENT_SCOPE != None:
            self.DATA_TYPES = self.PARENT_SCOPE.DATA_TYPES
            self.VALUES = self.PARENT_SCOPE.VALUES
        else:
            self.init_data_types()
            self.VALUES = {}

    def add(self, var_name, value):
        self.VALUES[var_name] = value

    def init_data_types(self):
        self.DATA_TYPES['INTEGER'] = int
        self.DATA_TYPES['STRING'] = str
        self.DATA_TYPES['REAL'] = float
        self.DATA_TYPES['BOOLEAN'] = bool
