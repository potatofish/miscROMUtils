class HeaderBuffer:
    def __init__(self, binary_data, fields):
        self.buffer = {}
        for fd in fields:
            self.buffer[fd.name] = binary_data[:fd.size]
            binary_data = binary_data[fd.size:]

        