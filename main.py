# CS 143B - Project 1 (main.py)
# Name: Duangchanok Phueklieng (45231967)

# Emulated Disk

'''
Block 0: 64 bits bitmap (1 per block)
Blocks 1-6: 192 file descriptors (4 ints: file_size, B0, B1, B2) # 16 bytes per descriptor
    Directory Entries: File name (4 chars incl. string terminator), descriptor index (1 int) # 8 bytes per dir entry
'''

class FSError(Exception):
    def __init__(self, message):
        self.message = message

D = None
I = None
O = None
M = None
OFT = None

DIR_ENTRY_SIZE = 8 # bytes
FILE_NAME_SIZE = 4 # bytes
DESCRIPTOR_SIZE = 16 # bytes
INT_SIZE = 4 # bytes
MAX_FILE_SIZE = 512 * 3 # bytes

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
    global I, MASK
    read_block(0)  # read bitmap into I
    byte, bit = locate_block_in_bitmap(block)
    if (I[byte] & MASK[bit]):  # Extracting the bit. Only all 0 if bit is 0
        return 1
    return 0

def set_bitmap (block, status):
    ''' Set bit in bitmap for block to 1 (allocated) or 0 (free) '''
    global O, I, MASK
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
    
    def copy_buffer_to_disk (self):
        ''' Copy the current buffer contents to the block '''
        global O
        block = self.determine_block_in_buffer()
        O[:] = self.rw_buffer[:]   # copy r/w buffer to O
        write_block(block)   # Write O to D[block]

    def copy_block_to_buffer (self, block):
        ''' Load disk block into the OFT r/w buffer '''
        global I
        read_block(block)  # Now block is in I
        self.rw_buffer[:] = I[:]

    def copy_next_block_to_buffer (self):
        ''' Copy the next block to the r/w buffer '''
        n = self.position // 512   # which block we need next
        block_index = get_descriptor_blocks(self.descriptor_index)[n]
        self.copy_block_to_buffer(block_index)
        

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
    global OFT
    oft_entry = OFT[0]
    seek(0, 0)  # Move current position in directory to 0
    while (oft_entry.position < oft_entry.file_size): # check EOF
        read(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE) # Now next directory entry is at the end of M
        name_field = read_memory(512 - DIR_ENTRY_SIZE, 4)
        if name_field.decode('ascii') == name:
            return 1
    return 0

def find_free_descriptor ():
    ''' Find and return index of free descriptor '''
    global I
    for block in range(1, 7):
        read_block(block)
        for d in range(32):
            start = d * DESCRIPTOR_SIZE
            size_field = int.from_bytes(I[start : start + 4], 'little', signed=True)
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
    ''' return the size field in descriptor i'''
    global I
    block, offset = get_descriptor_location(i)
    read_block(block)
    size_field = int.from_bytes(I[offset : offset + INT_SIZE], 'little', signed=True)
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
        block_num = int.from_bytes(I[ block_start : block_start + INT_SIZE], 'little', signed=True)
        block_numbers.append(block_num)
    return block_numbers

def assign_descriptor (i):
    ''' Assign descriptor i to new file '''
    global O, I
    block, offset = get_descriptor_location(i)
    read_block(block)
    O[:] = I[:]
    O[offset : offset + INT_SIZE] = (0).to_bytes(INT_SIZE, 'little', signed=True)  # Set file descriptor size from -1 to 0
    O[offset + INT_SIZE : offset + DESCRIPTOR_SIZE] = [0] * 12   # Zero out the block numbers. 12 bytes is the size of the 3 fields
    write_block(block)

def free_descriptor (i):
    '''  Free descriptor i and its blocks '''
    global O, I
    block, offset = get_descriptor_location(i)
    read_block(block)
    O[:] = I[:]
    O[offset : offset + INT_SIZE] = (-1).to_bytes(INT_SIZE, 'little', signed=True)  # Set file descriptor size from 0 to -1
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
    I[offset : offset + INT_SIZE] = size.to_bytes(INT_SIZE, 'little', signed=True)  # Update the size field
    O[:] = I[:]   # Copy to O
    write_block(block)  # Save changes to descriptor

