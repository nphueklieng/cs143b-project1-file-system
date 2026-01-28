# CS 143B - Project 1 (main.py)
# Name: Duangchanok Phueklieng (45231967)

# Emulated Disk

'''
Block 0: 64 bits bitmap (1 per block)
Blocks 1-6: 192 file descriptors (4 ints: file_size, B0, B1, B2) # 16 bytes per descriptor
    Directory Entries: File name (4 chars incl. string terminator), descriptor index (1 int) # 8 bytes per dir entry
'''

D = None
I = None
O = None
M = None
OFT = None

DIR_ENTRY_SIZE = 8 # bytes
FILE_NAME_SIZE = 4 # bytes
DESCRIPTOR_SIZE = 16 # bytes
INT_SIZE = 4 # bytes

# Bitmap

MASK = [0] * 8  # 8-bit mask, it's for the byte array
MASK[7] = 1
for i in range (6, 0, -1):
    MASK[i] = MASK[i + 1] << 1

def locate_block_in_bitmap (block):
    ''' Return the corresponding location of the block: which byte and which bit in that byte '''
    byte = block // 8
    bit = block % 8
    return byte, bit

def get_bitmap (block):
    ''' Return the status of that block in the bitmap '''
    global I
    read_block(0)  # read bitmap into I
    byte, bit = locate_block_in_bitmap(block)
    if (O[byte] & MASK[bit]):  # Extracting the bit. Only all 0 if bit is 0
        return 1
    return 0

def set_bitmap (block, status):
    ''' Set bit in bitmap for block to 1 (allocated) or 0 (free) '''
    global O, I
    read_block(0)  # read the bitmap into I
    O[:] = I[:]    # copy into O
    byte, bit = locate_block_in_bitmap(block)
    if status:  # Set bit to 1
        O[byte] |= MASK[bit]
    else:  # Clear bit
        O[byte] &= ~MASK[bit]
    write_block(0)  # write updated bitmap to disk

def find_free_block ():
    ''' Use the bitmap to find a free block and return its index '''
    for i in range(7, 64):  # There are 64 blocks, we skip the bitmap and descriptor blocks
        if get_bitmap(i):
            return i 
    return -1

# Disk Access functions

def read_block (b):
    ''' Read block b contents into an input buffer (bytearray I[512]) '''
    global I, D
    I[:] = D[b]  # Overwrites the caller's buffer

def write_block (b):
    ''' Write buffer (bytearray O[512]) into disk block b '''
    global O, D
    D[b][:] = O  # Don't just change reference, change the memory contents of D[i]

# File System

class OFTEntry:
    def __init__ (self):
        self.rw_buffer = bytearray(512)
        self.position = -1   # Mark as free
        self.file_size = 0
        self.descriptor_index = 0
    
    def determine_block_in_buffer (self):
        ''' Determine which block is currently held in the rw_buffer. Return block index in disk'''
        n = self.position // 512  # currently in the nth block in the file descriptor
        block_index = get_descriptor_blocks(self.descriptor_index)[n]  # Current position is in Disk block i
        return block_index
    
    def write_buffer_to_disk (self):
        ''' Copy the current buffer contents to the block '''
        global O
        block = self.determine_block_in_buffer()
        O[:] = self.rw_buffer[:]   # copy r/w buffer to O
        write_block(block)   # Write O to D[block]

def read_memory (mem, count):
    ''' Return data read. Copy count bytes from memory M starting with position mem to output device'''
    global M
    return M[mem : mem + count]

def write_memory (mem, str):
    ''' Return num bytes written. Copy string str into memory M starting with position mem from input device'''
    global M
    n = len(str)
    M[mem : mem + n] = str
    return n

def check_directory_entry_exists (name):
    ''' Check if file already exists '''
    oft_entry = OFT[0]
    seek(0, 0)  # Move current position in directory to 0
    while (oft_entry.position < oft_entry.size): # check EOF
        read(0, 0, DIR_ENTRY_SIZE) # Now next directory entry is in memory starting at M[m]
        name_field = read_memory(0, 4)
        if name_field == name:
            return 1
    return 0

def find_free_descriptor ():
    ''' Find and return index of free descriptor '''
    global I
    for block in range(1, 7):
        read_block(block)
        for d in range(32):
            start = d * DESCRIPTOR_SIZE
            size_field = I[start : start + 4]
            if size_field == -1: # Free file descriptor
                descriptor = (block - 1) * 32 + d
                return descriptor
    return -1
    
