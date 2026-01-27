# CS 143B - Project 1 (emulated_disk.py)
# Name: Duangchanok Phueklieng (45231967)

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
            

    def get_descriptor (self, index):
        ''' Read the contents of a particular file descriptor'''
        block_index = index // 32 + 1  # Which disk block is it in?
        offset = (index % 32) * 16  # Offset index in bytes
        return memoryview(self.D[block_index])[offset : offset + 4]  # Return descriptor as a reference to the bytearray
    
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


    def read_block (self):
        pass

    def write_block (self):
        pass
