import pretty_midi
from typing import List

from .types import GuitarNote, GuitarTrack

def extract_guitar_tracks(midi: pretty_midi.PrettyMIDI) -> List[GuitarTrack]:
    tracks: List[GuitarTrack] = []

    for inst in midi.instruments:
        if inst.is_drum:
            continue

        notes: List[GuitarNote] = []
        seen_notes = set()

        for n in inst.notes:
            if n.end <= n.start:
                continue
            
            # 중복 방지 로직
            note_key = (round(n.start, 3), n.pitch) 
            if note_key in seen_notes:
                continue
            seen_notes.add(note_key)

            notes.append(
                GuitarNote(
                    pitch=n.pitch,
                    start=n.start,
                    end=n.end,
                    velocity=n.velocity,
                )
            )

        if not notes:
            continue

        notes.sort(key=lambda x: x.start)

        tracks.append(
            GuitarTrack(
                notes=notes,
                instrument=inst
            )
        )

    return tracks