def get_descriptor_location(i):
    ''' Return the block number and block offset of file descriptor i '''
    block = 1 + (i // 32)  # which block? skipping the first block (bitmap)
    offset = (i % 32) * DESCRIPTOR_SIZE   # What index in that block?
    return block, offset

def get_descriptor_size (i):
    ''' Assign descriptor i to new file '''
    global I
    block, offset = get_descriptor_location(i)
    read_block(block)
    size_field = I[offset : offset + INT_SIZE]
    return size_field

def get_descriptor_blocks (i):
    ''' Return all block of descriptor i '''
    global I
    block, offset = get_descriptor_location(i)
    read_block(block)
    start = offset + INT_SIZE
    block_numbers = []
    for i in range(3):
        block_start = start + INT_SIZE * i
        block_num = I[ block_start : block_start + INT_SIZE]
        block_numbers.append(block_num)
    return block_numbers

def assign_descriptor (i):
    ''' Assign descriptor i to new file '''
    global O, I
    block, offset = get_descriptor_location(i)
    read_block(block)
    O[:] = I[:]
    O[offset : offset + INT_SIZE] = 0  # Set file descriptor size from -1 to 0
    O[offset + INT_SIZE : offset + DESCRIPTOR_SIZE] = [0] * 12   # Zero out the block numbers. 12 bytes is the size of the 3 fields
    write_block(block)

def free_descriptor (i):
    '''  Free descriptor i and its blocks '''
    global O, I
    block, offset = get_descriptor_location(i)
    read_block(block)
    O[:] = I[:]
    O[offset : offset + INT_SIZE] = -1  # Set file descriptor size from 0 to -1
    # Free allocated blocks
    start = offset + INT_SIZE
    block_numbers = get_descriptor_blocks(i)
    for block in block_numbers:
        if block != 0:
            set_bitmap(0, 0)  # Update bit map to free those blocks
    O[offset + INT_SIZE : offset + DESCRIPTOR_SIZE] = [0] * 12  # Zero out all block numbers
    write_block(block)

def update_descriptor_size (d, size):
    ''' Update descriptor d so that its file size field reflects the new size '''
    global I, O
    block, offset = get_descriptor_location(d)
    read_block(block)  # Now the block with the descriptor is in I
    I[offset : offset + INT_SIZE] = size  # Update the size field
    O[:] = I[:]   # Copy to O
    write_block(block)  # Save changes to descriptor

def update_descriptor_block (d, n, i):
    ''' Update descriptor d so that its nth block number is block index i '''
    global I, O
    block, offset = get_descriptor_location(d)
    read_block(block)  # Now the block with the descriptor is in I
    n_start = offset + INT_SIZE + (n * INT_SIZE)  # The offset of the nth block number
    I[n_start : n_start + INT_SIZE] = i  # Record block i
    O[:] = I[:]  # Copy to O
    write_block(block)   # Save changes to the descriptor

def find_directory_entry (name):
    ''' Find the matching directory entry for file <name> return the descriptor index'''
    oft_entry = OFT[0]
    seek(0, 0)
    while True:
        file_position = oft_entry.position  # File position of the entry in the directory
        if file_position >= oft_entry.file_size:  # Check EOF
            return -1
        read(0, 0, DIR_ENTRY_SIZE)
        name_field = read_memory(0, FILE_NAME_SIZE)
        if name_field == name:
            descriptor_index = read_memory(FILE_NAME_SIZE, INT_SIZE)
            return descriptor_index

    
def find_free_directory_entry ():
    ''' Search directory for free entry, return its file position'''
    oft_entry = OFT[0]
    seek(0, 0)
    max_dir_size = 1536
    while True:
        file_position = oft_entry.position  # File position of the entry in the directory
        if file_position >= max_dir_size:
            return -1  # No entry found, and there is no more room for a new entry in the directory
        if file_position >= oft_entry.file_size:
            return file_position  # If no entry found, but there is still room for a new entry in the directory
        read(0, 0, DIR_ENTRY_SIZE)
        name_field = read_memory(0, FILE_NAME_SIZE)
        if name_field == 0:  # If existing free directory entry found, overwrite
            return file_position

def write_directory_entry (file_position, name, descriptor_index):
    ''' Overwrite directory entry at position with the new file name and descriptor index '''
    write_memory(0, name)
    write_memory(FILE_NAME_SIZE, descriptor_index)
    # Write entry to directory at OFT[0]
    seek(0, file_position)
    write(0, 0, DIR_ENTRY_SIZE)


def find_free_oft_entry ():
    ''' Find free OFT entry (current position = -1) '''
    global OFT
    for i in range(len(OFT)):
        if OFT[i].position == -1:
            return i 
    return -1

def create_oft_entry (entry, descriptor, file_size):
    ''' Create a new OFT entry for opening file '''
    global OFT, I
    OFT[entry].position = 0
    OFT[entry].descriptor_index = descriptor 
    OFT[entry].file_size = file_size
    if file_size == 0:  # allocate a free block as the file's first block
        block = find_free_block()
        update_descriptor_block(descriptor, 0, block)
        set_bitmap(block, 1)
        OFT[entry].rw_buffer = bytearray(512)
    else:
        block_numbers = get_descriptor_blocks(i)
        read_block(block_numbers[0])  # Now first block is in I
        OFT[entry].rw_buffer[:] = I[:]  # Copy the first block of the file into the r/w buffer


# File System Functions

def create (name):
    ''' Create a new file with the name name '''
    if check_directory_entry_exists(name):  # Check if file already exists
        raise Exception("error: duplicate file name")
    i = find_free_descriptor  # Search for free file descriptor i
    if i == -1:
        raise Exception("error: too many files")
    assign_descriptor(i)  # If free descriptor i found, assign i to new file
    position = find_free_directory_entry()  # Search for free directory entry j
    if position == -1:
        raise Exception("error: no free directory found")
    else:
        write_directory_entry(position, name, i)  # Record info in the directory entry
    return name

def destroy (name):
    ''' Destroy existing file <name> assuming file is not open '''
    # Search for directory entry of file
    oft_entry = OFT[0]
    seek(0, 0)  # Move current position in directory to 0
    while (oft_entry.position < oft_entry.size): # check EOF
        read(0, 0, DIR_ENTRY_SIZE) # Now next directory entry is in memory starting at M[m]
        name_field = read_memory(0, FILE_NAME_SIZE)
        if name_field == name:  # If found
            i = read_memory(FILE_NAME_SIZE, INT_SIZE)  # Descriptor index
            free_descriptor(i)
            write_memory(0, 0)  # mark directory entry as free by setting name field to 0
            return name
    raise Exception ("error: file does not exist")

def open (name):
    ''' Open file name '''
    # Search directory for file name and get the descriptor i
    i = find_directory_entry(name)
    if i == -1:
        raise Exception("error: file does not exist")
    # Search for free OFT entry j
    j = find_free_oft_entry()
    if j == -1:
        raise Exception("error: too many files open")
    file_size = get_descriptor_size(i)
    create_oft_entry(j, i, file_size)
    return name

def close (i):
    ''' Close file where OFT index is i, reversing the steps of open '''
    OFT[i].write_buffer_to_disk()
    update_descriptor_size(OFT[i].descriptor, OFT[i].file_size)
    OFT[i].position = -1   # Mark OFT entry as free
    return i

def read (i, m, n):
    ''' Copy n bytes from open file i (starting at current position) to memory M (start at M[m]) '''
    pass

def write (i, m, n):
    ''' Copy n bytes from memory M staarting at location m to open file i (starting at current position)'''
    pass

def seek (i, p):
    ''' Move current position within open file i to new position p '''
    pass

def directory ():
    ''' Display a list of all files and their sizes '''
    pass

# Shell

def initialize ():
    ''' Initialize system at start-up '''
    global D, I, O, M
    D = [bytearray(512) for block in range(64)]
    I = bytearray(512)
    O = bytearray(512)
    M = bytearray(512)
    OFT = [OFTEntry() for entry in range(4)]

    # All descriptors initially free (set descriptor file sizes to -1)
    # Descriptor 0: Directory (Initially with size 0 and block 7 allocated)
    # Remaining blocks 8-63 free (set bitmap)

def eval (user_input):
    command = user_input[0]
    if command == "cr":
        pass
    elif command == "de":
        pass
    elif command == "op":
        pass
    elif command == "cl":
        pass
    elif command == "rd":
        pass
    elif command == "wr":
        pass
    elif command == "sk":
        pass
    elif command == "dr":
        pass
    elif command == "in":
        pass
    elif command == "rm":
        pass
    elif command == "wm":
        pass
    else:
        raise SyntaxError

def main ():
    ''' Initialize system & run the Presentation/Test Shell '''
    initialize()
    while (True):
        try:
            user_input = input("").strip().split()  # Parse user input
            if not user_input:
                continue    # Ignore if empty
            eval(user_input)
        except:
            print("error")
            break

if __name__ == '__main__':
    main()
