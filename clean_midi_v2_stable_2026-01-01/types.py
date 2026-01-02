from dataclasses import dataclass
from typing import List
import pretty_midi


@dataclass
class GuitarNote:
    pitch: int
    start: float
    end: float
    velocity: int
    string_group: int = -1  # 스트럼 그룹 ID
    is_slide: bool = False


@dataclass
class GuitarTrack:
    notes: List[GuitarNote]
    instrument: pretty_midi.Instrument
