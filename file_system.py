# CS 143B - Project 1 (file_system.py)
# Name: Duangchanok Phueklieng (45231967)

class OFTEntry:
    def __init__ (self):
        self.rw_buffer = bytearray(512)
        self.position = 0
        self.file_size = 0
        self.descriptor_index = 0


class FileSystem:
    def __init__ (self):
        self.I = bytearray(512)
        self.O = bytearray(512)
        self.M = bytearray(512)
        self.OFT = [OFTEntry() for entry in range(4)]

    def read_memory (self):
        pass

    def write_memory (self):
        pass

    def create (self):
        pass

    def destroy (self):
        pass

    def open (self):
        pass

    def close (self):
        pass

    def read (self):
        pass

    def write (self):
        pass

    def seek (self):
        pass

    def directory (self):
        pass

