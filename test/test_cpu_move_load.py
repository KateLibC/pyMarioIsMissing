from pysnes.cpu import CPU65816

# .../PySNES/venv/$ py.test pysnes/test/
class HeaderMock():
    def __init__(self):
        self.reset_int_addr = 0x8000

class MemoryMock(object):
    def __init__(self, ROM):
        self.ram = {}
        self.ROM = ROM
        self.header = HeaderMock()
        pc = self.header.reset_int_addr
        for byte in ROM:
            self.ram[pc] = byte
            pc += 1

    def read(self, address):
        return self.ram[address]

    def write(self, address, value):
        self.ram[address] = value


def test_LDA_long():
    mem = MemoryMock([0xAF, 0x56, 0x34, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    mem.write(0x123456, 0xAB)
    mem.write(0x123457, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 4 + mem.header.reset_int_addr


def test_LDA_long2():
    mem = MemoryMock([0xAF, 0xFF, 0xFF, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    mem.write(0x12FFFF, 0xAB)
    mem.write(0x130000, 0xCD) # no wrapping
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 4 + mem.header.reset_int_addr


def test_LDA_const16Bit():
    mem = MemoryMock([0xA9, 0x34, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 3
    assert cpu.A == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_const8Bit():
    mem = MemoryMock([0xA9, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00100000 # 8 Bit mode
    cpu.e = 1
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 2
    assert cpu.A == 0x34
    assert cpu.P == 0b00100000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP():
    mem = MemoryMock([0xA5, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x001234, 0xAB)
    mem.write(0x001235, 0x00)
    cpu.DP = 0x1200
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.A == 0x00AB
    assert cpu.P == 0b00000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP2():
    mem = MemoryMock([0xA5, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x000000, 0xCD)
    mem.write(0x00FFFF, 0xAB) # zero bank wrapping!
    mem.write(0x010000, 0xEF) # Bug if this is read
    cpu.DP = 0xFF00
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_absolute():
    mem = MemoryMock([0xAD, 0x56, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x123456, 0xAB)
    mem.write(0x123457, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_absolute2():
    mem = MemoryMock([0xAD, 0xFF, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x12FFFF, 0xAB) # no wrapping
    mem.write(0x130000, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_DP_indirect_indexed_Y():
    mem = MemoryMock([0xB1, 0x10])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.DP = 0x0020
    cpu.Y = 0x0001
    mem.write(0x000030, 0x30)
    mem.write(0x000031, 0x40)
    mem.write(0x000032, 0x23)
    mem.write(0x000033, 0x22)
    mem.write(0x000034, 0xFA)
    mem.write(0x000035, 0x22)
    mem.write(0x000036, 0x23)
    mem.write(0x000037, 0x1C)

    mem.write(0x000038, 0x23)
    mem.write(0x000039, 0x2D)
    mem.write(0x00003A, 0xDD)
    mem.write(0x00003B, 0xF4)
    mem.write(0x00003C, 0xFF)
    mem.write(0x00003D, 0xFF)
    mem.write(0x00003E, 0xFF)
    mem.write(0x00003F, 0xFF)

    mem.write(0x804031, 0xAB)
    mem.write(0x804032, 0xCD)
    cpu.P = 0b00000000  # 16 Bit mode
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect_indexed_Y2():
    mem = MemoryMock([0xB1, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.DP = 0xFF00
    cpu.Y = 0x000A
    mem.write(0x000000, 0xFF)
    mem.write(0x00FFFF, 0xFE)

    mem.write(0x130008, 0xAB)
    mem.write(0x130009, 0xCD)
    cpu.P = 0b00000000  # 16 Bit mode
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect():
    mem = MemoryMock([0xB2, 0x10])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.DP = 0x0020
    cpu.Y = 0x0001
    mem.write(0x000030, 0x30)
    mem.write(0x000031, 0x40)
    mem.write(0x000032, 0x23)
    mem.write(0x000033, 0x22)
    mem.write(0x000034, 0xFA)
    mem.write(0x000035, 0x22)
    mem.write(0x000036, 0x23)
    mem.write(0x000037, 0x1C)

    mem.write(0x000038, 0x23)
    mem.write(0x000039, 0x2D)
    mem.write(0x00003A, 0xDD)
    mem.write(0x00003B, 0xF4)
    mem.write(0x00003C, 0xFF)
    mem.write(0x00003D, 0xFF)
    mem.write(0x00003E, 0xFF)
    mem.write(0x00003F, 0xFF)

    mem.write(0x804030, 0xAB)
    mem.write(0x804031, 0xCD)
    cpu.P = 0b00000000  # 16 Bit mode
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6, 7)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect2():
    mem = MemoryMock([0xB2, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.DP = 0xFF00
    cpu.Y = 0x0001 # should have no effect
    mem.write(0x000000, 0xFF)
    mem.write(0x00FFFF, 0xFF)

    mem.write(0x12FFFF, 0xAB)
    mem.write(0x130000, 0xCD)
    cpu.P = 0b00000000  # 16 Bit mode
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6, 7)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect_long_indexed_Y():
    mem = MemoryMock([0xB7, 0x10])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.DP = 0x0020
    cpu.Y = 0x0001
    mem.write(0x000030, 0x30)
    mem.write(0x000031, 0x40)
    mem.write(0x000032, 0x23)
    mem.write(0x000033, 0x22)
    mem.write(0x000034, 0xFA)
    mem.write(0x000035, 0x22)
    mem.write(0x000036, 0x23)
    mem.write(0x000037, 0x1C)

    mem.write(0x000038, 0x23)
    mem.write(0x000039, 0x2D)
    mem.write(0x00003A, 0xDD)
    mem.write(0x00003B, 0xF4)
    mem.write(0x00003C, 0xFF)
    mem.write(0x00003D, 0xFF)
    mem.write(0x00003E, 0xFF)
    mem.write(0x00003F, 0xFF)

    mem.write(0x234031, 0xAB)
    mem.write(0x234032, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (7, 8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect_long_indexed_Y2():
    mem = MemoryMock([0xB7, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80 # should have no effect
    cpu.DP = 0xFF00
    cpu.Y = 0x000A
    mem.write(0x000000, 0x12)
    mem.write(0x00FFFE, 0xFC)
    mem.write(0x00FFFF, 0xFF)

    mem.write(0x130006, 0xAB)
    mem.write(0x130007, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (7, 8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect_long():
    mem = MemoryMock([0xA7, 0x10])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.DP = 0x0020
    mem.write(0x000030, 0x30)
    mem.write(0x000031, 0x40)
    mem.write(0x000032, 0x23)
    mem.write(0x000033, 0x22)
    mem.write(0x000034, 0xFA)
    mem.write(0x000035, 0x22)
    mem.write(0x000036, 0x23)
    mem.write(0x000037, 0x1C)

    mem.write(0x000038, 0x23)
    mem.write(0x000039, 0x2D)
    mem.write(0x00003A, 0xDD)
    mem.write(0x00003B, 0xF4)
    mem.write(0x00003C, 0xFF)
    mem.write(0x00003D, 0xFF)
    mem.write(0x00003E, 0xFF)
    mem.write(0x00003F, 0xFF)

    mem.write(0x234030, 0xAB)
    mem.write(0x234031, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6, 7, 8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indirect_long2():
    mem = MemoryMock([0xA7, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80 # should have no effect
    cpu.DP = 0xFF00
    mem.write(0x000000, 0x12)
    mem.write(0x00FFFE, 0xFF)
    mem.write(0x00FFFF, 0xFF)

    mem.write(0x12FFFF, 0xAB)
    mem.write(0x130000, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6, 7, 8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indexed_indirect_X():
    mem = MemoryMock([0xA1, 0x02])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.DP = 0x0020
    cpu.X = 0x0004

    mem.write(0x000020, 0xFF)
    mem.write(0x000021, 0x00)
    mem.write(0x000022, 0xFF)
    mem.write(0x000023, 0x09)
    mem.write(0x000024, 0x33)
    mem.write(0x000025, 0x33)
    mem.write(0x000026, 0x09)
    mem.write(0x000027, 0x88)

    mem.write(0x000028, 0x08)
    mem.write(0x000029, 0x76)
    mem.write(0x00002A, 0x66)
    mem.write(0x00002B, 0x36)
    mem.write(0x00002C, 0xD7)
    mem.write(0x00002D, 0x23)
    mem.write(0x00002E, 0x99)
    mem.write(0x00002F, 0x00)

    mem.write(0x808809, 0xAB)
    mem.write(0x80880A, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6,7,8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indexed_indirect_X2():
    mem = MemoryMock([0xA1, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.DP = 0xFF00
    cpu.X = 0x000A

    mem.write(0x000008, 0xFF)
    mem.write(0x000009, 0xFF)

    mem.write(0x12FFFF, 0xAB)
    mem.write(0x130000, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (6,7,8)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indexed_X():
    mem = MemoryMock([0xB5, 0x30])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80  # should have no effect
    cpu.DP = 0x0020
    cpu.X = 0x0004

    mem.write(0x000054, 0xAB)
    mem.write(0x000055, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_DP_indexed_X2():
    mem = MemoryMock([0xB5, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80 # should have no effect
    cpu.DP = 0xFF00
    cpu.X = 0x000A

    mem.write(0x000008, 0xAB)
    mem.write(0x000009, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_abs_indexed_X():
    mem = MemoryMock([0xBD, 0x00, 0x80])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.X = 0x0001

    mem.write(0x808001, 0xAB) # no wrapping
    mem.write(0x808002, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_abs_indexed_X2():
    mem = MemoryMock([0xBD, 0xFE, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.X = 0x000A

    mem.write(0x130008, 0xAB) # no wrapping
    mem.write(0x130009, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_abs_indexed_Y():
    mem = MemoryMock([0xB9, 0x00, 0x80])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.Y = 0x0001

    mem.write(0x808001, 0xAB) # no wrapping
    mem.write(0x808002, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_abs_indexed_Y2():
    mem = MemoryMock([0xB9, 0xFE, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.Y = 0x000A

    mem.write(0x130008, 0xAB) # no wrapping
    mem.write(0x130009, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDA_long_indexed_X():
    mem = MemoryMock([0xBF, 0x00, 0x80, 0x80])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.X = 0x0001

    mem.write(0x808001, 0xAB)
    mem.write(0x808002, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 4 + mem.header.reset_int_addr


def test_LDA_long_indexed_X2():
    mem = MemoryMock([0xBF, 0xFE, 0xFF, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.X = 0x000A

    mem.write(0x130008, 0xAB)
    mem.write(0x130009, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 6
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 4 + mem.header.reset_int_addr


def test_LDA_stack_relative():
    mem = MemoryMock([0xA3, 0x01])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.SP = 0x1FF0

    mem.write(0x001FF1, 0xAB)
    mem.write(0x001FF2, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_stack_relative2():
    mem = MemoryMock([0xA3, 0xFA])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.SP = 0xFF10

    mem.write(0x00000A, 0xAB)
    mem.write(0x00000B, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDA_stack_relative_indirect_indexed_Y():
    mem = MemoryMock([0xB3, 0xFA])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.SP = 0xFF10
    cpu.Y = 0x50
    cpu.DBR = 0x12

    mem.write(0x00000A, 0xF0) # 0x1000A becomes 0x000A
    mem.write(0x00000B, 0xFF) # 0x1000B becomes 0x000B

    mem.write(0x130040, 0xAB)
    mem.write(0x130041, 0xCD)
    assert cpu.A == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 8
    assert cpu.A == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_const16Bit():
    mem = MemoryMock([0xA2, 0x34, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 3
    assert cpu.X == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDX_const8Bit():
    mem = MemoryMock([0xA2, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # 8 Bit mode
    cpu.e = 1
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 2
    assert cpu.X == 0x34
    assert cpu.P == 0b00010000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_DP():
    mem = MemoryMock([0xA6, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x001234, 0xAB)
    mem.write(0x001235, 0x00)
    cpu.DP = 0x1200
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.X == 0x00AB
    assert cpu.P == 0b00000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_DP2():
    mem = MemoryMock([0xA6, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x000000, 0xCD)
    mem.write(0x00FFFF, 0xAB) # zero bank wrapping!
    mem.write(0x010000, 0xEF) # Bug if this is read
    cpu.DP = 0xFF00
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_absolute():
    mem = MemoryMock([0xAE, 0x56, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x123456, 0xAB)
    mem.write(0x123457, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDX_absolute2():
    mem = MemoryMock([0xAE, 0xFF, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x12FFFF, 0xAB) # no wrapping
    mem.write(0x130000, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDX_DP_indexed_Y():
    mem = MemoryMock([0xB6, 0x30])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80  # should have no effect
    cpu.DP = 0x0020
    cpu.Y = 0x0004

    mem.write(0x000054, 0xAB)
    mem.write(0x000055, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_DP_indexed_Y2():
    mem = MemoryMock([0xB6, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80 # should have no effect
    cpu.DP = 0xFF00
    cpu.Y = 0x000A

    mem.write(0x000008, 0xAB)
    mem.write(0x000009, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDX_abs_indexed_Y():
    mem = MemoryMock([0xBE, 0x00, 0x80])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.Y = 0x0001

    mem.write(0x808001, 0xAB) # no wrapping
    mem.write(0x808002, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDX_abs_indexed_Y2():
    mem = MemoryMock([0xBE, 0xFE, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.Y = 0x000A

    mem.write(0x130008, 0xAB) # no wrapping
    mem.write(0x130009, 0xCD)
    assert cpu.X == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.X == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDY_const16Bit():
    mem = MemoryMock([0xA0, 0x34, 0x12])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 3
    assert cpu.Y == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDY_const8Bit():
    mem = MemoryMock([0xA0, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # 8 Bit mode
    cpu.e = 1
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 2
    assert cpu.Y == 0x34
    assert cpu.P == 0b00010000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDY_DP():
    mem = MemoryMock([0xA4, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x001234, 0xAB)
    mem.write(0x001235, 0x00)
    cpu.DP = 0x1200
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.Y == 0x00AB
    assert cpu.P == 0b00000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDY_DP2():
    mem = MemoryMock([0xA4, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000  # 16 Bit mode
    cpu.e = 0
    mem.write(0x000000, 0xCD)
    mem.write(0x00FFFF, 0xAB) # zero bank wrapping!
    mem.write(0x010000, 0xEF) # Bug if this is read
    cpu.DP = 0xFF00
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (3, 4, 5)
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDY_absolute():
    mem = MemoryMock([0xAC, 0x56, 0x34])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x123456, 0xAB)
    mem.write(0x123457, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDY_absolute2():
    mem = MemoryMock([0xAC, 0xFF, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    mem.write(0x12FFFF, 0xAB) # no wrapping
    mem.write(0x130000, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles == 5
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDY_DP_indexed_X():
    mem = MemoryMock([0xB4, 0x30])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80  # should have no effect
    cpu.DP = 0x0020
    cpu.X = 0x0004

    mem.write(0x000054, 0xAB)
    mem.write(0x000055, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDY_DP_indexed_X2():
    mem = MemoryMock([0xB4, 0xFE])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80 # should have no effect
    cpu.DP = 0xFF00
    cpu.X = 0x000A

    mem.write(0x000008, 0xAB)
    mem.write(0x000009, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles in (5, 6)
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 2 + mem.header.reset_int_addr


def test_LDY_abs_indexed_X():
    mem = MemoryMock([0xBC, 0x00, 0x80])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x80
    cpu.X = 0x0001

    mem.write(0x808001, 0xAB) # no wrapping
    mem.write(0x808002, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_LDY_abs_indexed_X2():
    mem = MemoryMock([0xBC, 0xFE, 0xFF])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000 # 16 Bit mode
    cpu.e = 0
    cpu.DBR = 0x12
    cpu.X = 0x000A

    mem.write(0x130008, 0xAB) # no wrapping
    mem.write(0x130009, 0xCD)
    assert cpu.Y == 0

    cpu.fetch_decode_execute()

    assert cpu.cycles >= 6
    assert cpu.Y == 0xCDAB
    assert cpu.P == 0b10000000
    assert cpu.PC == 3 + mem.header.reset_int_addr


def test_TAX():
    mem = MemoryMock([0xAA])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x6789
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TAX

    assert cpu.cycles == 2
    assert cpu.A == 0x6789
    assert cpu.X == 0x6789
    assert cpu.Y == 0xABCD
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAX_N():
    mem = MemoryMock([0xAA])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0xC789
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TAX

    assert cpu.cycles == 2
    assert cpu.A == 0xC789
    assert cpu.X == 0xC789
    assert cpu.Y == 0xABCD
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAX_Z():
    mem = MemoryMock([0xAA])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x0000
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TAX

    assert cpu.cycles == 2
    assert cpu.A == 0x0000
    assert cpu.X == 0x0000
    assert cpu.Y == 0xABCD
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAX_X():
    mem = MemoryMock([0xAA])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0x5678
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TAX

    assert cpu.cycles == 2
    assert cpu.A == 0x5678
    assert cpu.X == 0x1278
    assert cpu.Y == 0xABCD
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAX_NX():
    mem = MemoryMock([0xAA])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0x6789
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TAX

    assert cpu.cycles == 2
    assert cpu.A == 0x6789
    assert cpu.X == 0x1289
    assert cpu.Y == 0xABCD
    assert cpu.P == 0b10010000 # nx
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAY():
    mem = MemoryMock([0xA8])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x6789
    cpu.X = 0xABCD
    cpu.Y = 0x1234

    cpu.fetch_decode_execute() # TAY

    assert cpu.cycles == 2
    assert cpu.A == 0x6789
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x6789
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAY_N():
    mem = MemoryMock([0xA8])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0xC789
    cpu.X = 0xABCD
    cpu.Y = 0x1234

    cpu.fetch_decode_execute() # TAY

    assert cpu.cycles == 2
    assert cpu.A == 0xC789
    assert cpu.X == 0xABCD
    assert cpu.Y == 0xC789
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAY_Z():
    mem = MemoryMock([0xA8])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x0000
    cpu.X = 0xABCD
    cpu.Y = 0x1234

    cpu.fetch_decode_execute() # TAY

    assert cpu.cycles == 2
    assert cpu.A == 0x0000
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x0000
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAY_X():
    mem = MemoryMock([0xA8])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0x5678
    cpu.X = 0xABCD
    cpu.Y = 0x1234

    cpu.fetch_decode_execute() # TAY

    assert cpu.cycles == 2
    assert cpu.A == 0x5678
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x1278
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TAY_NX():
    mem = MemoryMock([0xA8])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0x6789
    cpu.X = 0xABCD
    cpu.Y = 0x1234

    cpu.fetch_decode_execute() # TAY

    assert cpu.cycles == 2
    assert cpu.A == 0x6789
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x1289
    assert cpu.P == 0b10010000 # nx
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXA():
    mem = MemoryMock([0x8A])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0xABCD
    cpu.X = 0x1234
    cpu.Y = 0x6789

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.A == 0x1234
    assert cpu.X == 0x1234
    assert cpu.Y == 0x6789
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXA_N():
    mem = MemoryMock([0x8A])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0xABCD
    cpu.X = 0x8234
    cpu.Y = 0x6789

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.A == 0x8234
    assert cpu.X == 0x8234
    assert cpu.Y == 0x6789
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXA_Z():
    mem = MemoryMock([0x8A])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0xABCD
    cpu.X = 0x0000
    cpu.Y = 0x6789

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.A == 0x0000
    assert cpu.X == 0x0000
    assert cpu.Y == 0x6789
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXA_X():
    mem = MemoryMock([0x8A])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0xABCD
    cpu.X = 0x1234
    cpu.Y = 0x6789

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.A == 0x1234
    assert cpu.X == 0x1234
    assert cpu.Y == 0x6789
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXY():
    mem = MemoryMock([0x9B])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TXY

    assert cpu.cycles == 2
    assert cpu.X == 0x1234
    assert cpu.Y == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXY_N():
    mem = MemoryMock([0x9B])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0x8234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TXY

    assert cpu.cycles == 2
    assert cpu.X == 0x8234
    assert cpu.Y == 0x8234
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXY_Z():
    mem = MemoryMock([0x9B])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0x0000
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TXY

    assert cpu.cycles == 2
    assert cpu.X == 0x0000
    assert cpu.Y == 0x0000
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TXY_X():
    mem = MemoryMock([0x9B])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.X = 0x1234
    cpu.Y = 0xABCD

    cpu.fetch_decode_execute() # TXY

    assert cpu.cycles == 2
    assert cpu.X == 0x1234
    assert cpu.Y == 0xAB34
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYA():
    mem = MemoryMock([0x98])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0x8976
    cpu.Y = 0x1234
    cpu.A = 0xABCD

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.X == 0x8976
    assert cpu.Y == 0x1234
    assert cpu.A == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYA_N():
    mem = MemoryMock([0x98])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0xABCD
    cpu.Y = 0x8234
    cpu.A = 0xABCD

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x8234
    assert cpu.A == 0x8234
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYA_Z():
    mem = MemoryMock([0x98])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.X = 0xABCD
    cpu.Y = 0x0000
    cpu.A = 0xABCD

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.X == 0xABCD
    assert cpu.Y == 0x0000
    assert cpu.A == 0x0000
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYA_X():
    mem = MemoryMock([0x98])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.X = 0x8765
    cpu.Y = 0x1234
    cpu.A = 0xABCD

    cpu.fetch_decode_execute() # TXA

    assert cpu.cycles == 2
    assert cpu.X == 0x8765
    assert cpu.Y == 0x1234
    assert cpu.A == 0x1234
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYX():
    mem = MemoryMock([0xBB])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x8765
    cpu.Y = 0x1234
    cpu.X = 0xABCD

    cpu.fetch_decode_execute() # TYX

    assert cpu.cycles == 2
    assert cpu.A == 0x8765
    assert cpu.Y == 0x1234
    assert cpu.X == 0x1234
    assert cpu.P == 0b00000000
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYX_N():
    mem = MemoryMock([0xBB])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x8765
    cpu.Y = 0x8234
    cpu.X = 0xABCD

    cpu.fetch_decode_execute() # TYX

    assert cpu.cycles == 2
    assert cpu.A == 0x8765
    assert cpu.Y == 0x8234
    assert cpu.X == 0x8234
    assert cpu.P == 0b10000000 # n
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYX_Z():
    mem = MemoryMock([0xBB])
    cpu = CPU65816(mem)
    cpu.P = 0b00000000
    cpu.e = 0
    cpu.A = 0x8765
    cpu.Y = 0x0000
    cpu.X = 0xABCD

    cpu.fetch_decode_execute() # TYX

    assert cpu.cycles == 2
    assert cpu.A == 0x8765
    assert cpu.Y == 0x0000
    assert cpu.X == 0x0000
    assert cpu.P == 0b00000010 # z
    assert cpu.PC == 1 + mem.header.reset_int_addr


def test_TYX_X():
    mem = MemoryMock([0xBB])
    cpu = CPU65816(mem)
    cpu.P = 0b00010000 # x
    cpu.e = 0
    cpu.A = 0x8765
    cpu.Y = 0x1234
    cpu.X = 0xABCD

    cpu.fetch_decode_execute() # TYX

    assert cpu.cycles == 2
    assert cpu.A == 0x8765
    assert cpu.Y == 0x1234
    assert cpu.X == 0xAB34
    assert cpu.P == 0b00010000 # x
    assert cpu.PC == 1 + mem.header.reset_int_addr