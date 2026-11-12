import argparse
from pathlib import Path

try:
    from .code_module import comp as comp_code
    from .code_module import dest as dest_code
    from .code_module import jump as jump_code
    from .parser import A_COMMAND, C_COMMAND, L_COMMAND, Parser
    from .symbol_table import SymbolTable
except ImportError:
    from code_module import comp as comp_code
    from code_module import dest as dest_code
    from code_module import jump as jump_code
    from parser import A_COMMAND, C_COMMAND, L_COMMAND, Parser
    from symbol_table import SymbolTable


FIRST_VARIABLE_ADDRESS = 16
MAX_A_VALUE = 32767


class Assembler:
    def assemble(self, input_path, output_path=None):
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else input_path.with_suffix(".hack")

        symbol_table = self._build_symbol_table(input_path)
        binary_commands = self._generate_machine_code(input_path, symbol_table)

        with open(output_path, "w", encoding="utf-8", newline="\n") as output_file:
            for command in binary_commands:
                output_file.write(command + "\n")

        return output_path, len(binary_commands)

    def _build_symbol_table(self, input_path):
        symbol_table = SymbolTable()
        parser = Parser(input_path)
        rom_address = 0

        while parser.has_more_commands():
            parser.advance()
            if parser.command_type() == L_COMMAND:
                symbol_table.add_entry(parser.symbol(), rom_address)
            else:
                rom_address += 1

        return symbol_table

    def _generate_machine_code(self, input_path, symbol_table):
        parser = Parser(input_path)
        binary_commands = []
        next_variable_address = FIRST_VARIABLE_ADDRESS

        while parser.has_more_commands():
            parser.advance()
            command_type = parser.command_type()

            if command_type == L_COMMAND:
                continue

            if command_type == A_COMMAND:
                symbol = parser.symbol()
                if symbol.isdigit():
                    value = int(symbol)
                    if value > MAX_A_VALUE:
                        raise ValueError(f"A-instruction value out of range: {value}")
                elif symbol_table.contains(symbol):
                    value = symbol_table.get_address(symbol)
                else:
                    value = next_variable_address
                    symbol_table.add_entry(symbol, value)
                    next_variable_address += 1

                binary_commands.append(format(value, "016b"))
            elif command_type == C_COMMAND:
                binary_commands.append(
                    "111"
                    + comp_code(parser.comp())
                    + dest_code(parser.dest())
                    + jump_code(parser.jump())
                )
            else:
                raise ValueError(f"Unknown command type: {command_type}")

        return binary_commands


def main(argv=None):
    arg_parser = argparse.ArgumentParser(description="Hack Assembler (Nand to Tetris Project 6)")
    arg_parser.add_argument("input", help="Path to the .asm source file")
    arg_parser.add_argument("-o", "--output", help="Path to the output .hack file")
    args = arg_parser.parse_args(argv)

    output_path, instruction_count = Assembler().assemble(args.input, args.output)
    print(f"Assembled {args.input} -> {output_path} ({instruction_count} instructions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
