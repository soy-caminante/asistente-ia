from    dataclasses                 import  dataclass
from    tools.factories             import  *
#--------------------------------------------------------------------------------------------------

@dataclass
class ColorPalette:
    theme:str   = "#54BAAD"
    grey:str    = ft.Colors.GREY_300
#--------------------------------------------------------------------------------------------------

class Factories:
    tf: TextFactory     = None
    bf: ButtonFactory   = None
    lf: LogoFactory     = None
    cp: ColorPalette    = None
    #----------------------------------------------------------------------------------------------

    @classmethod
    def setup(cls, tf, bf, lf, cp):
        cls.tf      = tf
        cls.bf      = bf
        cls.lf      = lf
        cls.cp      = ColorPalette()
    #----------------------------------------------------------------------------------------------

    def __init__(self):
        pass
    #----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
