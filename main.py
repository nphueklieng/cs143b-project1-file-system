# CS 143B - Project 1 (main.py)
# Name: Duangchanok Phueklieng (45231967)

class EmulatedDisk (self):
    def __init__(self):
        self.disk = [bytearray(512) for block in range(64)]

    def read_block(self):
        pass

    def write_block(self):
        pass
    
def initialize ():
    '''
    At start-up, initialize system
    '''



def main ():
    initialize()

if __name__ == '__main__':
    main()
