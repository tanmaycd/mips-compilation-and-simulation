class MIPSCompiler:
    def __init__(self):
        self.registers = {
            '$zero': 0, '$0': 0,
            '$at': 1, '$v0': 2, '$v1': 3,
            '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
            '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
            '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
            '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
            '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
            '$t8': 24, '$t9': 25,
            '$k0': 26, '$k1': 27,
            '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31
        }

       
        self.r_type = {
            'add': {'opcode': '000000', 'funct': '100000'},
            'sub': {'opcode': '000000', 'funct': '100010'},
            'and': {'opcode': '000000', 'funct': '100100'},
            'or':  {'opcode': '000000', 'funct': '100101'},
            'slt': {'opcode': '000000', 'funct': '101010'}
        }

        self.i_type = {
            'lw':   '100011',
            'sw':   '101011',
            'beq':  '000100',
            'addi': '001000'
        }

        self.j_type = {
            'j': '000010'
        }

        self.data_section = {}
        self.labels = {}
        self.current_address = 0x00400000
        self.data_start_address = 0x10010000

    def parse_data_section(self, line):
        parts = line.strip().split()
        if len(parts) >= 2:
            label = parts[0].rstrip(':')
            data_type = parts[1]
            value = ' '.join(parts[2:])

            if data_type == '.word':
                values = [int(v) for v in value.split()]
                self.data_section[label] = {
                    'type': data_type,
                    'value': values[0],
                    'address': self.data_start_address
                }
                self.data_start_address += 4

    def compile_instruction(self, instruction, line_address):
        parts = instruction.strip().replace(',', '').split()
        if not parts:
            return None

        
        if parts[0].endswith(':'):
            label = parts[0][:-1]
            self.labels[label] = line_address
            parts = parts[1:]
            if not parts:
                return None

        op = parts[0].lower()
        
        if op in self.r_type:
            opcode = self.r_type[op]['opcode']
            funct = self.r_type[op]['funct']
            rd = parts[1]
            rs = parts[2]
            rt = parts[3]
            binary = f"{opcode}{self.registers[rs]:05b}{self.registers[rt]:05b}{self.registers[rd]:05b}00000{funct}"
            return {'binary': binary, 'original': instruction.strip()}

        elif op in self.i_type:
            opcode = self.i_type[op]
            
            if op in ['lw', 'sw']:
                rt = parts[1]
                if '(' in parts[2]:  # Offset(base) format
                    offset_base = parts[2].split('(')
                    base_register = offset_base[1].strip(')')
                    imm = format(int(offset_base[0]), '016b')
                else:  # Handle label
                    label = parts[2]
                    if label in self.data_section:
                        imm = format(self.data_section[label]['address'] - self.data_start_address, '016b')
                    else:
                        imm = '0000000000000000'
                    base_register = '$zero'
                    
                rs = base_register
                binary = f"{opcode}{self.registers[rs]:05b}{self.registers[rt]:05b}{imm}"

           
            elif op == 'addi':
                rt = parts[2] 
                rs = parts[1] 
                imm = int(parts[3]) 
                
                imm = format(imm & 0xFFFF, '016b')
                binary = f"{opcode}{self.registers[rt]:05b}{self.registers[rs]:05b}{imm}"

           
            elif op == 'beq':
                rs = parts[1]
                rt = parts[2]
                label = parts[3]
                
                if label in self.labels:
                    offset = (self.labels[label] - (line_address + 4)) // 4
                    imm = format(offset & 0xFFFF, '016b')
                else:
                    imm = '0000000000000000'
                
                binary = f"{opcode}{self.registers[rs]:05b}{self.registers[rt]:05b}{imm}"

            return {'binary': binary, 'original': instruction.strip()}

        
        elif op in self.j_type:
            opcode = self.j_type[op]
            try:
                target = int(parts[1])
            except ValueError:
                if parts[1] in self.labels:
                    target = self.labels[parts[1]] // 4
                else:
                    target = 0

            binary = f"{opcode}{format(target & 0x3FFFFFF, '026b')}"
            return {'binary': binary, 'original': instruction.strip()}

        return None

    def compile_file(self, filename="task1.txt"):
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            return [], {}

        text_section = False
        data_section = False
        compiled_instructions = []
        current_address = self.current_address

       
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '.data' in line:
                data_section = True
                text_section = False
                continue
            elif '.text' in line:
                text_section = True
                data_section = False
                continue
            
            if data_section:
                self.parse_data_section(line)
            elif text_section and ':' in line:
                label = line.split(':')[0]
                self.labels[label] = current_address
            
            if text_section and not line.strip().endswith(':'):
                current_address += 4

        
        text_section = False
        current_address = self.current_address
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '.text' in line:
                text_section = True
                continue
            elif '.data' in line:
                text_section = False
                continue
            
            if text_section and not line.endswith(':'):
                compiled = self.compile_instruction(line, current_address)
                if compiled:
                    compiled['address'] = format(current_address, '08x')
                    compiled_instructions.append(compiled)
                    current_address += 4

        return compiled_instructions, self.data_section



