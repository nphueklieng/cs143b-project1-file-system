# CS 143B - Project 1 (emulated_disk.py)
# Name: Duangchanok Phueklieng (45231967)

# Bitmap Mask for 8 bits (byte)
MASK = [0] * 8
MASK[7] = 0x0001
for i in range (6, -1, -1):
    MASK[i] = MASK[i + 1] << 1

class EmulatedDisk:
    def __init__ (self):
        '''
        Block 0: 64 bits bitmap (1 per block)
        Blocks 1-6: 192 file descriptors (4 ints: file_size, B0, B1, B2) # 16 bytes per descriptor
            Directory Entries: File name (4 chars incl. string terminator), descriptor index (1 int) # 8 bytes per entry
        '''
        self.D = [bytearray(512) for block in range(64)]

    def read_block (self, i, buffer):
        ''' Read block i contents into a buffer'''
        buffer[:] = self.D[i]  # Overwrites the caller's buffer

    def write_block (self, i, buffer):
        ''' Write buffer into disk block 1 '''
        self.D[i][:] = buffer  # Don't just change reference, change the memory contents of D[i]

