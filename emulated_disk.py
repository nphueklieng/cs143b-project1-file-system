# CS 143B - Project 1 (emulated_disk.py)
# Name: Duangchanok Phueklieng (45231967)

class EmulatedDisk:
    def __init__ (self):
        '''
        Block 0: 64 bits bitmap (1 per block)
        Blocks 1-6: 192 file descriptors (4 ints: file_size, B0, B1, B2) 16 bytes per dedscriptor
        Blocks 7-63: Contain zeroes
        '''
        self.D = [bytearray(512) for block in range(64)] # Byte array D[64][512]
        self.bitmap = self.D[0]
        self.descriptors = self.D[1:7]

    def read_block (self):
        pass

    def write_block (self):
        pass
