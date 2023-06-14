
from src.common.munchie import Munchie
from src.common.constants import LABEL_CHECKSUM, LABEL_COMPLEMENT
from munch import Munch

def _from_list(arg_array, key_cb=lambda x:x, val_cb=lambda x:x):
    arg_array = list(arg_array)

    def normalize_key(arg_string):
        US = '_'
        is_normal = lambda c : c.isalnum() or c in [US]
        normal_key = ''.join(
            [c if is_normal(c) else US for c in arg_string]
        )
        if is_normal:
            return normal_key

    temp_keys = list(map(key_cb, arg_array.copy()))
    temp_values = list(map(val_cb, arg_array.copy()))
    for key_val in arg_array:                # use the original to iterate
        normal_key = normalize_key(key_val)
        if key_val != normal_key:            # so we can modify the copys
            temp_keys.append(normal_key)
            temp_values.append(key_val)
    
    return Munch(dict(zip(temp_keys, temp_values)))
Munch.from_list = _from_list

def _from_two_lists(key_list, value_list):
    if len(key_list) != len(value_list):
        raise Exception("Can't Munch with mismatch argument lengths")
    return Munch(dict(zip(key_list, value_list)))
Munch.from_two_lists = _from_two_lists


KEYS = Munch()
KEYS.COMMON = Munch.from_list(["NAME","SIZE","VALUE"])

def munch_name(name):
    return Munch({KEYS.COMMON.NAME : name})

def munch_name_size(name,size):
    keys = [KEYS.COMMON.NAME, KEYS.COMMON.SIZE]
    return Munch.from_two_lists(keys, [name,size])

def munch_name_value(name,value):
    keys = [KEYS.COMMON.NAME, KEYS.COMMON.VALUE]
    return Munch.from_two_lists(keys, [name,value])

# squash all values for each key of a dictionary down to
# the value of a specific subkey at key
def _squash_munch(dict_to_munch, squash_at_key):
    new_munch = Munch()
    for key,val in dict_to_munch.items():
        new_munch[key] = val[squash_at_key]
    return new_munch


KEYS.CHIPSET = Munch.from_list([
    "ROM_ONLY", "ROM_RAM", "ROM_RAM_BATTERY", 
    "ROM_COPROCESSOR", "ROM_COPROCESSOR_RAM", "ROM_COPROCESSOR_RAM_BATTERY",
    "ROM_COPROCESSOR_BATTERY"
])

KEYS.CHIP  = Munch.from_list([
    'ROM','RAM','BATTERY','COPROCESSOR',            # Normal Chips
    'DSP', 'GSU', 'OBC1', 'SA_1', 'S_DD1', 'S_RTC', # Coprocessor Chips
    "OTHER", "CUSTOM",
    "SPC7110", "ST010_ST011", "ST018", "CX4"        # Custom Coprocessors
])

LABELS = Munch()
LABELS.HARDWARE = Munch()
LABELS.HARDWARE.CHIP = Munch({
    #Normal Chips
    KEYS.CHIP.ROM           : 'ROM',      KEYS.CHIP.RAM           : 'RAM',
    KEYS.CHIP.BATTERY       : 'BATTERY',  KEYS.CHIP.COPROCESSOR   : 'coprocessor',
    # Coprocessor Chips
    KEYS.CHIP.DSP           : 'DSP',      KEYS.CHIP.GSU           : 'GSU',
    KEYS.CHIP.OBC1          : 'OBC1',     KEYS.CHIP.SA_1          : 'SA-1',
    KEYS.CHIP.S_DD1         : 'S-DD1',    KEYS.CHIP.S_RTC         : 'S-RTC',
    KEYS.CHIP.OTHER         : 'other',    KEYS.CHIP.CUSTOM        : 'custom',
    # Custom Coprocessors
    KEYS.CHIP.SPC7110       : 'SPC7110',  KEYS.CHIP.ST010_ST011   : 'ST010/ST011',
    KEYS.CHIP.ST018         : 'ST018',    KEYS.CHIP.CX4           : 'CX4'
})
def _make_chipset_label(chip_keys):
    return "+".join([LABELS.HARDWARE.CHIP[k] for k in chip_keys])

LABELS.HARDWARE.CHIPSET = Munch({
    KEYS.CHIPSET.ROM_ONLY                     : _make_chipset_label(['ROM']),      
    KEYS.CHIPSET.ROM_RAM                      : _make_chipset_label(['ROM','RAM']), 
    KEYS.CHIPSET.ROM_RAM_BATTERY              : _make_chipset_label(['ROM','RAM', 'BATTERY']), 
    KEYS.CHIPSET.ROM_COPROCESSOR              : _make_chipset_label(['ROM','COPROCESSOR']),      
    KEYS.CHIPSET.ROM_COPROCESSOR_RAM          : _make_chipset_label(['ROM','COPROCESSOR','RAM']),      
    KEYS.CHIPSET.ROM_COPROCESSOR_RAM_BATTERY  : _make_chipset_label(['ROM','COPROCESSOR','RAM', 'BATTERY']),      
    KEYS.CHIPSET.ROM_COPROCESSOR_BATTERY      : _make_chipset_label(['ROM','COPROCESSOR', 'BATTERY']),      
})

