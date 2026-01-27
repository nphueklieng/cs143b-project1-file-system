# CS 143B - Project 1 (main.py)
# Name: Duangchanok Phueklieng (45231967)

from emulated_disk import EmulatedDisk
from file_system import FileSystem

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
    ''' Run the Presentation/Test Shell '''
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
