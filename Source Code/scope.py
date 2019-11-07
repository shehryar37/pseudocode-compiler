from symbol_table import SymbolTable
from copy import deepcopy


class Scope():
    def __init__(self, PARENT_SCOPE, block, parameters=[], return_type=[]):
        self.SYMBOL_TABLE = SymbolTable()
        self.PARENT_SCOPE = PARENT_SCOPE
        self.parameters = parameters
        self.block = block
        self.return_type = return_type
        self.DATA_TYPES = {}

        if self.PARENT_SCOPE != None:
            self.DATA_TYPES = deepcopy(self.PARENT_SCOPE.DATA_TYPES)
            self.VALUES = deepcopy(self.PARENT_SCOPE.VALUES)
        else:
            self.init_data_types()
            self.VALUES = {}

    def declare(self, name, metadata):
        self.SYMBOL_TABLE.add(name, metadata)

    def assign(self, variable_name, *data):
        if self.VALUES.get(variable_name) is None:
            self.VALUES[variable_name] = data[0]
        else:
            self.VALUES[variable_name].assign(data)

    def get(self, variable_name):

        if self.VALUES.get(variable_name) is not None:
            return self.VALUES.get(variable_name).value
        else:
            return None

    def init_data_types(self):
        self.DATA_TYPES['INTEGER'] = int
        self.DATA_TYPES['STRING'] = str
        self.DATA_TYPES['REAL'] = float
        self.DATA_TYPES['BOOLEAN'] = bool
        self.DATA_TYPES['CHAR'] = str

    def clear(self):
        self.VALUES = None
        self.parameters = None
