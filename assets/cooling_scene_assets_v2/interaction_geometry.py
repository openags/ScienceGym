"""Source topology and explicitly inferred contact locations, shared with tasks.

Pin identities: USB-TC Rev10A Figure2/p8 and Table14/p17, visually inspected.
Exact connector pitch is not supplied by that schematic. Sensor coordinates
are a proposed SI-Figure5 reconstruction, never measured historical positions.
"""
TC_CHANNEL_PINS = [(3, 4), (7, 8), (13, 14), (17, 18),
                   (44, 43), (40, 39), (34, 33), (30, 29)]
PIN_SIGNALS = {
    1:'RSVD',2:'NC',3:'C0H',4:'C0L',5:'NC',6:'RSVD',7:'C1H',8:'C1L',9:'GND',10:'RSVD',
    11:'RSVD',12:'NC',13:'C2H',14:'C2L',15:'NC',16:'RSVD',17:'C3H',18:'C3L',19:'GND',20:'RSVD',
    21:'+5V',22:'GND',23:'DIO0',24:'DIO1',25:'DIO2',26:'DIO3',
    27:'RSVD',28:'GND',29:'C7L',30:'C7H',31:'RSVD',32:'NC',33:'C6L',34:'C6H',35:'NC',36:'RSVD',
    37:'RSVD',38:'GND',39:'C5L',40:'C5H',41:'RSVD',42:'NC',43:'C4L',44:'C4H',45:'NC',46:'RSVD',
    47:'+5V',48:'GND',49:'DIO7',50:'DIO6',51:'DIO5',52:'DIO4',
}

# Coordinates relative to bottom of the two-layer insulation, at one selected
# azimuth. Z is upward, X follows the SI cross section. Units are metres.
SENSOR_LAYOUT = [
    ('TC_W','emitter_copper',(0,0,.0500),'backside near centre','source-related contact; exact patch inferred'),
    ('TC_MAP_1','foam_2',(0,0,.045),'inside upper insulation near axis','depth inferred from SI Figure5; prepare a retained probe recess'),
    ('TC_MAP_2','foam_1',(0,0,.025),'insulation centre near layer boundary','inferred layer-interface placement; do not assume external surface contact'),
    ('TC_MAP_3','PE_support',(.038,0,.030),'inner PE wall','approximate SI surface association; azimuth inferred'),
    ('TC_MAP_4','PE_support',(.051,0,.030),'outer PE wall','approximate SI surface association; Mylar contact order must be qualified'),
    ('TC_MAP_5','radiation_shield',(.070,0,.032),'inner aluminum shield wall','approximate SI surface association; height inferred'),
    ('TC_MAP_6','aperture_plate',(.052,0,.0634),'underside of upper aluminum aperture plate','approximate SI surface association; height/datum inherited from selected stack'),
]
