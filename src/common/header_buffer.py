from src.common.field_definition import FieldDefinition

class HeaderBuffer:
    def __init__(self, fields, binary_data=None):
        if isinstance(fields,list) and len(fields) == 3:
            # for fld in fields:
            #     print(f"{fld=}")
            self.field_name_order = fields[0]
            self.buffer = fields[1]
            self.field_descriptors = fields[2]
            self.validate()
            return
        
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
                # print(f"{binary_data[:fd.size]=}")
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
            # print(f"{binary_data[:field_size]=} : {type(binary_data[:field_size])=} : {type(binary_data)=} : {type(self.buffer[field_at_pos])=}")
            # print([pos, field_at_pos, field_size, self.buffer[field_at_pos]])
            binary_data = binary_data[field_size:]
        self.validate()

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
        is_order_list = isinstance(self.field_name_order, list)
        is_buffer_dict = isinstance(self.buffer, dict)
        is_definitions_list = isinstance(self.field_descriptors, dict)
        if not (is_order_list and is_buffer_dict and is_definitions_list):
            printables = [[is_order_list,type(self.field_name_order)]]
            printables = [[is_buffer_dict,type(self.buffer)]]
            printables = [[is_definitions_list,type(self.field_descriptors)]]
            raise Exception(f"0x000: Header Contents Mis-Match {printables=}")

        if (len(self.field_name_order) != len(self.buffer.keys()) or
            len(self.field_name_order) != len(self.field_descriptors.keys())):
            raise Exception("0x0F0: Header Contents Mis-Match")
        
        for field_name in self.field_name_order:
            is_name_str = isinstance(field_name, str)
            if not is_name_str:
                printables = [[is_name_str,type(field_name)]]
                raise Exception(f"0x0F8: Header Contents Mis-Match {printables=}")
            
            if (not field_name in self.buffer.keys() and
                not field_name in self.field_descriptors.keys()):
                raise Exception("0x0FF: Header Contents Mis-Match")
            
            is_definition_FD = isinstance(self.field_descriptors[field_name], FieldDefinition)
            if not is_definition_FD: #todo refactor to align descriptor/definition
                printables = [[is_definition_FD,type(self.field_descriptors[field_name])]]
                raise Exception(f"0x8F0: Header Contents Mis-Match {printables=}")

            if not (isinstance(self.buffer[field_name],bytes) or self.buffer[field_name] == None):
                raise Exception(f"0x8F8: Header Contents Mis-Match")


    def get_values_as_dict(self):
        results = {}
        for field_name in self.field_name_order:
            f_size = self.field_descriptors[field_name].size
            f_raw = self.buffer[field_name]
            results[field_name] = {'size' : f_size, 'data' : f_raw}
        return results
    
    def join(self, new_HeaderBuffer, pos=None):
        if not isinstance(new_HeaderBuffer, HeaderBuffer):
            raise ImportError(f"Invalid new_HeaderBuffer type: {isinstance(new_HeaderBuffer, HeaderBuffer)=}")

        # print(f"Running {self.join}")
        start_insert_at_pos = pos
        if pos == None:
            start_insert_at_pos = self.get_byte_width()
        
        new_fields_count = new_HeaderBuffer.field_count
        
        new_fields_buffer, new_field_descriptors = {}, {}
        new_field_order = []
        for currHB_f_pos, currHB_f_name in enumerate(self.field_name_order):
            if currHB_f_pos == start_insert_at_pos:
                for newHB_f_pos, newHB_f_name in enumerate(new_HeaderBuffer.field_name_order):
                    if newHB_f_name in new_fields_buffer.keys():
                      raise ImportError(f"Invalid merge. new_HeaderBuffer re-uses field name: {newHB_f_name=} is in new_fields_buffer.keys()")
                    # updated_HB_pos = currHB_f_pos + newHB_f_pos
                    # new_field_order[updated_HB_pos] = newHB_f_name
                    new_field_order.append(newHB_f_name)
                    new_field_descriptors[newHB_f_name] = new_HeaderBuffer.field_descriptors[newHB_f_name]
                    new_fields_buffer[newHB_f_name] = new_HeaderBuffer.buffer[newHB_f_name]
            else:
                # updated_HB_pos = currHB_f_pos if currHB_f_pos < start_insert_at_pos else currHB_f_pos + new_fields_count
                # new_field_order[updated_HB_pos] = currHB_f_name
                new_field_order.append(currHB_f_name)
                new_field_descriptors[currHB_f_name] = self.field_descriptors[currHB_f_name]
                new_fields_buffer[currHB_f_name] = self.buffer[currHB_f_name]

        return HeaderBuffer([new_field_order, new_fields_buffer, new_field_descriptors])

