import re
import sys
from pathlib import Path

from main import Assembler
from symbol_table import SymbolTable

BASE_DIR = Path(__file__).resolve().parent

EXPECTED_OUTPUTS = {
    "Add": [
        "0000000000000010",
        "1110110000010000",
        "0000000000000011",
        "1110000010010000",
        "0000000000000000",
        "1110001100001000",
    ],
    "Max": [
        "0000000000000000",
        "1111110000010000",
        "0000000000000001",
        "1111010011010000",
        "0000000000001010",
        "1110001100000001",
        "0000000000000001",
        "1111110000010000",
        "0000000000001100",
        "1110101010000111",
        "0000000000000000",
        "1111110000010000",
        "0000000000000010",
        "1110001100001000",
        "0000000000001110",
        "1110101010000111",
    ],
}

BINARY_LINE = re.compile(r"^[01]{16}$")


def verify_program(name):
    input_path = BASE_DIR / f"{name}.asm"
    output_path = BASE_DIR / f"{name}.hack"
    produced_path, instruction_count = Assembler().assemble(input_path, output_path)
    lines = produced_path.read_text(encoding="utf-8").splitlines()

    assert produced_path == output_path, f"{name}: unexpected output path"
    assert instruction_count == len(EXPECTED_OUTPUTS[name]), (
        f"{name}: expected {len(EXPECTED_OUTPUTS[name])} instructions, got {instruction_count}"
    )
    assert len(lines) == len(EXPECTED_OUTPUTS[name]), (
        f"{name}: expected {len(EXPECTED_OUTPUTS[name])} lines, got {len(lines)}"
    )

    for line_number, line in enumerate(lines, start=1):
        assert BINARY_LINE.fullmatch(line), (
            f"{name}: line {line_number} is not a 16-bit binary string: {line!r}"
        )

    assert lines == EXPECTED_OUTPUTS[name], f"{name}: output does not match expected machine code"

    print(f"PASS {name}.asm -> {name}.hack ({len(lines)} instructions, all 16-bit)")


def verify_symbol_table():
    table = SymbolTable()
    expected = {
        "SP": 0,
        "LCL": 1,
        "ARG": 2,
        "THIS": 3,
        "THAT": 4,
        "R0": 0,
        "R15": 15,
        "SCREEN": 16384,
        "KBD": 24576,
    }
    for symbol, address in expected.items():
        assert table.contains(symbol), f"missing predefined symbol: {symbol}"
        assert table.get_address(symbol) == address, f"wrong address for {symbol}"

    table.add_entry("counter", 16)
    assert table.contains("counter")
    assert table.get_address("counter") == 16

    print("PASS symbol table predefined symbols and custom entry")


def main():
    verify_program("Add")
    verify_program("Max")
    verify_symbol_table()
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
