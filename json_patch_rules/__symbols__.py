import time

class Symbol(str):
    def __new__(cls, value):
        cls.__symbol_id = time.time()
        return super(Symbol, cls).__new__(cls, f"Symbol({value})")

    def __repr__(self) -> str:
        return self.value

    def __eq__(self, other):
        if isinstance(other, Symbol):
            return other.__symbol_id == self.__symbol_id
        return False

EMPTY_ARRAY_SYMBOL = Symbol("aa")