def update_descriptor_block (d, n, i):
    ''' Update descriptor d so that its nth block number is block index i '''
    global I, O
    block, offset = get_descriptor_location(d)
    read_block(block)  # Now the block with the descriptor is in I
    n_start = offset + INT_SIZE + (n * INT_SIZE)  # The offset of the nth block number
    I[n_start : n_start + INT_SIZE] = i.to_bytes(INT_SIZE, 'little', signed=True)  # Record block i
    O[:] = I[:]  # Copy to O
    write_block(block)   # Save changes to the descriptor

def find_directory_entry (name):
    ''' Find the matching directory entry for file <name> return the descriptor index'''
    global OFT
    seek(0, 0)
    while True:
        if OFT[0].position >= OFT[0].file_size:  # Check EOF
            return -1
        read(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE)  # now directory entry is at the end pf M
        name_field = read_memory(512 - DIR_ENTRY_SIZE, FILE_NAME_SIZE).decode('ascii').strip('\x00')  # strip null
        if name_field == name:
            descriptor_index = int.from_bytes(read_memory(512 - DIR_ENTRY_SIZE + FILE_NAME_SIZE, INT_SIZE), 'little', signed=True)
            return descriptor_index

    
def find_free_directory_entry ():
    ''' Search directory for free entry, return its file position'''
    global OFT
    oft_entry = OFT[0]
    seek(0, 0)
    max_dir_size = 1536
    while True:
        file_position = oft_entry.position  # File position of the entry in the directory
        if file_position >= max_dir_size:
            return -1  # No entry found, and there is no more room for a new entry in the directory
        if file_position >= oft_entry.file_size:
            return file_position  # If no entry found, but there is still room for a new entry in the directory
        read(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE)  # Put at the end of M
        name_field = read_memory(512 - DIR_ENTRY_SIZE, FILE_NAME_SIZE)
        if name_field[0] == 0:  # If existing free directory entry found, overwrite
            return file_position

def write_directory_entry (file_position, name, descriptor_index):
    ''' Overwrite directory entry at position with the new file name and descriptor index '''
    padded_name = name.ljust(FILE_NAME_SIZE, '\0').encode('ascii')
    write_memory(512 - DIR_ENTRY_SIZE, padded_name)
    write_memory(512 - DIR_ENTRY_SIZE + FILE_NAME_SIZE, descriptor_index.to_bytes(INT_SIZE, 'little', signed=True))
    # Write entry to directory at OFT[0]
    seek(0, file_position)
    write(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE)

# TODO: Problem with using M as a "scratchpad" for OS

def find_free_oft_entry ():
    ''' Find free OFT entry (current position = -1) '''
    global OFT
    for i in range(len(OFT)):
        if OFT[i].position == -1:
            return i

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
    global OFT
    if check_directory_entry_exists(name):  # Check if file already exists
        raise FSError("error: duplicate file name")
    i = find_free_descriptor()  # Search for free file descriptor i
    if i == -1:
        raise FSError("error: too many files")
    position = find_free_directory_entry()  # Search for free directory entry j
    if position == -1:
        raise FSError("error: no free directory found")
    assign_descriptor(i)  # If free descriptor i found, assign i to new file
    write_directory_entry(position, name, i)  # Record info in the directory entry
    # If the new directory entry extends the directory, upate its size
    if (position + DIR_ENTRY_SIZE) > OFT[0].file_size: 
        OFT[0].file_size = (position + DIR_ENTRY_SIZE)
        update_descriptor_size(0, position + DIR_ENTRY_SIZE)
    return name

