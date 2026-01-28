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
        '''
        self.D = [bytearray(512) for block in range(64)]
        self.bitmap = self.D[0]
        # All descriptors initially free: Initialize all file sizes to -1
        for i in range(192):
            self.set_descriptor_file_size(i, -1)
        # Remaining Blocks 7-63 are initially free, blocks before are not free
        for i in range(7):
            self.allocate_block(i, -1)

    def get_bitmap_bit (self, block):
        byte_index = block // 8
        bit_offset = 7 - (block % 8)  # If Block 0, 1 is leftmost
        return (self.bitmap[byte_index] >> bit_offset) & 1  # Look at only that bit
    
    def set_bitmap_bit (self, block):
        byte_index = block // 8
        bit_offset = 7 - (block % 8)  # If Block 0, 1 is leftmost
        self.bitmap[byte_index] |= MASK[bit_offset]

    def get_descriptor (self, index):
        ''' Read the contents of a particular file descriptor'''
        block_index = index // 32 + 1  # Which disk block is it in?
        offset = (index % 32) * 16  # Offset index in bytes
        return memoryview(self.D[block_index])[offset : offset + 16].cast("i")  # Return descriptor as a reference to the array of 4-byte integers
    
    def set_descriptor_file_size (self, index, file_size):
        d = self.get_descriptor(index)
        d[0] = file_size

    def add_descriptor_file_block (self, index, new_block):
        # Search the descriptor for a space to record the new block
        # If cannot find empty slot, return -1
        d = self.get_descriptor(index)
        for i in range(1, 4):
            if (d[i] == 0):
                d[i] = new_block
                return new_block
        return -1

    def allocate_block (self, block, descriptor):
        # Update the bitmap with the mask
        if descriptor > -1:
            self.add_descriptor_file_block(descriptor, block)  # Allocate that block to a file.  What if full/error?
        # Set bit at that block index to 1 (allocated)
        self.set_bitmap_bit(block)
        

    def read_block (self):
        pass

    def write_block (self):
        pass
