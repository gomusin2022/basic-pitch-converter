from dataclasses import dataclass, field
from typing import Optional, List
import pretty_midi

@dataclass
class GuitarNote:
    pitch: int
    start: float
    end: float
    velocity: int
    string_number: int = 1  # 탭악보를 위한 줄 번호
    string_group: int = -1
    is_slide: bool = False

@dataclass
class StrumGroup:
    id: int
    start: float
    notes: List[GuitarNote] = field(default_factory=list)

@dataclass
class GuitarTrack:
    notes: List[GuitarNote]
    instrument: pretty_midi.Instrument