import sys
import os
import glob

class VMTranslator:
    def __init__(self, output_path, is_dir=False):
        self.output_file = open(output_path, 'w', encoding='utf-8')
        self.filename = ""
        self.label_counter = 0
        self.current_function = ""

        self.segment_map = {
            'local': 'LCL',
            'argument': 'ARG',
            'this': 'THIS',
            'that': 'THAT'
        }

        if is_dir:
            self.write_bootstrap()

    def write(self, asm_code):
        self.output_file.write(asm_code + "\n")

    def set_filename(self, filename):
        self.filename = os.path.splitext(os.path.basename(filename))[0]

    def write_bootstrap(self):
        self.write("// Bootstrap")
        self.write("@256\nD=A\n@SP\nM=D")
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, command):
        self.write(f"// {command}")
        if command in ['add', 'sub', 'and', 'or']:
            op_map = {'add': 'D+M', 'sub': 'M-D', 'and': 'D&M', 'or': 'D|M'}
            self.write("@SP\nAM=M-1\nD=M\nA=A-1\nM=" + op_map[command])
        elif command in ['neg', 'not']:
            op_map = {'neg': '-', 'not': '!'}
            self.write("@SP\nA=M-1\nM=" + op_map[command] + "M")
        elif command in ['eq', 'gt', 'lt']:
            jump_map = {'eq': 'JEQ', 'gt': 'JGT', 'lt': 'JLT'}
            lbl_true = f"TRUE_{self.label_counter}"
            lbl_end = f"END_{self.label_counter}"
            self.label_counter += 1

            self.write("@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D")
            self.write(f"@{lbl_true}\nD;{jump_map[command]}")
            self.write("@SP\nA=M-1\nM=0")
            self.write(f"@{lbl_end}\n0;JMP")
            self.write(f"({lbl_true})\n@SP\nA=M-1\nM=-1")
            self.write(f"({lbl_end})")

    def write_push(self, segment, index):
        self.write(f"// push {segment} {index}")
        if segment == 'constant':
            self.write(f"@{index}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        elif segment in self.segment_map:
            base = self.segment_map[segment]
            self.write(f"@{index}\nD=A\n@{base}\nA=D+M\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        elif segment == 'temp':
            self.write(f"@{5 + int(index)}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        elif segment == 'pointer':
            ptr = 'THIS' if index == 0 else 'THAT'
            self.write(f"@{ptr}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        elif segment == 'static':
            self.write(f"@{self.filename}.{index}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1")

    def write_pop(self, segment, index):
        self.write(f"// pop {segment} {index}")
        if segment in self.segment_map:
            base = self.segment_map[segment]
            self.write(f"@{index}\nD=A\n@{base}\nD=D+M\n@R13\nM=D")
            self.write("@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D")
        elif segment == 'temp':
            self.write(f"@SP\nAM=M-1\nD=M\n@{5 + int(index)}\nM=D")
        elif segment == 'pointer':
            ptr = 'THIS' if index == 0 else 'THAT'
            self.write(f"@SP\nAM=M-1\nD=M\n@{ptr}\nM=D")
        elif segment == 'static':
            self.write(f"@SP\nAM=M-1\nD=M\n@{self.filename}.{index}\nM=D")

    def _full_label(self, label):
        return f"{self.current_function}${label}" if self.current_function else label

    def write_label(self, label):
        self.write(f"// label {label}")
        self.write(f"({self._full_label(label)})")

    def write_goto(self, label):
        self.write(f"// goto {label}")
        self.write(f"@{self._full_label(label)}\n0;JMP")

    def write_if(self, label):
        self.write(f"// if-goto {label}")
        self.write(f"@SP\nAM=M-1\nD=M\n@{self._full_label(label)}\nD;JNE")

    def write_function(self, function_name, n_vars):
        self.write(f"// function {function_name} {n_vars}")
        self.current_function = function_name
        self.write(f"({function_name})")
        for _ in range(int(n_vars)):
            self.write("@0\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1")

    def write_call(self, function_name, n_args):
        self.write(f"// call {function_name} {n_args}")
        ret_label = f"RETURN_{function_name}_{self.label_counter}"
        self.label_counter += 1

        self.write(f"@{ret_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        for seg in ['LCL', 'ARG', 'THIS', 'THAT']:
            self.write(f"@{seg}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1")
        self.write(f"@SP\nD=M\n@5\nD=D-A\n@{n_args}\nD=D-A\n@ARG\nM=D")
        self.write("@SP\nD=M\n@LCL\nM=D")
        self.write(f"@{function_name}\n0;JMP")
        self.write(f"({ret_label})")

    def write_return(self):
        self.write("// return")
        self.write("@LCL\nD=M\n@R14\nM=D")
        self.write("@5\nA=D-A\nD=M\n@R15\nM=D")
        self.write("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D")
        self.write("@ARG\nD=M+1\n@SP\nM=D")
        for i, seg in enumerate(['THAT', 'THIS', 'ARG', 'LCL'], start=1):
            self.write(f"@R14\nD=M\n@{i}\nA=D-A\nD=M\n@{seg}\nM=D")
        self.write("@R15\nA=M\n0;JMP")

    def close(self):
        self.output_file.close()


def translate_file(vm_file, translator):
    translator.set_filename(vm_file)
    with open(vm_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.split("//")[0].strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0]

            if cmd in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
                translator.write_arithmetic(cmd)
            elif cmd == 'push':
                translator.write_push(parts[1], int(parts[2]))
            elif cmd == 'pop':
                translator.write_pop(parts[1], int(parts[2]))
            elif cmd == 'label':
                translator.write_label(parts[1])
            elif cmd == 'goto':
                translator.write_goto(parts[1])
            elif cmd == 'if-goto':
                translator.write_if(parts[1])
            elif cmd == 'function':
                translator.write_function(parts[1], int(parts[2]))
            elif cmd == 'call':
                translator.write_call(parts[1], int(parts[2]))
            elif cmd == 'return':
                translator.write_return()


def main():
    if len(sys.argv) < 2:
        print("用法: python vm2asm.py <檔案.vm 或 目錄>")
        sys.exit(1)

    target = sys.argv[1]

    if os.path.isfile(target):
        out_path = os.path.splitext(target)[0] + ".asm"
        translator = VMTranslator(out_path, is_dir=False)
        translate_file(target, translator)
        translator.close()
        print(f"翻譯完成：{out_path}")

    elif os.path.isdir(target):
        dir_name = os.path.basename(os.path.normpath(target))
        out_path = os.path.join(target, f"{dir_name}.asm")
        vm_files = glob.glob(os.path.join(target, "*.vm"))

        has_sys = any("Sys.vm" in os.path.basename(f) for f in vm_files)
        translator = VMTranslator(out_path, is_dir=has_sys)

        for vm_file in vm_files:
            print(f"正在編譯: {os.path.basename(vm_file)}")
            translate_file(vm_file, translator)

        translator.close()
        print(f"目錄翻譯完成：{out_path}")


if __name__ == "__main__":
    main()
