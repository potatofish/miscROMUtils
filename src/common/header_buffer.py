from src.common.field_definition import FieldDefinition

class HeaderBuffer:
    def __init__(self, fields, binary_data=None):
        self.buffer, self.field_descriptors = {}, {}
        self.field_name_order = []
        for fd in fields:
            if isinstance(fd,tuple):
                fd = FieldDefinition(fd[0],fd[1])
            if not isinstance(fd, FieldDefinition):
                raise TypeError(f'Expected FieldDefinition, got {type(fd).__name__}')
            
            field_name = fd.name
            self.field_name_order.append(field_name)
            self.field_descriptors[field_name] = fd
            if binary_data != None:
                self.buffer[field_name] = binary_data[:fd.size]
                binary_data = binary_data[fd.size:]
            else:
                self.buffer[fd.name] = None
    
    def fill_buffer(self, binary_data, field_to_fill=None, overflow=False):
        self.validate()
        if field_to_fill == None:
            field_to_fill = self.get_field_label_by_position(0)

        if not overflow:
            if len(binary_data) == self.get_field_size(field_to_fill):
                self.buffer[field_to_fill] = binary_data
                return
            else:
                raise Exception("Unexpected length for binary_data/field combination")
        
        #otherwise overflow
        for pos in range(self.get_field_position_by_label(field_to_fill), self.field_count()):
            if len(binary_data) == 0:
                break
            field_at_pos = self.get_field_label_by_position(pos)
            field_size = self.get_field_size(field_at_pos)
            self.buffer[field_at_pos] = binary_data[:field_size]
            binary_data = binary_data[field_size:]

    def field_count(self):
        self.validate()
        return len(self.field_name_order)
    
    def get_field_size(self, field_name):
        self.validate()
        if isinstance(field_name, int):
            field_name = self.get_field_label_by_position(field_name)
        return self.field_descriptors[field_name].size
    
    def get_field_data(self, field_name, cb=lambda x : x):
        # print(f"{type(field_name)=}")
        self.validate()
        if isinstance(field_name, int):
            field_name = self.get_field_label_by_position(field_name)
        
        if isinstance(field_name, str):
            return self.buffer[field_name]
        elif isinstance(field_name, list):
            return [self.buffer[name] for name in field_name]
        else:
            raise KeyError(f"field name of unknown type={type(field_name)}")
    
    def get_field_position_by_label(self, field_name):
        self.validate()
        return self.field_name_order.index(field_name)
    
    def get_field_label_by_position(self, field_pos):
        return self.field_name_order[field_pos]
    
    def get_byte_width(self, start=0, stop=None):
        if isinstance(start, str):
            start = self.get_field_position_by_label(start)
        if stop is None:
            stop = self.field_count()
        elif isinstance(stop, str):
            stop = self.get_field_position_by_label(stop)
        # print(f"get_byte_width({start}:{stop})")
        byte_width = 0
        for pos in range(start, stop):
            field_name = self.get_field_label_by_position(pos)
            field_width = self.get_field_size(field_name)
            # print(f"{field_name} @ {pos} is {field_width} bytes")
            byte_width += field_width
        return byte_width


    def validate(self):
        if (len(self.field_name_order) != len(self.buffer.keys()) or
            len(self.field_name_order) != len(self.field_descriptors.keys())):
            raise Exception("Header Contents Mis-Match")
        
        for field_name in self.field_name_order:
            if (not field_name in self.buffer.keys() and
                not field_name in self.field_descriptors.keys()):
                raise Exception("Header Contents Mis-Match")
