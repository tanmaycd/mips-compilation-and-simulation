
op_map = {
    'add': '000000', 'sub': '000000', 'and': '000000', 'or': '000000', 'slt': '000000',
    'lw': '100011', 'sw': '101011', 'beq': '000100', 'addi': '001000', 'j': '000010'
}

func_map = {
    'add': '100000', 'sub': '100010', 'and': '100100', 'or': '100101', 'slt': '101010'
}

reg_map = {
    '$zero': '00000', '$t0': '01000', '$t1': '01001', '$t2': '01010', '$t3': '01011',
    '$t4': '01100', '$t5': '01101', '$t6': '01110', '$t7': '01111'
}

data_storage = {}
instruction_list = []
label_positions = {}

def process_data(data_lines):
    addr = 0
    for line in data_lines:
        parts = line.split(':')
        label = parts[0].strip()
        value = int(parts[1].strip().split()[1])
        data_storage[label] = addr
        addr += 4

def translate_instruction(instruction, current_addr):
    tokens = instruction.split()
    inst_type = identify_instruction_type(tokens[0])

    if inst_type == 'R':
        return handle_r_type(tokens)
    elif inst_type == 'I':
        return handle_i_type(tokens, current_addr)
    elif inst_type == 'J':
        return handle_j_type(tokens)
    else:
        raise ValueError("Unknown instruction type")

def identify_instruction_type(op):
    if op in ['add', 'sub', 'and', 'or', 'slt']:
        return 'R'
    elif op in ['lw', 'sw', 'beq', 'addi']:
        return 'I'
    elif op == 'j':
        return 'J'
    else:
        raise ValueError(f"Invalid operation: {op}")

def sanitize_register(reg):
    return reg.replace(',', '')

def handle_r_type(tokens):
    opcode = op_map[tokens[0]]
    rs = reg_map[sanitize_register(tokens[2])]
    rt = reg_map[sanitize_register(tokens[3])]
    rd = reg_map[sanitize_register(tokens[1])]
    shamt = '00000'
    funct = func_map[tokens[0]]
    return f'{opcode}{rs}{rt}{rd}{shamt}{funct}'

def handle_i_type(tokens, current_addr):
    opcode = op_map[tokens[0]]
    rt = reg_map[sanitize_register(tokens[1])]
    rs = reg_map[sanitize_register(tokens[2])] if tokens[0] != 'lw' else reg_map['$zero']

    if tokens[0] == 'addi':
        imm = format(int(tokens[3]), '016b')
        return f'{opcode}{rs}{rt}{imm}'

    elif tokens[0] in ['lw', 'sw'] and sanitize_register(tokens[2]) in data_storage:
        address = data_storage[sanitize_register(tokens[2])]
        imm = format(address, '016b')
        return f'{opcode}{rs}{rt}{imm}'

    elif tokens[0] == 'beq':
        rs = reg_map[sanitize_register(tokens[1])]
        rt = reg_map[sanitize_register(tokens[2])]
        label = sanitize_register(tokens[3])
        branch_addr = label_positions[label] - (current_addr + 4)
        imm = format(branch_addr // 4, '016b')
        return f'{opcode}{rs}{rt}{imm}'

def handle_j_type(tokens):
    opcode = op_map[tokens[0]]
    label = sanitize_register(tokens[1])
    addr = label_positions[label] // 4
    return f'{opcode}{format(addr, "026b")}'

def first_pass(file_lines):
    current_addr = 0
    for line in file_lines:
        line = line.strip()
        if line.endswith(':'):
            label = line[:-1]
            label_positions[label] = current_addr
        else:
            if not (line.startswith('.data') or line.startswith('.text')):
                current_addr += 4

def assemble_mips(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    first_pass(lines)

    in_data_section = False
    in_text_section = False
    current_addr = 0

    for line in lines:
        line = line.strip()

        if line.startswith('.data'):
            in_data_section = True
            in_text_section = False
            continue
        elif line.startswith('.text'):
            in_data_section = False
            in_text_section = True
            continue

        if in_data_section and line:
            process_data([line])
        elif in_text_section and line:
            if not line.endswith(':'):
                binary_instruction = translate_instruction(line, current_addr)
                instruction_list.append((line, binary_instruction))  # Store both MIPS and binary
                current_addr += 4

    return instruction_list

def display_comparison(instructions):
    print(f"{'MIPS Code':<40} {'Binary Code'}")
    print("=" * 80)
    for mips, binary in instructions:
        print(f"{mips:<40} {binary}")

file_path = './mips_code_5.txt'
compiled_code = assemble_mips(file_path)

display_comparison(compiled_code)
