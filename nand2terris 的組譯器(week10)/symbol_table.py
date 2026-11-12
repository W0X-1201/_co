PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,
}


class SymbolTable:
    def __init__(self):
        self.symbols = dict(PREDEFINED_SYMBOLS)
        for register in range(16):
            self.symbols[f"R{register}"] = register

    def add_entry(self, symbol, address):
        self.symbols[symbol] = address

    def contains(self, symbol):
        return symbol in self.symbols

    def get_address(self, symbol):
        if symbol not in self.symbols:
            raise KeyError(f"Unknown symbol: {symbol!r}")
        return self.symbols[symbol]