def destroy (name):
    ''' Destroy existing file <name> assuming file is not open '''
    # Search for directory entry of file
    global OFT
    oft_entry = OFT[0]
    seek(0, 0)  # Move current position in directory to 0
    while (oft_entry.position < oft_entry.file_size): # check EOF
        read(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE) # Now next directory entry is in memory starting at M[m]
        name_field = read_memory(512 - DIR_ENTRY_SIZE, FILE_NAME_SIZE).decode('ascii').strip('\x00')
        if name_field == name:  # If found
            i = int.from_bytes(read_memory(512 - DIR_ENTRY_SIZE + FILE_NAME_SIZE, INT_SIZE), 'little', signed=True)  # Descriptor index
            free_descriptor(i)
            write_memory(512 - DIR_ENTRY_SIZE, [0] * DIR_ENTRY_SIZE)  # mark directory entry in M as free by setting name field to 0
            seek(0, oft_entry.position - DIR_ENTRY_SIZE) 
            write(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE)  # Now write back the changes to the directory file
            return name
    raise FSError("error: file does not exist")

def open (name):
    ''' Open file name '''
    # Search directory for file name and get the descriptor i
    i = find_directory_entry(name)
    if i == -1:
        raise FSError("error: file does not exist")
    # Search for free OFT entry j
    j = find_free_oft_entry()
    if j == -1:
        raise FSError("error: too many files open")
    file_size = get_descriptor_size(i)
    create_oft_entry(j, i, file_size)
    return name, j

def close (i):
    ''' Close file where OFT index is i, reversing the steps of open '''
    global OFT
    OFT[i].copy_buffer_to_disk()
    update_descriptor_size(OFT[i].descriptor_index, OFT[i].file_size)
    OFT[i].position = -1   # Mark OFT entry as free
    return i

def read (i, m, n):
    ''' Copy n bytes from open file i (starting at current position) to memory M (start at M[m]) '''
    global OFT
    size = OFT[i].file_size
    count = 0  # How many bytes read?
    while True:
        buf_position = OFT[i].position % 512  # position in rw buffer
        if count == n or OFT[i].position >= size:  # Check EOF or all bytes read
            # bytes_read = read_memory(m, count)
            return count, i
        if buf_position == 0 and OFT[i].position != 0:  # Check end of r/w buffer reached
            OFT[i].copy_buffer_to_disk()
            OFT[i].copy_next_block_to_disk()
            buf_position = 0  # Reset buffer position to start of the r/w buffer
        write_memory(m + count, OFT[i].rw_buffer[buf_position : buf_position + 1])  # Write the byte from rw_buffer into M
        count += 1
        OFT[i].position += 1

def write (i, m, n):
    ''' Copy n bytes from memory M starting at location m to open file i (starting at current position)'''
    global OFT
    d = OFT[i].descriptor_index
    count = 0  # How many bytes written ?
    while True:
        buf_position = OFT[i].position % 512  # Position in rw buffer
        # Check desired count n reached or Max file size
        if count == n or OFT[i].file_size >= MAX_FILE_SIZE:   
            pos = OFT[i].position
            if pos > OFT[i].file_size: # Update size in oft entry and descriptor
                OFT[i].file_size = OFT[i].position
                update_descriptor_size(d, pos)
            return count, i
        # Check end of buffer reached
        if buf_position == 0 and OFT[i].position != 0:
            OFT[i].copy_buffer_to_disk()
            n = OFT[i].position // 512  # Which block?
            block = get_descriptor_blocks(d)[n] 
            if block != 0:  # If the next block exists
                OFT[i].copy_block_to_buffer(block)
            else:  # allocate a new block to the file
                block = find_free_block()
                update_descriptor_block(d, n, block)
                set_bitmap(block, 1)
                OFT[i].rw_buffer = bytearray(512)  # New block means fresh r/w buffer
            buf_position = 0  # Reset buffer position to start of the r/w buffer
        OFT[i].rw_buffer[buf_position : buf_position + 1] = read_memory(m + count, 1)  # Read the byte from M into rw_buffer
        count += 1 
        OFT[i].position += 1

