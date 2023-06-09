COPIER_HEADER_SIZE = 512

LABEL_MAP_MODE = "Map Mode"
LABEL_COMPLEMENT = "Complement"
LABEL_CHECKSUM = "Checksum"

LABEL_MAPSPEED = "Map/Speed"
MAPSPEED_BITS_FIXED_0 = [7,6,3]
MAPSPEED_BITS_FIXED_1 = [5]
MAPSPEED_BIT_SPEED = 4
MAPSPEED_BIT_EX = 2
MAPSPEED_BIT_SPECIAL = 1
MAPSPEED_BIT_HI_LO = 0

SPEED_MODE_SLOW, SPEED_MODE_FAST = 0, 1
SPEED_MODE_LABELS = [
    [SPEED_MODE_SLOW, "Slow"],
    [SPEED_MODE_FAST, "Fast"]
]
SPEED_MODE_LABELS = dict(SPEED_MODE_LABELS)


LABEL_ROM_LO = "LoROM"
LABEL_ROM_HI = "HiROM"
LABEL_ROM_EXHI = "ExHiROM"
LABEL_ROM_SA_1 = "SA-1 ROM"
LABEL_ROM_SDD_1 = "SDD-1 ROM"
LABEL_ROM_UNKN = "Unknown ROM"
HI_LO_MODE_LOROM, HI_LO_MODE_HIROM = 0, 1
HI_LO_MODE_LABELS = [
    [HI_LO_MODE_LOROM, LABEL_ROM_LO],
    [HI_LO_MODE_HIROM, LABEL_ROM_HI]
]
HI_LO_MODE_LABELS = dict(HI_LO_MODE_LABELS)

HEADER_OFFSETS = [
    [LABEL_ROM_LO, 0x_7F_B0],
    [LABEL_ROM_HI, 0x_FF_B0],
    [LABEL_ROM_EXHI, 0x_40_FF_B0]
]
HEADER_OFFSETS = dict(HEADER_OFFSETS)

HEADER_FIELDS = [
    ("Maker Code", 2), 
    ("Game Code", 4), 
    ("Fixed Byte[0]", 1), 
    ("Fixed Byte[1]", 1), 
    ("Fixed Byte[2]", 1), 
    ("Fixed Byte[3]", 1), 
    ("Fixed Byte[4]", 1), 
    ("Fixed Byte[5]", 1), 
    ("ExFlash Size", 1), 
    ("ExRAM Size", 1), 
    ("Special Version", 1), 
    ("Cart SubType", 1), 
    ("Game title", 21), 
    (LABEL_MAPSPEED, 1), 
    ("Hardware", 1), 
    ("ROM Size", 1), 
    ("RAM Size", 1), 
    ("Country Code", 1), 
    ("Has ExHeader", 1), 
    ("ROM version", 1),
    (LABEL_COMPLEMENT, 2),
    (LABEL_CHECKSUM, 2)
]
