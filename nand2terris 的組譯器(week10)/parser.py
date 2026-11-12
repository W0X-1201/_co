A_COMMAND = "A_COMMAND"
C_COMMAND = "C_COMMAND"
L_COMMAND = "L_COMMAND"


class Parser:
    def __init__(self, file_path):
        self.file_path = str(file_path)
        self.commands = []
        self.current_index = -1
        self.current_command = ""
        self._load_commands()

    def _load_commands(self):
        with open(self.file_path, "r", encoding="utf-8") as source:
            for raw_line in source:
                line = raw_line.split("//", 1)[0].strip()
                if line:
                    self.commands.append(line)

    def has_more_commands(self):
        return self.current_index + 1 < len(self.commands)

    def advance(self):
        if not self.has_more_commands():
            raise IndexError("No more commands to advance to.")
        self.current_index += 1
        self.current_command = self.commands[self.current_index]

    def command_type(self):
        self._ensure_advanced()
        command = self.current_command
        if command.startswith("(") and command.endswith(")"):
            return L_COMMAND
        if command.startswith("@"):
            return A_COMMAND
        return C_COMMAND

    def symbol(self):
        self._ensure_advanced()
        command_type = self.command_type()
        if command_type == L_COMMAND:
            return self.current_command[1:-1].strip()
        if command_type == A_COMMAND:
            return self.current_command[1:].strip()
        raise ValueError("symbol() is only valid for A- and L-commands.")

    def dest(self):
        self._ensure_advanced()
        if "=" not in self.current_command:
            return ""
        return self.current_command.split("=", 1)[0].strip()

    def comp(self):
        self._ensure_advanced()
        command = self.current_command
        if "=" in command:
            command = command.split("=", 1)[1]
        if ";" in command:
            command = command.split(";", 1)[0]
        return command.strip()

    def jump(self):
        self._ensure_advanced()
        if ";" not in self.current_command:
            return ""
        return self.current_command.split(";", 1)[1].strip()

    def _ensure_advanced(self):
        if self.current_index < 0:
            raise RuntimeError("advance() must be called before reading a command.")
