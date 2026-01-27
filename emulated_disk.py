# CS 143B - Project 1 (emulated_disk.py)
# Name: Duangchanok Phueklieng (45231967)

class EmulatedDisk:
    def __init__ (self):
        self.D = [bytearray(512) for block in range(64)] # Byte array D[64][512]

    def read_block (self):
        pass

    def write_block (self):
        pass
