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

    def prngLevelLoad(self):
        self.prngLoadObjects()       # .81:E920 JSR     funcLevelLoadObjects?
        self.a = 0x0                 # .81:E923 LDA     #0
        memory.write(0x06A7, self.a) # .81:E926 STA     word_7E06A7 ; orig=0x06A7
        self.a = 0x40                # .81:E929 LDA     #$40 ; '@'
        memory.write(0x0E31, self.a) # .81:E92C STA     word_7E0E31 ; orig=0x0E31
        self.prngItemAssignment()    # .81:E92F JSR     funcItemAssignmentPRNG
        # To be implemented          # .81:E932 JSR     funcAnotherFuckenPRNGItem
        # To be implemented          # .81:E935 JSR     funcAssignSpritesToObjects?
        self.prngSpritePlacement()   # .81:E938 JSR     funcSpritePlacement?

    def prngLoadObjects(self):
        memory.write(0x0683, 0x0)                      # .81:E93C STZ     word_7E0683 ; orig=0x0683
        memory.write(0x0685, 0x0)                      # .81:E93F STZ     word_7E0685 ; orig=0x0685
        self.a = 0x0                                   # .81:E942 LDA     #0
        memory.write(0x06DB, self.a)                   # .81:E945 STA     word_7E06DB ; orig=0x06DB
        self.a = 0xFFFF                                # .81:E948 LDA     #$FFFF
        memory.write(0x06A3, self.a)                   # .81:E94B STA     word_7E06A3 ; orig=0x06A3
        self.prngLevelLoadA()                          # .81:E94E JSR     sub_81FF03
        memory.write(0x06A5, 0x0)                      # .81:E951 STZ     SpriteAction? ; orig=0x06A5
        memory.write(0x0711, 0x0)                      # .81:E954 STZ     word_7E0711 ; orig=0x0711
        self.a = 0x03                                  # .81:E957 LDA     #3
        memory.write(0x07B3, self.a)                   # .81:E95A STA     word_7E07B3 ; orig=0x07B3
        self.x = 0x0C                                  # .81:E95D LDX     #$C
        memory.write(0x3000 + self.x, self.a)          # .81:E960 LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                   # .81:E964 STA     D, word_7E00DB
        self.x = 0x02                                  # .81:E966 LDX     #2
        self.a = memory.read(0x3000 + self.x)          # .81:E969 LDA     word_7E3000, X
        memory.write(0x0A3B, self.a)                   # .81:E96D STA     word_7E0A3B ; orig=0x0A3B
        memory.write(0x0A71, self.a)                   # .81:E970 STA     word_7E0A71 ; orig=0x0A71
        self.a = self.a << 1                           # .81:E973 ASL
        self.a = self.a << 1                           # .81:E974 ASL
        self.y = self.a                                # .81:E975 TAY
        self.a = memory.read(0x00DB + self.y)          # .81:E976 LDA     [D, word_7E00DB], Y
        memory.write(0x0747, self.a)                   # .81:E978 STA     word_7E0747 ; orig=0x0747
        memory.write(0x0963, self.a)                   # .81:E97B STA     word_7E0963 ; orig=0x0963
        memory.write(0x09CF, self.a)                   # .81:E97E STA     word_7E09CF ; orig=0x09CF
        self.y = self.y + 1                            # .81:E981 INY
        self.y = self.y + 1                            # .81:E982 INY
        self.a = memory.read(0x00DB)                   # .81:E983 LDA     [D, word_7E00DB], Y
        memory.write(0x077D, self.a)                   # .81:E985 STA     word_7E077D ; orig=0x077D
        memory.write(0x0999, self.a)                   # .81:E988 STA     word_7E0999 ; orig=0x0999
        memory.write(0x0A05, self.a)                   # .81:E98B STA     word_7E0A05 ; orig=0x0A05
        self.a = memory.read(0x0A71)                   # .81:E98E LDA     word_7E0A71 ; orig=0x0A71
        self.a = self.a << 1                           # .81:E991 ASL
        self.a = self.a << 1                           # .81:E992 ASL
        # .81:E993 CLC
        self.a = memory.read(0x0A71) + self.a          # .81:E994 ADC     word_7E0A71 ; orig=0x0A71
        self.a = self.a + 1                            # .81:E997 INC
        self.y = self.a                                # .81:E998 TAY
        self.x = 0x1C                                  # .81:E999 LDX     #$1C
        self.a = memory.read(0x3000 + self.x)          # .81:E99C LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                   # .81:E9A0 STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)          # .81:E9A2 LDA     [D, word_7E00DB], Y
        self.a = self.a & 0xFF                         # .81:E9A4 AND     #$FF
        memory.write(0x0BEB, self.a)                   # .81:E9A7 STA     word_7E0BEB ; orig=0x0BEB
        memory.write(0x0BED, self.a)                   # .81:E9AA STA     word_7E0BED ; orig=0x0BED
        self.a = self.y                                # .81:E9AD TYA
        self.a = self.a << 1                           # .81:E9AE ASL
        self.y = self.a                                # .81:E9AF TAY
        self.x = 0x18                                  # .81:E9B0 LDX     #$18
        self.a = memory.read(0x3000 + self.x)          # .81:E9B3 LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                   # .81:E9B7 STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)          # .81:E9B9 LDA     [D, word_7E00DB], Y
        memory.write(0x0C21, self.a)                   # .81:E9BB STA     word_7E0C21 ; orig=0x0C21
        self.a = self.a << 1                           # .81:E9BE ASL
        self.a = self.a << 1                           # .81:E9BF ASL
        self.a = self.a << 1                           # .81:E9C0 ASL
        self.a = self.a << 1                           # .81:E9C1 ASL
        memory.write(0x08C1, self.a)                   # .81:E9C2 STA     word_7E08C1 ; orig=0x08C1
        memory.write(0x0855, self.a)                   # .81:E9C5 STA     word_7E0855 ; orig=0x0855
        memory.write(0x0857, self.a)                   # .81:E9C8 STA     word_7E0857 ; orig=0x0857
        memory.write(0x0F39, self.a)                   # .81:E9CB STA     word_7E0F39 ; orig=0x0F39
        self.a = memory.read(0x0BEB)                   # .81:E9CE LDA     word_7E0BEB ; orig=0x0BEB
        self.a = self.a << 1                           # .81:E9D1 ASL
        self.y = self.a                                # .81:E9D2 TAY
        self.x = 0x16                                  # .81:E9D3 LDX     #$16
        self.a = memory.read(0x3000 + self.x)          # .81:E9D6 LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                   # .81:E9DA STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)          # .81:E9DC LDA     [D, word_7E00DB], Y
        self.a = self.a << 1                           # .81:E9DE ASL
        self.a = self.a << 1                           # .81:E9DF ASL
        self.a = self.a << 1                           # .81:E9E0 ASL
        self.a = self.a << 1                           # .81:E9E1 ASL
        memory.write(0x0C57, self.a)                   # .81:E9E2 STA     word_7E0C57 ; orig=0x0C57
        self.x = 0x10                                  # .81:E9E5 LDX     #$10
        self.a = memory.read(0x3000 + self.x)          # .81:E9E8 LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                   # .81:E9EC STA     D, word_7E00DB
        self.x = memory.read(0x0685)                   # .81:E9EE LDX     word_7E0685 ; orig=0x0685
        self.a = memory.read(0x0a71 + self.x)          # .81:E9F1 LDA     word_7E0A71, X
        self.a = self.a << 1                           # .81:E9F4 ASL
        self.a = self.a << 1                           # .81:E9F5 ASL
        self.a = self.a << 1                           # .81:E9F6 ASL
        # .81:E9F7 CLC
        self.a = self.a & memory.read(0x0BB5 + self.x) # .81:E9F8 ADC     word_7E0BB5, X
        self.a = self.a & memory.read(0x0BB5 + self.x) # .81:E9FB ADC     word_7E0BB5, X
        self.y = self.a                                # .81:E9FE TAY
        self.a = memory.read(0x00DB + self.y)          # .81:E9FF LDA     [D, word_7E00DB], Y
        memory.write(0x0B75 + self.x, self.a)          # .81:EA01 STA     word_7E0B7F, X
        memoryw.rite(0x08F7 + self.x, 0x0)             # .81:EA04 STZ     word_7E08F7, X
        self.x = 0x0A                                  # .81:EA07 LDX     #$A
        self.a =                                       # .81:EA0A LDA     word_7E3000, X
        memory.write(0x0D9B, self.a)                   # .81:EA0E STA     word_7E0D9B ; orig=0x0D9B
        self.y = memory.read(0x0BEB)                   # .81:EA11 LDY     word_7E0BEB ; orig=0x0BEB
        self.a = memory.read(0x0C21)                   # .81:EA14 LDA     word_7E0C21 ; orig=0x0C21
        self.prngLevelLoadB()                          # .81:EA17 JSL     sub_809F8D      
        self.a = 0x1F                                  # .81:EA1B LDA     #$1F
        memory.write(0x212C, self.a)                   # .81:EA1E STA     TM ; orig=0x212C ; Main Screen Designation (000abcde a = Object b = Bg4 c = Bg3 d = Bg2 e = Bg1)
        memory.write(0x067B, 0x0)                      # .81:EA21 STZ     word_7E067B ; orig=0x067B
        # Likely we can ignore this due to input func  # .81:EA24 JSL     sub_80828C

    def prngLevelLoadA(self):
        self.a = memory.read(0x06DB)                   # .81:FF03 LDA     word_7E06DB ; orig=0x06DB
        if self.a is not memory.read(0x06A3):          # .81:FF06 CMP     word_7E06A3 ; orig=0x06A3
            # Buffer                                   # .81:FF09 BNE     loc_81FF0C
            # Buffer                                   # .81:FF0C loc_81FF0C:                             ; CODE XREF: sub_81FF03+6↑j
            memory.write(0x06A3, self.a)               # .81:FF0C STA     word_7E06A3 ; orig=0x06A3
            self.a = self.a << 1                       # .81:FF0F ASL
            self.a = self.a << 1                       # .81:FF10 ASL
            self.y = self.a                            # .81:FF11 TAY
            self.a = memory.read(0x81FF4D + self.y)    # .81:FF12 LDA     word_81FF4D, Y
            memory.write(0x005D, self.a)               # .81:FF15 STA     D, word_7E005D
            self.a = memory.read(0x81FF4F + self.y)    # .81:FF17 LDA     word_81FF4F, Y
            memory.write(0x005F, self.a)               # .81:FF1A STA     D, word_7E005F
            self.a = 0x0800                            # .81:FF1C LDA     #$800
            self.prngLevelLoadC()                      # .81:FF1F JSL     sub_808781
            self.a = memory.read(0x06A3)               # .81:FF23 LDA     word_7E06A3 ; orig=0x06A3
            if self.a is not memory.read(0x06A3):      # .81:FF26 BNE     loc_81FF32
                self.a = 0x5B                          # .81:FF28 LDA     #$5B ; '['
                self.prngLevelLoadD()                  # .81:FF2B JSR     sub_81ECF1
                self.a += 1                            # .81:FF2E INC
                self.prngLevelLoadD()                  # .81:FF2F JSR     sub_81ECF1
        else:                                          # .81:FF32 loc_81FF32:                             ; CODE XREF: sub_81FF03+23↑j
            self.a = memory.read(0x6DB)                # .81:FF32 LDA     word_7E06DB ; orig=0x06DB
            self.a = self.a << 1                       # .81:FF35 ASL
            self.y = self.a                            # .81:FF36 TAY
            self.a = memory.read(0x81FF55)             # .81:FF37 LDA     word_81FF55, Y
            memory.write(0x0E4B, self.a)               # .81:FF3A STA     word_7E0E4B ; orig=0x0E4B
            self.a = memory.read(0x81FF59, self.y)     # .81:FF3D LDA     word_81FF59, Y
            memory.write(0x0E57, self.a)               # .81:FF40 STA     word_7E0E57 ; orig=0x0E57
            self.a = memory.read(0x0855)               # .81:FF43 LDA     word_7E0855 ; orig=0x0855
            self.a = self.a & 0xFFFE                   # .81:FF46 AND     #$FFFE
            memory.write(0x0855, self.a)               # .81:FF49 STA     word_7E0855 ; orig=0x0855

    def prngLevelLoadB(self):
        # .80:9F8D PHP
        # .80:9F8E PHB
        # .80:9F8F PHK
        # .80:9F90 PLB
        # .80:9F91 ; ds=80000 B=80
        # .80:9F91 REP     #$30 ; '0'
        # .80:9F93 STA     word_7E0E5F ; orig=0x0E5F
        self.a = self.a << 1                       # .80:9F96 ASL
        self.a = self.a << 1                       # .80:9F97 ASL
        self.a = self.a << 1                       # .80:9F98 ASL
        self.a = self.a << 1                       # .80:9F99 ASL
        # .80:9F9A STA     word_7E0F39 ; orig=0x0F39
        # .80:9F9D STA     word_7E0F2D ; orig=0x0F2D
        # .80:9FA0 TYA
        self.a = self.a << 1                       # .80:9FA1 ASL
        # .80:9FA2 TAY
        # .80:9FA3 LDX     #$1A
        # .80:9FA6 LDA     word_7E3000, X
        # .80:9FAA STA     D, word_7E005D
        # .80:9FAC LDA     #$7E ; '~'
        # .80:9FAF STA     D, word_7E005F
        # .80:9FB1 STA     D, word_7E006F
        # .80:9FB3 LDA     [D, word_7E005D], Y
        # .80:9FB5 STA     D, word_7E006D
        # .80:9FB7 LDX     #$16
        # .80:9FBA LDA     word_7E3000, X
        # .80:9FBE STA     D, word_7E005D
        # .80:9FC0 LDA     [D, word_7E005D], Y
        # .80:9FC2 STA     word_7E0F3D ; orig=0x0F3D
        self.a = self.a << 1                       # .80:9FC5 ASL
        self.a = self.a << 1                       # .80:9FC6 ASL
        self.a = self.a << 1                       # .80:9FC7 ASL
        self.a = self.a << 1                       # .80:9FC8 ASL
        # .80:9FC9 STA     word_7E0F41 ; orig=0x0F41
        # .80:9FCC SEC
        # .80:9FCD LDA     word_7E0F3D ; orig=0x0F3D
        # .80:9FD0 SBC     #$10
        # .80:9FD3 STA     word_7E0F3F ; orig=0x0F3F
        # .80:9FD6 LDA     word_7E0E5F ; orig=0x0E5F
        # .80:9FD9 STA     word_7E0E63 ; orig=0x0E63
        # .80:9FDC LDA     #0
        # .80:9FDF STA     word_7E0F31 ; orig=0x0F31
        # .80:9FE2 LDX     #$12
        # .80:9FE5
        # .80:9FE5 loc_809FE5:                             ; CODE XREF: sub_809F8D+71↓j
        # .80:9FE5 LDA     word_7E0E63 ; orig=0x0E63
        # .80:9FE8 CMP     word_7E0F3D ; orig=0x0F3D
        # .80:9FEB BCS     loc_80A000
        # .80:9FED PHA
        # .80:9FEE AND     #$1F
        # .80:9FF1 STA     word_7E0F29 ; orig=0x0F29
        # .80:9FF4 PLA
        # .80:9FF5 PHX
        self.prngLevelLoadE() # .80:9FF6 JSR     sub_80A0C5
        # .80:9FF9 INC     word_7E0E63 ; orig=0x0E63
        # .80:9FFC PLX
        # .80:9FFD DEX
        # .80:9FFE BNE     loc_809FE5
        # .80:A000
        # .80:A000 loc_80A000:                             ; CODE XREF: sub_809F8D+5E↑j
        # .80:A000 LDA     word_7E0E5F ; orig=0x0E5F
        # .80:A003 DEC
        # .80:A004 STA     word_7E0E61 ; orig=0x0E61
        # .80:A007 LDA     #2
        # .80:A00A STA     word_7E0F31 ; orig=0x0F31
        # .80:A00D LDX     #$12
        # .80:A010
        # .80:A010 loc_80A010:                             ; CODE XREF: sub_809F8D+99↓j
        # .80:A010 LDA     word_7E0E61 ; orig=0x0E61
        # .80:A013 BMI     loc_80A028
        # .80:A015 PHA
        # .80:A016 AND     #$1F
        # .80:A019 STA     word_7E0F2B ; orig=0x0F2B
        # .80:A01C PLA
        # .80:A01D PHX
        self.prngLevelLoadE() # .80:A01E JSR     sub_80A0C5
        # .80:A021 DEC     word_7E0E61 ; orig=0x0E61
        # .80:A024 PLX
        # .80:A025 DEX
        # .80:A026 BNE     loc_80A010
        # .80:A028
        # .80:A028 loc_80A028:                             ; CODE XREF: sub_809F8D+86↑j
        # .80:A028 SEC
        # .80:A029 LDA     word_7E0F3D ; orig=0x0F3D
        # .80:A02C SBC     #8
        # .80:A02F CMP     word_7E0E5F ; orig=0x0E5F
        # .80:A032 BCS     loc_80A040
        # .80:A034 SEC
        # .80:A035 LDA     word_7E0F3D ; orig=0x0F3D
        # .80:A038 SBC     #$10
        # .80:A03B AND     #$1F
        # .80:A03E BRA     loc_80A054
        # .80:A040 ; ---------------------------------------------------------------------------
        # .80:A040
        # .80:A040 loc_80A040:                             ; CODE XREF: sub_809F8D+A5↑j
        # .80:A040 LDA     word_7E0E5F ; orig=0x0E5F
        # .80:A043 CMP     #9
        # .80:A046 BCS     loc_80A04D
        # .80:A048 LDA     #0
        # .80:A04B BRA     loc_80A054
        # .80:A04D ; ---------------------------------------------------------------------------
        # .80:A04D
        # .80:A04D loc_80A04D:                             ; CODE XREF: sub_809F8D+B9↑j
        # .80:A04D SEC
        # .80:A04E SBC     #8
        # .80:A051 AND     #$1F
        # .80:A054
        # .80:A054 loc_80A054:                             ; CODE XREF: sub_809F8D+B1↑j
        # .80:A054                                         ; sub_809F8D+BE↑j
        self.a = self.a << 1                       # .80:A054 ASL
        self.a = self.a << 1                       # .80:A055 ASL
        self.a = self.a << 1                       # .80:A056 ASL
        self.a = self.a << 1                       # .80:A057 ASL
        # .80:A058 STA     D, word_7E004D
        # .80:A05A STZ     word_7E0F37 ; orig=0x0F37
        # .80:A05D STZ     D, word_7E0051
        # .80:A05F PLB
        # .80:A060 PLP
        pass

    def prngLevelLoadC(self):
        # .80:8781    PHP
        # .80:8782    REP     #$20 ; ' '
        # .80:8784    SEP     #$10
        # .80:8786 .I8
        # .80:8786    STA     D, word_7E002A
        # .80:8788    LDA     [D, word_7E005D]
        # .80:878A    STA     D, word_7E002C
        # .80:878C    LDX     #0
        # .80:878E    STX     D, byte_7E002E
        # .80:8790    LDA     #$8000
        # .80:8793    STA     D, word_7E002F
        # .80:8795    LDX     #$7F
        # .80:8797    STX     D, word_7E0031
        # .80:8799    INC     D, word_7E005D
        # .80:879B    INC     D, word_7E005D
        # .80:879D    JSL     sub_808BB7
        # .80:87A1    LDA     #$2A ; '*'
        # .80:87A4    STA     D, word_7E0018
        # .80:87A6    LDX     #0
        # .80:87A8    STX     D, word_7E001A
        self.prngSpriteWorker() # .80:87AA    JSL     sub_808506
        # .80:87AE    PLP
        pass

    def prngLevelLoadD(self):
        # .81:ECF1 PHA
        # .81:ECF2 STA     word_7E05DB ; orig=0x05DB
        # .81:ECF5 AND     #7
        self.a = self.a << 1                       # .81:ECF8 ASL
        # .81:ECF9 TAY
        # .81:ECFA LDA     word_7E05DB ; orig=0x05DB
        # .81:ECFD LSR
        # .81:ECFE LSR
        # .81:ECFF AND     #$FE
        # .81:ED02 TAX
        # .81:ED03 LDA     byte_7E0400, X
        # .81:ED06 ORA     word_8180E4, Y
        # .81:ED09 STA     byte_7E0400, X
        # .81:ED0C LDA     word_7E05DB ; orig=0x05DB
        self.a = self.a << 1                       # .81:ED0F ASL
        self.a = self.a << 1                       # .81:ED10 ASL
        # .81:ED11 TAY
        # .81:ED12 LDA     #$80
        # .81:ED15 STA     word_7E0200, Y
        # .81:ED18 PLA
        # .81:ED19 RTS
        pass

    def prngLevelLoadE(self):
        # .80:A0C5 CMP     word_7E0F3D ; orig=0x0F3D
        # .80:A0C8 BCC     loc_80A0D6
        # .80:A0CA LDX     #$7E ; '~'
        # .80:A0CD loc_80A0CD:                             ; CODE XREF: sub_80A0C5+D↓j
        # .80:A0CD STZ     unk_7E0EA5, X
        # .80:A0D0 DEX
        # .80:A0D1 DEX
        # .80:A0D2 BPL     loc_80A0CD
        # .80:A0D4 BRA     loc_80A106
        # .80:A0D6 loc_80A0D6:                             ; CODE XREF: sub_80A0C5+3↑j
        # .80:A0D6 ASL
        # .80:A0D7 PHA
        self.a = self.a << 1                       # .80:A0D8 ASL
        # .80:A0D9 PHA
        # .80:A0DA ASL
        # .80:A0DB STA     word_7E0F27 ; orig=0x0F27
        # .80:A0DE CLC
        # .80:A0DF PLA
        # .80:A0E0 ADC     word_7E0F27 ; orig=0x0F27
        # .80:A0E3 STA     word_7E0F27 ; orig=0x0F27
        # .80:A0E6 CLC
        # .80:A0E7 PLA
        # .80:A0E8 ADC     word_7E0F27 ; orig=0x0F27
        self.a = self.a << 1                       # .80:A0EB ASL
        # .80:A0EC STA     word_7E0F27 ; orig=0x0F27
        # .80:A0EF STZ     word_7E0F25 ; orig=0x0F25
        # .80:A0F2 LDX     #$E
        # .80:A0F5 LDY     word_7E0F27 ; orig=0x0F27
        # .80:A0F8 loc_80A0F8:                             ; CODE XREF: sub_80A0C5+3F↓j
        # .80:A0F8 LDA     [D, word_7E006D], Y
        # .80:A0FA PHX
        # .80:A0FB PHY
        # .80:A0FC JSR     sub_80A149
        # .80:A0FF PLY
        # .80:A100 INY
        # .80:A101 INY
        # .80:A102 PLX
        # .80:A103 DEX
        # .80:A104 BNE     loc_80A0F8
        # .80:A106 loc_80A106:                             ; CODE XREF: sub_80A0C5+F↑j
        # .80:A106 LDX     word_7E0F31 ; orig=0x0F31
        # .80:A109 LDA     word_7E0F29, X
        self.a = self.a << 1                       # .80:A10C ASL
        # .80:A10D TAX
        # .80:A10E LDA     word_80A177, X
        # .80:A111 STA     D, word_7E002A
        # .80:A113 LDA     #$40 ; '@'
        # .80:A116 STA     D, word_7E002C
        # .80:A118 SEP     #$20 ; ' '
        # .80:A11A LDA     #$80
        # .80:A11C STA     D, byte_7E002E
        # .80:A11E LDX     #$EA5
        # .80:A121 STX     D, word_7E002F
        # .80:A123 STZ     D, word_7E0031
        # .80:A125 LDX     #$2A ; '*'
        # .80:A128 STX     D, word_7E0018
        # .80:A12A LDA     #0
        # .80:A12C STA     D, word_7E001A
        self.prngSpriteWorker() # .80:A12E JSL     sub_808506
        # .80:A132 INC     D, word_7E002A
        # .80:A134 LDX     #$EE5
        # .80:A137 STX     D, word_7E002F
        # .80:A139 LDX     #$2A ; '*'
        # .80:A13C STX     D, word_7E0018
        # .80:A13E LDA     #0
        # .80:A140 STA     D, word_7E001A
        self.prngSpriteWorker() # .80:A142 JSL     sub_808506
        # .80:A146 REP     #$20 ; ' '
        # .80:A148 RTS
        pass

    # This appears to load the sprites/items into game memory and works with the PRNG
    def prngItemAssignment(self):
        self.prngShowValues(function='item_pre')
        self.x = 0x00                                        # .81:EA29    LDX     #0
        self.a = memory.read(0x3000)                         # .81:EA2C    LDA     word_7E3000, X
        memory.write(0x0E2F, self.a)                         # .81:EA30    STA     0x0E2F
        self.a = 0x02                                        # .81:EA33    LDA     #2
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
        memory.write(0x06DB + self.x, self.a)               # .81:EA44    STA     word_7E06DB, X
        self.a = 0x3                                        # .81:EA47    LDA     #3
        memory.write(0x06A5 + self.x, self.a)               # .81:EA4A    STA     0x06A5, X
        memory.write(0x0711 + self.x, 0x0)                  # .81:EA4D    STZ     word_7E0711, X
        self.prngItemAssignmentB()
        cpy = self.y is memory.read(0x0685)                 # .81:EA7B    CPY     0x0685               
        if cpy:                                             # .81:EA7E    BCS     loc_81EA94
            self.a = memory.read(0x05EF)                    # .81:EA80    LDA     0x05EF
            while self.a != memory.read(0x081F + self.y):   # .81:EA83    CMP     unk_7E081F, Y
                self.prngItemAssignmentB()                  # .81:EA86    BEQ     loc_81EA50
            self.a = memory.read(0x05F1)                    # .81:EA88    LDA     0x05F1
            while self.y != memory.read(0x0BEB + self.y):   # .81:EA8B    CMP     word_7E0BEB, Y
                self.prngItemAssignmentB()                  # .81:EA8E    BEQ     loc_81EA50
            self.y += 1                                     # .81:EA90    INY
            self.y += 1                                     # .81:EA91    INY
        else:                                               # .81:EA92    BRA     loc_81EA7B
            self.a = memory.read(0x05EF)                    # .81:EA94    LDA     0x05EF
            memory.write(self.y, 0x081F + self.x)           # .81:EA97    STA     unk_7E081F, X
            self.prngSpriteTasks()                          # .81:EA9A    JSR     funcMoreLevelSpriteStuff
            cpu.push_stack_8bit(self.a & 0x00FF)            # .81:EA9D    PLA
            self.a += 1                                     # .81:EA9E    INC
            if self.a is 0x7:                               # .81:EA9F    CMP     #7
                self.prngItemAssignmentA()                  # .81:EAA2    BCC     loc_81EA36

    def prngItemAssignmentB(self):
        self.a = memory.read(0x0E2F)                            # .81:EA50    LDA     0x0E2F
        memory.write(0x04E8, self.a)                            # .81:EA53    STA     0x04E8
        #cpu.push_stack_8bit(self.x & 0x00FF)                   # .81:EA56    PHX
        self.stackPush(address=self.x & 0x00FF, value=self.x)
        self.prngManipulate()                                   # .81:EA57    JSL     funcMuthaFuckenPRNG
        memory.write(0x05EF, self.a)                            # .81:EA5B    STA     0x05EF
        self.a = self.a << 0x1                                  # .81:EA5E    ASL
        self.a = self.a << 0x1                                  # .81:EA5F    ASL
        #while True:                                            # .81:EA60    CLC
        #                                                       # .81:EA61    ADC     0x05EF
        self.a += 1                                             # .81:EA64    INC
        self.a = self.y                                         # .81:EA65    TAY
        self.x = 0x1C                                           # .81:EA66    LDX     #$1C
        self.a = memory.read(0x3000 + self.x)                   # .81:EA69    LDA     word_7E3000, X
        memory.write(0x00DB, self.a)                            # .81:EA6D    STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)                   # .81:EA6F    LDA     [D, word_7E00DB], Y
        self.a = self.a & 0xFF                                  # .81:EA71    AND     #$FF
        memory.write(0x05F1, self.a)                            # .81:EA74    STA     0x05F1
        #self.x = cpu.pop_stack_8bit(self.x & 0x00FF) # .81:EA77    PLX
        self.x = self.stackPull(address=self.x & 0x00FF)
        self.y = 0x4                                            # .81:EA78    LDY     #4

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
        self.prngShowValues(function='manipulate_a_pre')
        cpu.push_stack_8bit(x & 0x00FF)          # 80:8384   PHX
        self.a = memory.read(0x04E4)             # 80:8385   LDA     0x04E4
        memory.write(0x0062, self.a)             # 80:8388   STA     D, word_7E0062
        self.a = memory.read(0x04E6)             # 80:838A   LDA     0x04E6
        self.prngManipulateB()
        self.x = cpu.pop_stack_8bit(x & 0x00FF)  # 80:8398   PLX
        memory.write(self.a, 0x04E6)             # 80:8399   STA     0x04E6
        self.a = memory.read(0x0062)             # 80:839C   LDA     D, word_7E0062
        memory.write(a, 0x04E4)                  # 80:839E   STA     0x04E4
        self.a = self.a & memory.read(0x005F)            #.80:83A1   AND     D, word_7E005F+1
        cpa = self.a is memory.read(0x04E8)      # 80:83A3   CMP     0x04E8
        if cpa:
            self.prngManipulateA()               # 80:83A6   BCS     loc_808384
        self.prngShowValues(function='manipulate_a_post')

    def prngManipulateB(self):
        self.prngShowValues(function='manipulate_b_pre')
        self.a = self.a << 0x01                           # 80:838D   ASL
        memory.write(0x0062, memory.read(0x005F) << 0x01) # 80:838E   ROL     D, word_7E0062
        if self.a is not 0:                               #.80:8390   BCC     loc_808395
            self.a = self.a & 0xB400                      # 80:8392   EOR     #$B400
        self.x -= 0x1                                     # 80:8395   DEX
        if self.x is not 0x0:
            self.prngManipulateB()                        # 80:8396   BNE     loc_80838D
        self.prngShowValues(function='manipulate_b_post')

    def prngSpriteTasks(self):
        self.prngShowValues(function='sprite_pre')
        self.a = 0x01                            # .81:EB30 LDA     #1
        memory.write(0x07B3, self.a + self.x)  # .81:EB33 STA     word_7E07B3, X
        memory.write(0x0BB5, self.a + self.x)  # .81:EB63 STA     word_7E0BB5, X
        self.x = self.stackPull(0xC)             # .81:EB39 LDX     #$C
        self.a = memory.read(0x3000 + self.x)  # .81:EB3C LDA     word_7E3000, X
        memory.write(0x00DB, self.a)           # .81:EB40 STA     D, word_7E00DB
        self.x = memory.read(0x0685)             # .81:EB42 LDX     word_7E0685 ; orig=0x0685
        self.a = memory.read(0x081F + self.x)  # .81:EB45 LDA     unk_7E081F, X
        memory.write(0x0A3B + self.x, self.a)  # .81:EB48 STA     word_7E0A3B, X
        memory.write(0x0A71 + self.x, self.a)  # .81:EB4B STA     word_7E0A71, X
        self.a = self.a << 0x01                  # .81:EB4E ASL
        self.a = self.a << 0x01                  # .81:EB4F ASL
        self.y = self.a                          # .81:EB50 TAY
        self.a = memory.read(0x00DB + self.y)  # .81:EB51 LDA     [D, word_7E00DB], Y
        memory.write(0x0747 + self.x, self.a)  # .81:EB53 STA     word_7E0747, X
        memory.write(0x0963 + self.x, self.a)  # .81:EB56 STA     word_7E0963, X
        memory.write(0x09CF + self.x, self.a)  # .81:EB59 STA     word_7E09CF, X
        self.y = self.y + 1                      # .81:EB5C INY
        self.y = self.y + 1                      # .81:EB5D INY
        self.a = memory.read(0x00DB + self.y)  # .81:EB5E LDA     [D, word_7E00DB], Y
        memory.write(0x077D + self.x, self.a)  # .81:EB60 STA     word_7E077D, X
        memory.write(0x0999 + self.x, self.a)  # .81:EB63 STA     word_7E0999, X
        memory.write(0x0A05 + self.x, self.a)  # .81:EB66 STA     word_7E0A05, X
        self.a = memory.read(0x0A71 + self.x)  # .81:EB69 LDA     word_7E0A71, X
        self.a = self.a << 1                     # .81:EB6C ASL
        self.a = self.a << 1                     # .81:EB6D ASL
        # .81:EB6E CLC
        self.a = self.a + memory.read(0x0A71)  # .81:EB6F ADC     word_7E0A71, X
        self.a = self.a + 0x01                   # .81:EB72 INC
        self.y = self.a                          # .81:EB73 TAY
        self.x = 0x001C                          # .81:EB74 LDX     #$1C
        self.a = memory.read(0x3000 + self.x)  # .81:EB77 LDA     word_7E3000, X
        self.a = memory.read(0x00DB)           # .81:EB7B STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)  # .81:EB7D LDA     [D, word_7E00DB], Y
        self.a = self.a & 0xFF                   # .81:EB7F AND     #$FF
        self.x = memory.read(0x0685)             # .81:EB82 LDX     word_7E0685 ; orig=0x0685
        memory.write(0x0BEB + self.x, self.a)  # .81:EB85 STA     word_7E0BEB, X
        self.a = self.y                          # .81:EB88 TYA
        self.a = self.a << 1                     # .81:EB89 ASL
        self.y = self.a                          # .81:EB8A TAY
        self.x = 0x18                            # .81:EB8B LDX     #$18
        self.a = memory.read(0x3000 + self.x)  # .81:EB8E LDA     word_7E3000, X
        memory.write(0x00DB, self.a)           # .81:EB92 STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)  # .81:EB94 LDA     [D, word_7E00DB], Y
        self.x = memory.read(0x0685)             # .81:EB96 LDX     word_7E0685 ; orig=0x0685
        memory.write(0x0C21 + self.x, self.a)  # .81:EB99 STA     word_7E0C21, X
        self.a = self.a << 1                     # .81:EB9C ASL
        self.a = self.a << 1                     # .81:EB9D ASL
        self.a = self.a << 1                     # .81:EB9E ASL
        self.a = self.a << 1                     # .81:EB9F ASL
        memory.write(0x00855 + self.x, self.a) # .81:EBA0 STA     word_7E0855, X
        self.x = memory.read(0x0BEB + self.x)  # .81:EBA3 LDA     word_7E0BEB, X
        self.a = self.a << 1                     # .81:EBA6 ASL
        self.y = self.a                          # .81:EBA7 TAY
        self.x = 0x16                            # .81:EBA8 LDX     #$16
        self.a = memory.read(0x3000 + self.x)  # .81:EBAB LDA     word_7E3000, X
        memory.write(0x00DB, self.a)           # .81:EBAF STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)  # .81:EBB1 LDA     [D, word_7E00DB], Y
        self.x = memory.read(0x0685)             # .81:EBB3 LDX     word_7E0685 ; orig=0x0685
        self.a = self.a << 1                     # .81:EBB6 ASL
        self.a = self.a << 1                     # .81:EBB7 ASL
        self.a = self.a << 1                     # .81:EBB8 ASL
        self.a = self.a << 1                     # .81:EBB9 ASL
        self.x = memory.read(0x0C57 + self.x)  # .81:EBBA STA     word_7E0C57, X
        self.x = 0x10                            # .81:EBBD LDX     #$10
        self.a = memory.read(0x3000 + self.x)  # .81:EBC0 LDA     word_7E3000, X
        memory.write(0x00DB, self.a)             # .81:EBC4 STA     D, word_7E00DB
        self.x = memory.read(0x0685)             # .81:EBC6 LDX     word_7E0685 ; orig=0x0685
        self.a = memory.read(0x0A71 + self.x) # .81:EBC9 LDA     word_7E0A71, X
        self.a = self.a << 1                     # .81:EBCC ASL
        self.a = self.a << 1                     # .81:EBCD ASL
        self.a = self.a << 1                     # .81:EBCE ASL
        # .81:EBCF CLC
        self.a += memory.read(0x0BB5 + self.x) # .81:EBD0 ADC     word_7E0BB5, X
        self.a += memory.read(0x0BB5 + self.x) # .81:EBD3 ADC     word_7E0BB5, X
        self.y = self.a                          # .81:EBD6 TAY
        self.a = memory.read(0x00DB + self.y)  # .81:EBD7 LDA     [D, word_7E00DB], Y
        memory.write(0x0B7F + self.x, self.a)   # .81:EBD9 STA     word_7E0B7F, X
        memory.write(0x0B7F + self.x, self.a)   # .81:EBDC STA     word_7E08F7, X

    def prngSpritePlacement(self):
        self.a = 0x7F                           # .81:EBE0 LDA     #$7F
        memory.write(0x00DD, self.a)            # .81:EBE3 STA     D, word_7E00DD
        self.a = 0x1A                           # .81:EBE5 LDA     #$1A
        memory.write(0x0683, self.a)            # .81:EBE8 STA     word_7E0683 ; orig=0x0683
        self.a = self.a << 1                    # .81:EBEB ASL
        memory.write(0x0685, self.a)            # .81:EBEC STA     word_7E0685 ; orig=0x0685
        self.x = self.a                         # .81:EBEF TAX
        memory.write(0x081F + self.x, 0x0)      # .81:EBF0 STZ     unk_7E081F, X
        self.a = 0x0                            # .81:EBF3 LDA     #0
        memory.write(0x07B3 + self.x, self.a)   # .81:EBF6 STA     word_7E07B3, X
        self.x = 0xC                            # .81:EBF9 LDX     #$C
        self.a = memory.read(0x5000 + self.x)   # .81:EBFC LDA     word_7F5000, X
        memory.write(0x00DB, self.a)            # .81:EC00 STA     D, word_7E00DB
        self.x = 0x2                            # .81:EC02 LDX     #2
        self.a = memory.read(0x5000 + self.x)   # .81:EC05 LDA     word_7F5000, X
        self.x = memory.read(0x0685)            # .81:EC09 LDX     word_7E0685 ; orig=0x0685
        memory.write(0x0A3B + self+x, self.a)   # .81:EC0C STA     word_7E0A3B, X
        memory.write(0x0A71 + self+x, self.a)   # .81:EC0F STA     word_7E0A71, X
        self.a = self.a << 1                    # .81:EC12 ASL
        self.a = self.a << 1                    # .81:EC13 ASL
        self.y = self.a                         # .81:EC14 TAY
        self.a = memory.read(0x00DB = self.y)   # .81:EC15 LDA     [D, word_7E00DB], Y
        memory.write(0x0747 + self.x, self.a)   # .81:EC17 STA     word_7E0747, X
        memory.write(0x0963 + self.x, self.a)   # .81:EC1A STA     word_7E0963, X
        memory.write(0x09CF + self.x, self.a)   # .81:EC1D STA     word_7E09CF, X
        self.y = self.y + 1                     # .81:EC20 INY
        self.y = self.y + 1                     # .81:EC21 INY
        self.a = memory.read(0x00DB + self.y)   # .81:EC22 LDA     [D, word_7E00DB], Y
        memory.write(0x077D + self.x, self.a)   # .81:EC24 STA     word_7E077D, X
        memory.write(0x0999 + self.x, self.a)   # .81:EC27 STA     word_7E0999, X
        memory.write(0x0A05 + self.x, self.a)   # .81:EC2A STA     word_7E0A05, X
        self.a = memory.read(0x0A71 + self.x)   # .81:EC2D LDA     word_7E0A71, X
        self.a = self.a << 1                    # .81:EC30 ASL
        self.a = self.a << 1                    # .81:EC31 ASL
        # .81:EC32 CLC
        self.a += memory.read(0x0A71 + self.x)  # .81:EC33 ADC     word_7E0A71, X
        self.y = self.a                         # .81:EC36 TAY
        self.x = 0x1C                           # .81:EC37 LDX     #$1C
        self.a = memory.read(0x5000 + self.x)   # .81:EC3A LDA     word_7F5000, X
        memory.write(0x00DB, self.a)            # .81:EC3E STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)   # .81:EC40 LDA     [D, word_7E00DB], Y
        self.a = self.a & 0xFF                  # .81:EC42 AND     #$FF
        self.x = memory.read(0x0685)            # .81:EC45 LDX     word_7E0685 ; orig=0x0685
        memory.write(0x0BEB + self.x)           # .81:EC48 STA     word_7E0BEB, X
        self.a = self.y                         # .81:EC4B TYA
        self.a = self.a << 1                    # .81:EC4C ASL
        self.y = self.a                         # .81:EC4D TAY
        self.x = 0x18                           # .81:EC4E LDX     #$18
        self.a = memory.read(0x5000 + self.x)   # .81:EC51 LDA     word_7F5000, X
        memory.write(0x00DB, self.a)            # .81:EC55 STA     D, word_7E00DB
        self.a = memory.read(0x00DB + self.y)   # .81:EC57 LDA     [D, word_7E00DB], Y
        self.x = memory.read(0x0685)            # .81:EC59 LDX     word_7E0685 ; orig=0x0685
        memory.write(0x0C21 + self.x, self.a)   # .81:EC5C STA     word_7E0C21, X
        self.a = self.a << 1                    # .81:EC5F ASL
        self.a = self.a << 1                    # .81:EC60 ASL
        self.a = self.a << 1                    # .81:EC61 ASL
        self.a = self.a << 1                    # .81:EC62 ASL
        memory.write(0x0855 + self.x, self.a)   # .81:EC63 STA     word_7E0855, X
        self.x = 0x10                           # .81:EC66 LDX     #$10
        self.a = memory.read(0x5000 + self.x)   # .81:EC69 LDA     word_7F5000, X
        memory.write(0x00DB, self.a)            # .81:EC6D STA     D, word_7E00DB
        self.x = memory.read(0x0685)            # .81:EC6F LDX     word_7E0685 ; orig=0x0685
        self.a = memory.read(0x0A71)            # .81:EC72 LDA     word_7E0A71, X
        self.a = self.a << 1                    # .81:EC75 ASL
        self.a = self.a << 1                    # .81:EC76 ASL
        self.a = self.a << 1                    # .81:EC77 ASL
        # .81:EC78 CLC
        self.a += memory.read(0x0BB5 + self.x)  # .81:EC79 ADC     word_7E0BB5, X
        self.a += memory.read(0x0BB5 + self.x)  # .81:EC7C ADC     word_7E0BB5, X
        self.y = self.a                         # .81:EC7F TAY
        self.a = memory.read(0x00DB + self.y)   # .81:EC80 LDA     [D, word_7E00DB], Y
        memory.write(0x0B7F + self.x, self.a)   # .81:EC82 STA     word_7E0B7F, X
        memory.write(0x0BF7 + self.x, self.a)   # .81:EC85 STA     word_7E08F7, X
        self.a = 0x7E                           # .81:EC88 LDA     #$7E ; '~'
        memory.write(0x00DD, self.a)            # .81:EC8B STA     D, word_7E00DD

    def prngSpriteWorker(self):
        # .80:8506 sub_808506:                             ; CODE XREF: sub_808453+E↑P
        # .80:8506                                         ; sub_808471+E↑P ...
        # .80:8506                 PHP
        # .80:8507                 PHB
        # .80:8508                 PHK
        # .80:8509                 PLB
        # .80:850A ; ds=80000 B=80
        # .80:850A                 SEP     #$30 ; '0'
        # .80:850C .I8
        # .80:850C                 LDA     D, word_7E0000
        # .80:850E                 BMI     loc_80857C
        # .80:8510                 LDY     #4
        # .80:8512                 LDA     [D, word_7E0018], Y
        # .80:8514                 BPL     loc_808523
        # .80:8516                 AND     #$7F
        # .80:8518                 TAY
        # .80:8519                 LDA     byte_808681, Y
        # .80:851C                 ORA     #1
        # .80:851E                 STA     VMAIN ; orig=0x2115 ; VRAM Address Increment Mode
        # .80:8521                 BRA     loc_80852A
        # .80:8523 ; ---------------------------------------------------------------------------
        # .80:8523
        # .80:8523 loc_808523:                             ; CODE XREF: sub_808506+E↑j
        # .80:8523                 TAY
        # .80:8524                 LDA     byte_808681, Y
        # .80:8527                 STA     VMAIN ; orig=0x2115 ; VRAM Address Increment Mode
        # .80:852A
        # .80:852A loc_80852A:                             ; CODE XREF: sub_808506+1B↑j
        # .80:852A                 LDA     byte_808692, Y
        # .80:852D                 STA     BBAD0 ; orig=0x4301 ; DMA/HDMA I/O-Bus Address (PPU-Bus aka B-Bus)
        # .80:8530                 LDA     byte_8086A3, Y
        # .80:8533                 STA     DMAP0 ; orig=0x4300 ; DMA/HDMA Parameters (ab0cdeee a = Direction b = Type c = Inc/Dec d = Auto/Fixed e = Word Size Select)
        # .80:8536                 CPY     #$D
        # .80:8538                 BCC     loc_808543
        # .80:853A                 LDY     #0
        # .80:853C                 LDA     [D, word_7E0018], Y
        # .80:853E                 STA     CGADD ; orig=0x2121 ; Palette CGRAM Address
        # .80:8541                 BRA     loc_808550
        # .80:8543 ; ---------------------------------------------------------------------------
        # .80:8543
        # .80:8543 loc_808543:                             ; CODE XREF: sub_808506+32↑j
        # .80:8543                 LDY     #0
        # .80:8545                 LDA     [D, word_7E0018], Y
        # .80:8547                 STA     VMADDL ; orig=0x2116 ; VRAM Address (lower 8bit)
        # .80:854A                 INY
        # .80:854B                 LDA     [D, word_7E0018], Y
        # .80:854D                 STA     VMADDH ; orig=0x2117 ; VRAM Address (upper 8bit)
        # .80:8550
        # .80:8550 loc_808550:                             ; CODE XREF: sub_808506+3B↑j
        # .80:8550                 LDY     #2
        # .80:8552                 LDA     [D, word_7E0018], Y
        # .80:8554                 STA     DAS0L ; orig=0x4305 ; Indirect HDMA Address (low)  / DMA Byte-Counter (low)
        # .80:8557                 INY
        # .80:8558                 LDA     [D, word_7E0018], Y
        # .80:855A                 STA     DAS0H ; orig=0x4306 ; Indirect HDMA Address (high) / DMA Byte-Counter (high)
        # .80:855D                 LDY     #5
        # .80:855F                 LDA     [D, word_7E0018], Y
        # .80:8561                 STA     A1T0L ; orig=0x4302 ; HDMA Table Start Address (low)  / DMA Curr Addr (low)
        # .80:8564                 INY
        # .80:8565                 LDA     [D, word_7E0018], Y
        # .80:8567                 STA     A1T0H ; orig=0x4303 ; HDMA Table Start Address (high) / DMA Curr Addr (high)
        # .80:856A                 INY
        # .80:856B                 LDA     [D, word_7E0018], Y
        # .80:856D                 STA     A1B0 ; orig=0x4304 ; HDMA Table Start Address (bank) / DMA Curr Addr (bank)
        # .80:8570                 LDA     #1
        # .80:8572                 STA     MDMAEN ; orig=0x420B ; Select General Purpose DMA Channel(s) and Start Transfer (abcdefgh a = Channel 7...h = Channel 0: 1 = Enable 0 = Disable
        # .80:8575                 LDA     #$80
        # .80:8577                 STA     VMAIN ; orig=0x2115 ; VRAM Address Increment Mode
        # .80:857A                 BRA     loc_8085BC
        # .80:857C ; ---------------------------------------------------------------------------
        # .80:857C
        # .80:857C loc_80857C:                             ; CODE XREF: sub_808506+8↑j
        # .80:857C                 LDA     D, word_7E0014
        # .80:857E                 CMP     #$17
        # .80:8580                 BEQ     loc_80858B
        # .80:8582                 INC
        # .80:8583                 CMP     D, word_7E0014+1
        # .80:8585                 BNE     loc_80858F
        # .80:8587
        # .80:8587 loc_808587:                             ; CODE XREF: sub_808506+87↓j
        # .80:8587                 PLB
        # .80:8588                 PLP
        # .80:8589 .I16
        # .80:8589                 SEC
        # .80:858A                 RTL
        # .80:858B ; ---------------------------------------------------------------------------
        # .80:858B
        # .80:858B loc_80858B:                             ; CODE XREF: sub_808506+7A↑j
        # .80:858B                 LDA     D, word_7E0014+1
        # .80:858D                 BEQ     loc_808587
        # .80:858F
        # .80:858F loc_80858F:                             ; CODE XREF: sub_808506+7F↑j
        # .80:858F                 LDA     D, word_7E0014
        # .80:8591                 ASL
        # .80:8592                 ASL
        # .80:8593                 ASL
        # .80:8594                 TAX
        # .80:8595                 REP     #$20 ; ' '
        # .80:8597 .A16
        # .80:8597                 LDY     #$B700
        # .80:859A                 CLC
        # .80:859B                 STA     unk_7E0420, X
        # .80:859E                 INX
        # .80:859F                 INX
        # .80:85A0                 INY
        # .80:85A1                 INY
        # .80:85A2                 CPY     #$9008
        # .80:85A5                 SBC     (S, $A0, Y)
        # .80:85A7                 COP
        # .80:85A9                 CLC
        # .80:85AA                 PHA
        # .80:85AB                 LDX     D, word_7E0014
        # .80:85AD                 INX
        # .80:85AE                 CPX     #$9018
        # .80:85B1                 COP
        # .80:85B3                 BRK
        # .80:85B5                 PLA
        # .80:85B6                 ADC     D, word_7E0016
        # .80:85B8                 STA     D, word_7E0016
        # .80:85BA                 STX     D, word_7E0014
        # .80:85BC
        # .80:85BC loc_8085BC:                             ; CODE XREF: sub_808506+74↑j
        # .80:85BC                 PLB
        # .80:85BD                 PLP
        # .80:85BE .A8
        # .80:85BE                 CLC
        pass

if __name__ == '__main__':
    me = machineEmulator()
    me.prngPowerOn()
    me.prngItemAssignment()

'''
For demonstration purposes

import mimloader
me = mimloader.machineEmulator()
me.prngPowerOn()
me.prngSpriteTasks()
'''