class MIPSSimulator:
    def __init__(self, compiler):
        self.compiler = compiler
        self.registers = {f'${i}': 0 for i in range(32)}  
        self.memory = {} 
        self.pc = 0x00400000  
        
        
        self.registers['$zero'] = 0  
        self.registers['$sp'] = 0x7FFFFFFC 
        
        
        self.alu_ops = {
            'add': lambda x, y: x + y,
            'sub': lambda x, y: x - y,
            'and': lambda x, y: x & y,
            'or':  lambda x, y: x | y,
            'slt': lambda x, y: 1 if x < y else 0,
        }

    def reset(self):
        """Reset the simulator state"""
        self.__init__(self.compiler)

    def get_control_signals(self, instruction):
        """Generate control signals based on instruction type"""
        op = instruction['binary'][:6]
        
        signals = {
            'RegDst': 0, 'ALUSrc': 0, 'MemtoReg': 0,
            'RegWrite': 0, 'MemRead': 0, 'MemWrite': 0,
            'Branch': 0, 'Jump': 0, 'ALUOp': '00'
        }
        
       
        if op == '000000':
            signals['RegDst'] = 1
            signals['RegWrite'] = 1
            signals['ALUOp'] = '10'
        
        
        elif op == '100011':
            signals['ALUSrc'] = 1
            signals['MemtoReg'] = 1
            signals['RegWrite'] = 1
            signals['MemRead'] = 1
            signals['ALUOp'] = '00'
        
       
        elif op == '101011':
            signals['ALUSrc'] = 1
            signals['MemWrite'] = 1
            signals['ALUOp'] = '00'
        
       
        elif op == '000100':
            signals['Branch'] = 1
            signals['ALUOp'] = '01'
        
        
        elif op == '000010':
            signals['Jump'] = 1
        
        return signals

    def load_data_to_memory(self):
        """Load data section into simulated memory."""
        for label, value in self.compiler.data_section.items():
            address = 0x10010000 + list(self.compiler.data_section.keys()).index(label) * 4
            self.memory[address] = value  
            print(f"Loaded {value} into memory at address 0x{address:08x}")



    def display_initial_memory(self):
        """Display the initial memory state."""
        print("Initial Memory State:")
        for addr in sorted(self.memory.keys()):
            print(f"0x{addr:08x}: {self.memory[addr]}")
        print("-" * 30) 

    def execute_instruction(self, instruction):
        """Execute a single instruction."""
        binary = instruction['binary']
        op = binary[:6]

       
        if op == '000000':
            rs = int(binary[6:11], 2)
            rt = int(binary[11:16], 2)
            rd = int(binary[16:21], 2)
            funct = binary[26:32]

           
            rs_value = self.registers[f'${rs}']
            rt_value = self.registers[f'${rt}']
            if funct == '100000':  # add
                self.registers[f'${rd}'] = self.alu_ops['add'](rs_value, rt_value)
            elif funct == '100010':  # sub
                self.registers[f'${rd}'] = self.alu_ops['sub'](rs_value, rt_value)
            elif funct == '100100':  # and
                self.registers[f'${rd}'] = self.alu_ops['and'](rs_value, rt_value)
            elif funct == '100101':  # or
                self.registers[f'${rd}'] = self.alu_ops['or'](rs_value, rt_value)
            elif funct == '101010':  # slt
                self.registers[f'${rd}'] = self.alu_ops['slt'](rs_value, rt_value)

           
            self.pc += 4

        
        elif op == '001000': 
            rs = int(binary[6:11], 2)  
            rt = int(binary[11:16], 2)  
            imm = int(binary[16:], 2) 

          
            if imm >= 2**15:
                imm -= 2**16

          
            self.registers[f'${rt}'] = (self.registers[f'${rs}'] + imm) & 0xFFFFFFFF

            print(f"Executed addi: ${rt} = {self.registers[f'${rt}']} (rs: ${rs} + imm: {imm})")
            self.pc += 4

        elif op == '100011':  # lw opcode
            rt = int(binary[11:16], 2)  # Destination register

           
            label = instruction['original'].split()[2]
            if label in self.compiler.data_section:
               
                value = self.compiler.data_section[label]['value']
              
                self.registers[f'${rt}'] = value
                print(f"Loaded value {value} from label {label} into register ${rt}")
            else:
              
                rs = int(binary[6:11], 2)  # Base register
                imm = int(binary[16:], 2)  # Immediate value
                
                if imm >= 2**15:  
                    imm -= 2**16

                base_value = self.registers[f'${rs}']  # Value in the base register
                address = base_value + imm  # Effective memory address
                self.registers[f'${rt}'] = self.memory.get(address, 0)  # Load value from memory
                print(f"Loaded from address 0x{address:08x} into register ${rt} with value {self.registers[f'${rt}']}")

        # Store word
        elif op == '101011':
            rs = int(binary[6:11], 2)  # base register
            rt = int(binary[11:16], 2)  # source register
            imm = int(binary[16:], 2)   # offset

            base_value = self.registers[f'${rs}']
            address = base_value + imm
            self.memory[address] = self.registers[f'${rt}']  # Store value in memory
            self.pc += 4

        # Branch if equal
        elif op == '000100':
            rs = int(binary[6:11], 2)
            rt = int(binary[11:16], 2)
            imm = int(binary[16:], 2)
            # Before beq execution
            print(f"Executing beq: $rs={rs} ($t0={self.registers[f'${rs}']}), $rt={rt} ($t1={self.registers[f'${rt}']})")

            if self.registers[f'${rs}'] == self.registers[f'${rt}']:
                self.pc += imm * 4  # Branch
            else:
                self.pc += 4  

        # Jump instruction
        elif op == '000010':
            address = int(binary[6:], 2)  # Target address
            self.pc = (self.pc & 0xF0000000) | (address << 2)  # Jump to address

    def execute_program(self, instructions):
        """Execute all instructions in the program."""
        self.reset()
        
       
        self.load_data_to_memory()
        self.display_initial_memory()  # Show initial memory

        execution_trace = []
        
        for instruction in instructions:
            # Record state before execution
            state = {
                'pc': hex(self.pc),
                'instruction': instruction['original'],
                'registers': self.registers.copy(),
                'memory': self.memory.copy()
            }
            
            # Execute instruction
            self.execute_instruction(instruction)
            
            # Record state after execution
            state['next_pc'] = hex(self.pc)
            execution_trace.append(state)
            
          
            print(f"\nAfter executing: {instruction['original']}")
            print("Registers:")
            for reg, value in self.registers.items():
                print(f"{reg}: {value}")
            print("-" * 30)  

        return execution_trace


def main():
    compiler = MIPSCompiler()
    test_file = "mips_code_5.txt"
    instructions, data_section = compiler.compile_file(test_file)
    simulator = MIPSSimulator(compiler)
    simulator.load_data_to_memory()
    execution_trace = simulator.execute_program(instructions)
    print("\nFinal register  State")
    for reg, value in simulator.registers.items():
        print(f"{reg}: {value}")
    print("\nFinal memory state:")
    for addr, value in sorted(simulator.memory.items()):
        print(f"0x{addr:08x}: {value}")


if __name__ == "__main__":
    main()

//main file
