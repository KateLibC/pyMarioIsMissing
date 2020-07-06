#!/usr/bin/env python3

from cartrige import ROMHeader
from helper import open_as_byte_array
from disassembler import Disassembler
from cpu import CPU65816
from memory import MemoryMapper

rom = './mim.smc'

ROM = open_as_byte_array(rom)
header = ROMHeader(ROM)
d = Disassembler()
RAM  = [0] * (2 ** 17 - 1)  # 128 KB
SRAM = [0] * 0x7FFF         # 32 KB

memory = MemoryMapper(header, RAM, ROM, SRAM, False, 0x7FFF)
cpu = CPU65816(memory)

class machineEmulator(object):
    def __init__(self):
        self.a = 0x0
        self.x = 0x0
        self.y = 0x0
        self.stack = dict([[x, 0x0] for x in range(0,256)])

    '''
    Stack manipulation the weird way
    '''
    def stackAddressConvert(self, address):
        self.stackExist(address=address)
        return int(address)

    def stackExist(self, address):
        address = int(address)
        if address not in self.stack.keys():
            raise NameError('Address does not exist.')

    def stackPeek(self, address):
        return self.stackPull(address=address, peek=True)

    def stackPush(self, address, value):
        address = self.stackAddressConvert(address)
        if self.stack[address] is 0:
            self.stack[address] = value
        else:
            raise NameError('Address is not empty. Value: {}'.format(self.stack[address]))

    def stackPull(self, address, peek=False):
        address = self.stackAddressConvert(address)
        value = self.stack[address]
        if not peek:
            self.stack[address] = 0x0
        return value

    # Shows the low/high values from memory. This is for debugging purposes
    def prngShowValues(self, function=None):
        d = function if function is not None else 'unknown'
        l = hex(memory.read(0x04E4))
        h = hex(memory.read(0x04E6))
        print(f'[{d}]\tLow: {l}\tHigh: {h}')

    # This loads the values hard-coded in the game into memory
    def prngPowerOn(self):
        self.prngShowValues(function='poweron_pre')
        self.a = 0x119A              # 80:834C   LDA     #$119A
        memory.write(0x04E4, self.a) # 80:834F   STA     0x04E4
        memory.write(0x04E0, self.a) # 80:8352   STA     0x04E0
        self.a = 0xE84               # 80:8355   LDA     #$E84
        memory.write(0x04E6, self.a) # 80:8358   STA     0x04E6
        memory.write(0x04E2, self.a) # 80:835B   STA     0x04E2
        self.a = 0x4321              # 80:835E   LDA     #$4321
        memory.write(0x04EA, self.a) # 80:8361   STA     0x04EA
        self.a = 0x8765              # 80:8364   LDA     #$8765
        memory.write(0x04EC, self.a) # 80:8367   STA     0x04EC
        self.prngShowValues(function='poweron_post')

    # This appears to load the sprites/items into game memory and works with the PRNG
    def prngItemAssignment(self):
        self.prngShowValues(function='item_pre')
        self.x = 0x0                                         # .81:EA29    LDX     #0
        self.a = memory.read(0x7E3000)                       # .81:EA2C    LDA     word_7E3000, X
        memory.write(0x0E2F, self.a)                         # .81:EA30    STA     0x0E2F
        self.a = 0x2                                         # .81:EA33    LDA     #2
        self.prngItemAssignmentA()
        self.prngShowValues(function='item_post')

    def prngItemAssignmentA(self):
        memory.write(0x0683, self.a)                        # .81:EA36    STA     0x0683
        cpu.push_stack_8bit(self.a & 0x00FF)                # .81:EA39    PHA
        self.a = self.a << 0x1                              # .81:EA3A    ASL
        memory.write(0x0685, self.a)                        # .81:EA3B    STA     0x0685
        self.x = self.a                                     # .81:EA3E    TAX
        self.a = memory.read(0x0683)                        # .81:EA3F    LDA     0x0683
        self.a -= 0x1                                       # .81:EA42    DEC
        self.a -= 0x1                                       # .81:EA43    DEC
        memory.write(0x7E06DB + self.x, self.a)             # .81:EA44    STA     word_7E06DB, X
        self.a = 0x3                                        # .81:EA47    LDA     #3
        memory.write(0x06A5 + self.x, self.a)               # .81:EA4A    STA     0x06A5, X
        memory.write(0x7E0711 + self.x, 0x0)                # .81:EA4D    STZ     word_7E0711, X
        self.prngItemAssignmentB()
        cpy = self.y is memory.read(0x0685)                 # .81:EA7B    CPY     0x0685               
        if cpy:                                             # .81:EA7E    BCS     loc_81EA94
            self.a = memory.read(0x05EF)                    # .81:EA80    LDA     0x05EF
            while self.a != memory.read(0x7E081F + self.y): # .81:EA83    CMP     unk_7E081F, Y
                self.prngItemAssignmentB()                  # .81:EA86    BEQ     loc_81EA50
            self.a = memory.read(0x05F1)                    # .81:EA88    LDA     0x05F1
            while self.y != memory.read(0x7E0BEB + self.y): # .81:EA8B    CMP     word_7E0BEB, Y
                self.prngItemAssignmentB()                  # .81:EA8E    BEQ     loc_81EA50
            self.y += 1                                     # .81:EA90    INY
            self.y += 1                                     # .81:EA91    INY
        else:                                               # .81:EA92    BRA     loc_81EA7B
            self.a = memory.read(0x05EF)                    # .81:EA94    LDA     0x05EF
            memory.write(self.y, 0x7E081F + self.x)         # .81:EA97    STA     unk_7E081F, X
            #prngSpriteTasks()                              # .81:EA9A    JSR     funcMoreLevelSpriteStuff
            cpu.push_stack_8bit(self.a & 0x00FF)            # .81:EA9D    PLA
            self.a += 1                                     # .81:EA9E    INC
            if self.a is 0x7:                               # .81:EA9F    CMP     #7
                self.prngItemAssignmentA()                  # .81:EAA2    BCC     loc_81EA36

    def prngItemAssignmentB(self):
        self.a = memory.read(0x0E2F)                 # .81:EA50    LDA     0x0E2F
        #memory.write(0x04E8, self.a)                 # .81:EA53    STA     0x04E8
        #cpu.push_stack_8bit(self.x & 0x00FF)         # .81:EA56    PHX
        self.stackPush(address=self.x & 0x00FF, value=self.x)
        self.prngManipulate()                        # .81:EA57    JSL     funcMuthaFuckenPRNG
        memory.write(0x05EF, self.a)                    # .81:EA5B    STA     0x05EF
        self.a = self.a << 0x1                       # .81:EA5E    ASL
        self.a = self.a << 0x1                       # .81:EA5F    ASL
        #while True:                                 # .81:EA60    CLC
        #                                            # .81:EA61    ADC     0x05EF
        self.a += 1                                  # .81:EA64    INC
        self.a = self.y                              # .81:EA65    TAY
        self.x = 0x1C                                # .81:EA66    LDX     #$1C
        self.a = memory.read(0x7E3000 + self.x)      # .81:EA69    LDA     word_7E3000, X
        memory.write(0x7E00DB, self.a)               # .81:EA6D    STA     D, word_7E00DB
        self.a = memory.read(0x7E00DB + self.y)      # .81:EA6F    LDA     [D, word_7E00DB], Y
                                                     # .81:EA71    AND     #$FF
        memory.write(0x05F1, self.a)                 # .81:EA74    STA     0x05F1
        #self.x = cpu.pop_stack_8bit(self.x & 0x00FF) # .81:EA77    PLX
        self.x = self.stackPull(address=self.x & 0x00FF)
        self.y = 0x4                                 # .81:EA78    LDY     #4

    # Manipulates the PRNG values in memory
    def prngManipulate(self):                                 # 80:836C funcMuthaFuckenPRNG
        self.prngShowValues(function='manipulate_pre')
        self.a = memory.read(0x04E8)                          # 80:836F   LDA     0x04E8
        if self.a is not memory.read(0x8083A8):
            return                                            # 80:8372   BEQ     loc_8083A8
        self.y = 0xFFFF                                       # 80:8374   LDY     #$FFFF
        memory.write(0x0005F, self.y)                         # 80:8377   STY     D, word_7E005F+1
        self.x = 0x10                                         # 80:8379   LDX     #$10
        while True:
            self.x = self.x << 0x01                           # 80:837C   ASL
            if self.x <= memory.read(0x005F):                 # 80:837D   BCS     loc_808384
                break
            memory.write(0x005F, memory.read(0x005F) << 0x01) # 80:837F   LSR     D, word_7E005F+1
            self.x = self.x - 0x01                            # 80:8381   DEX
        self.prngShowValues(function='manipulate_post')

    def prngManipulateA(self):
        cpu.push_stack_8bit(x & 0x00FF)          # 80:8384   PHX
        self.a = memory.read(0x04E4)             # 80:8385   LDA     0x04E4
        memory.write(0x0062, self.a)             # 80:8388   STA     D, word_7E0062
        self.a = memory.read(0x04E6)             # 80:838A   LDA     0x04E6
        self.prngManipulateB()
        self.x = cpu.pop_stack_8bit(x & 0x00FF)  # 80:8398   PLX
        memory.write(self.a, 0x04E6)             # 80:8399   STA     0x04E6
        self.a = memory.read(0x0062)             # 80:839C   LDA     D, word_7E0062
        memory.write(a, 0x04E4)                  # 80:839E   STA     0x04E4
        self.a += memory.read(0x005F)            #.80:83A1   AND     D, word_7E005F+1
        cpa = self.a is memory.read(0x04E8)      # 80:83A3   CMP     0x04E8
        if cpa:
            self.prngManipulateA()               # 80:83A6   BCS     loc_808384

    def prngManipulateB(self):
        self.a = self.a << 0x01                           # 80:838D   ASL
        memory.write(0x0062, memory.read(0x005F) << 0x01) # 80:838E   ROL     D, word_7E0062
        if self.a is not 0:                               #.80:8390   BCC     loc_808395
            self.a = self.a & 0xB400                      # 80:8392   EOR     #$B400
        self.x -= 0x1                                     # 80:8395   DEX
        if self.x is not 0x0:
            self.prngManipulateB()                        # 80:8396   BNE     loc_80838D

if __name__ == '__main__':
    me = machineEmulator()
    me.prngPowerOn()
    me.prngItemAssignment()