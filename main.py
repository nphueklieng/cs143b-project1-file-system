# CS 143B - Project 1 (main.py)
# Name: Duangchanok Phueklieng (45231967)

from emulated_disk import EmulatedDisk
from file_system import FileSystem

DISK = None
FS = None

# Bitmap Mask Array
MASK = [0] * 64
MASK[63] = 0x0001
for i in range (62, 0, -1):
    MASK[i] = MASK[i + 1] << 1

def initialize ():
    ''' Initialize system at start-up '''
    global DISK
    DISK = EmulatedDisk()
    global FS
    FS = FileSystem()

    # Descriptor 0: Directory (Initially with length 0 and block 7 allocated)
    
    DISK.D[1] = 0

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