# the NAME and SIZE of each field
FIELDS = Munch(
    MAKER_CODE         = munch_name_size('Maker ID',          2),
    GAME_CODE          = munch_name_size('Game ID',           4),
    FIXED_BYTE         = munch_name_size('Fixed Byte',        1),
    FLASH_SIZE         = munch_name_size('Flash Size',        1),
    EX_RAM_SIZE        = munch_name_size('Ex. RAM Size',      1),
    SPECIAL_VERSION    = munch_name_size('Special Version',   1),
    CHIPSET_SUB_TYPE   = munch_name_size('Chipset Sub-Type',  1),
    GAME_TITLE         = munch_name_size('Game Title',       21),
    MAP_SPEED          = munch_name_size('Map/Speed',         1),
    CHIPSET            = munch_name_size('Chipset',           1),
    ROM_SIZE           = munch_name_size('ROM Size',          1),
    RAM_SIZE           = munch_name_size('RAM Size',          1),
    COUNTRY            = munch_name_size('Country',           1),
    DEV_ID             = munch_name_size('Dev ID',            1),
    VERSION            = munch_name_size('Version',           1),
    COMPLEMENT         = munch_name_size('Complement',        2),
    CHECKSUM           = munch_name_size('Checksum',          2),
    INTERRUPT_VECTORS  = munch_name_size('Interrupts',       32)
)


KEYS.FIELD  = Munch.from_list(FIELDS.keys())           # add FIELDS keys to KEYS.FIELD as source of record
LABELS.FIELD = _squash_munch(FIELDS, KEYS.COMMON.NAME) # add FIELDS names to LABELS.FIELD for quick access


# Build layouts to map the bytes of a block of memory into fields
# Enter HEADER.FIELD values in order into list HEADER.LAYOUT.<header_block>
LAYOUT = Munch()
LAYOUT.EXPANDED = [
    FIELDS.MAKER_CODE, 
    FIELDS.GAME_CODE,
]
LAYOUT.EXPANDED.append(                  # Expanded Header has 6 FIXED_BYTEs.
    [FIELDS.FIXED_BYTE for i in range(6)] # The duplicate names will need to
)                                               # be managed by the buffering process
LAYOUT.EXPANDED.append([
    FIELDS.FLASH_SIZE, 
    FIELDS.EX_RAM_SIZE, 
    FIELDS.SPECIAL_VERSION, 
    FIELDS.CHIPSET_SUB_TYPE
])

LAYOUT.NORMAL = [
    FIELDS.GAME_TITLE,
    FIELDS.MAP_SPEED,
    FIELDS.CHIPSET,
    FIELDS.ROM_SIZE,
    FIELDS.RAM_SIZE,
    FIELDS.COUNTRY,
    FIELDS.DEV_ID,
    FIELDS.VERSION,
    FIELDS.COMPLEMENT,
    FIELDS.CHECKSUM
]
LAYOUT.FULL = LAYOUT.EXPANDED.copy() +  LAYOUT.NORMAL.copy()

# LABELS.FIELD = Munch()
print(LABELS.FIELD)
Munchie._scream()

# chipset = Munch(keys = KEYS.CONFIG.CHIPSET, labels = LABELS.HARDWARE.CHIPSET.CONFIG)
# HEADER.CONFIG.CHIPSET = Munch({
#     chipset.keys.ROM_ONLY : munch_name_value(chipset.labels.ROM_ONLY, 0x0),
#     chipset.keys.ROM_RAM  : Munch(NAME=chipset.labels.CONFIG.ROM_RAM_BATTERY, VALUE=0x1),
#     chipset.keys.ROM_RAM_BATTERY : Munch(NAME=LABELS.HARDWARE.CONFIG.ROM_RAM_BATTERY, VALUE=0x2),
#     chipset.keys.ROM_COPROCESSOR : Munch(NAME=LABELS.HARDWARE.CONFIG.ROM_COPROCESSOR, VALUE=0x3),
#     chipset.keys.ROM_COPROCESSOR_RAM : Munch(NAME=LABELS.HARDWARE.CONFIG.ROM_COPROCESSOR_RAM, VALUE=0x4),
#     chipset.keys.ROM_COPROCESSOR_RAM_BATTERY : Munch(NAME=LABELS.HARDWARE.CONFIG.ROM_COPROCESSOR_RAM_BATTERY, VALUE=0x5),
#     chipset.keys.ROM_COPROCESSOR_BATTERY : Munch(NAME=LABELS.HARDWARE.CONFIG.ROM_COPROCESSOR_BATTERY, VALUE=0x6)
# })



