# clean_midi_v2/split.py
from typing import List, Tuple
from .types import Note

BASS_MAX_PITCH = 52  # E3

def split_bass_melody(notes: List[Note]) -> Tuple[List[Note], List[Note]]:
    bass = []
    melody = []

    for n in notes:
        if n.pitch <= BASS_MAX_PITCH:
            bass.append(n)
        else:
            melody.append(n)

    return bass, melody