def seek (i, p):
    ''' Move current position within open file i to new position p '''
    global OFT
    if p > OFT[i].file_size:
        raise FSError("error: current position is past the end of file")
    # Check file blocks (b0, b1, b2)
    curr_block = OFT[i].position // 512
    new_block = p // 512
    if curr_block != new_block:
        b = get_descriptor_blocks(OFT[i].descriptor)[new_block]  # Get its block index
        OFT[i].copy_buffer_to_disk()
        OFT[i].copy_block_to_buffer(b)
    OFT[i].position = p
    return p

def directory ():
    ''' Display a list of all files and their sizes '''
    global OFT
    seek(0, 0)
    dir_size = OFT[0].file_size
    while OFT[0].position < dir_size:
        read(0, 512 - DIR_ENTRY_SIZE, DIR_ENTRY_SIZE)  # Now dir entry is at M[0 : 8]
        file_name = read_memory(512 - DIR_ENTRY_SIZE, INT_SIZE).decode('ascii').strip('\x00')  # M[0 : 4]
        descriptor_index = int.from_bytes(read_memory(512 - DIR_ENTRY_SIZE + FILE_NAME_SIZE, INT_SIZE), 'little', signed=True)  # M[4 : 8]
        if file_name:  # If not empty
            file_size = get_descriptor_size(descriptor_index)
            print(f"{file_name} {file_size}", end=" ")
    print()
    return 0

# Shell

def init ():
    ''' Initialize system at start-up '''
    global D, I, O, M, OFT
    D = [bytearray(512) for block in range(64)]
    I = bytearray(512)
    O = bytearray(512)
    M = bytearray(512)
    OFT = [OFTEntry() for entry in range(4)]
    # All descriptors initially free (set descriptor file sizes to -1)
    for d in range(192):
        update_descriptor_size(d, -1)
    # Descriptor 0: Directory (Initially with size 0 and block 7 allocated)
    update_descriptor_size(0, 0)
    update_descriptor_block(0, 0, 7)
    OFT[0].position = 0    # OFT[0] reserved for open directory
    # Remaining blocks 8-63 free, but 0-7 are allocated (set bitmap)
    for b in range(0, 7):
        set_bitmap(b, 1)


def eval (input):
    command = input[0]
    if command == "cr":
        name = create(input[1])
        print(f"{name} created")
    elif command == "de":
        name = destroy(input[1])
        print(f"{name} destroyed")
    elif command == "op":
        name, index = open(input[1])
        print(f"{name} opened {index}")
    elif command == "cl":
        index = close(int(input[1]))
        print(f"{index} closed")
    elif command == "rd":
        n, index = read(int(input[1]), int(input[2]), int(input[3]))
        print(f"{n} bytes read from {index}")
    elif command == "wr":
        n, index = write(int(input[1]), int(input[2]), int(input[3]))
        print(f"{n} bytes written to {index}")
    elif command == "sk":
        p = seek(int(input[1]), int(input[2]))
        print(f"position is {p}")
    elif command == "dr":
        directory()
    elif command == "in":
        init()
        print("system initialized")
    elif command == "rm":
        x = read_memory(int(input[1]), int(input[2])).decode('ascii').strip('\x00')
        print(x)
    elif command == "wm":
        n = write_memory(int(input[1]), input[2].encode('ascii'))
        print(f"{n} bytes written to M")
    else:
        raise SyntaxError

def main ():
    ''' Initialize system & run the Presentation/Test Shell '''
    init()
    while (True):
        try:
            user_input = input("").strip().split()  # Parse user input
            if not user_input:
                print()
                continue    # Ignore if empty
            eval(user_input)
        except EOFError:
            break  # input.txt is done
        except FSError:
            print("error")
            
if __name__ == '__main__':
    main()
