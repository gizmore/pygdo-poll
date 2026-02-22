from gdo.core.GDT_Enum import GDT_Enum

class GDT_PollType(GDT_Enum):

    def __init__(self, name: str):
        super().__init__(name)

    def gdo_choices(self) -> dict:
        return {
            'global': 'global_poll',
            'effective': 'effective_poll',
        }