# HEADER.FIELDS.COPROCESSOR = Munch(NAME="Co-Processor")
# HEADER.FIELDS.COPROCESSOR.CONFIG = Munch(
#     DSP=Munch(NAME='DSP',VALUE=0x0),
#     GSU=Munch(NAME='GSU',VALUE=0x1),
#     OBC1=Munch(NAME='OBC1',VALUE=0x2),
#     SA1=Munch(NAME='SA1',VALUE=0x3),
#     SDD1=Munch(NAME='SDD1',VALUE=0x4),
#     SRTC=Munch(NAME='SRTC',VALUE=0x5),
#     OTHER=Munch(NAME='OTHER',VALUE=0xE),
#     CUSTOM=Munch(NAME='CUSTOM',VALUE=0xF)
# )
# HEADER.FIELDS.CUSTOM_COPROCESSOR = Munch(NAME="Chipset SubType")
# HEADER.FIELDS.CUSTOM_COPROCESSOR.CONFIG = Munch(
#     SPC7110 = Munch(NAME='SPC7110',VALUE=0x00),
#     ST010_ST011 = Munch(NAME='ST010/ST011',VALUE=0x01),
#     ST018 = Munch(NAME='ST018',VALUE=0x02),
#     CX4 = Munch(NAME='CX4',VALUE=0x03)
# )


# HARDWARE.CHIP.update(
#     DSP=HEADER.FIELDS.COPROCESSOR.CONFIG.DSP.NAME,
#     GSU=HEADER.FIELDS.COPROCESSOR.CONFIG.GSU.NAME,
#     OBC1=HEADER.FIELDS.COPROCESSOR.CONFIG.OBC1.NAME,
#     SA1=HEADER.FIELDS.COPROCESSOR.CONFIG.SA1.NAME,
#     SDD1=HEADER.FIELDS.COPROCESSOR.CONFIG.SDD1.NAME,
#     SRTC=HEADER.FIELDS.COPROCESSOR.CONFIG.SRTC.NAME,
#     SPC7110 = HEADER.FIELDS.CUSTOM_COPROCESSOR.CONFIG.SPC7110.NAME,
#     ST010_ST011 = HEADER.FIELDS.CUSTOM_COPROCESSOR.CONFIG.ST010_ST011.NAME,
#     ST018 = HEADER.FIELDS.CUSTOM_COPROCESSOR.CONFIG.ST018.NAME,
#     CX4 = HEADER.FIELDS.CUSTOM_COPROCESSOR.CONFIG.CX4.NAME
# )


# CUSTOM_COPROCESSOR_DICTIONARY = {
#     VALUE_SPC7110: LABEL_SPC7110,
#     VALUE_ST010_ST011: LABEL_ST010_ST011,
#     VALUE_ST018: LABEL_ST018,
#     VALUE_CX4: LABEL_CX4
# }
# CUSTOM_COPROCESSOR_DICTIONARY = dict(CUSTOM_COPROCESSOR_DICTIONARY)

# chipset.CHIPSETS_WITH_COPROCESSOR = [
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR,
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_RAM,
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_RAM_BATTERY,
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_BATTERY
# ]

# chipset.COPROCESSOR_DICTIONARY = [
#     [chipset.VALUE.COPROCESSOR.DSP, chipset.LABEL.CHIP_DSP],
#     [chipset.VALUE.COPROCESSOR.GSU, chipset.LABEL.CHIP_GSU],
#     [chipset.VALUE.COPROCESSOR.OBC1, chipset.LABEL.CHIP_OBC1],
#     [chipset.VALUE.COPROCESSOR.SA1, chipset.LABEL.CHIP_SA1],
#     [chipset.VALUE.COPROCESSOR.SDD1, chipset.LABEL.CHIP_SDD1],
#     [chipset.VALUE.COPROCESSOR.SRTC, chipset.LABEL.CHIP_SRTC],
#     [chipset.VALUE.COPROCESSOR.OTHER, chipset.LABEL.CHIP_OTHER],
#     [chipset.VALUE.COPROCESSOR.CUSTOM, chipset.LABEL.CHIP_CUSTOM]
# ]
# chipset.COPROCESSOR_DICTIONARY = dict(chipset.COPROCESSOR_DICTIONARY)




# HEADER.CHIPSET_DICTIONARY = {
#     chipset.VALUE.CHIPSET.ROM_ONLY:                     [chipset.LABEL.CHIP_ROM],
#     chipset.VALUE.CHIPSET.ROM_RAM:                      [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_RAM],
#     chipset.VALUE.CHIPSET.ROM_RAM_BATTERY:              [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_RAM, chipset.LABEL.CHIP_BATTERY],
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR:              [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_COPROCESSOR],
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_RAM:          [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_COPROCESSOR, chipset.LABEL.CHIP_RAM],
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_RAM_BATTERY:  [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_COPROCESSOR, chipset.LABEL.CHIP_RAM, chipset.LABEL.CHIP_BATTERY],
#     chipset.VALUE.CHIPSET.ROM_COPROCESSOR_BATTERY:      [chipset.LABEL.CHIP_ROM, chipset.LABEL.CHIP_COPROCESSOR, chipset.LABEL.CHIP_BATTERY]
# }
# # chipset.CHIPSET_DICTIONARY = dict(chipset.CHIPSET_DICTIONARY)