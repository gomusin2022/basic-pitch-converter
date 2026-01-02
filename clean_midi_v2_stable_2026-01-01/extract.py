import pretty_midi
from typing import List

from .types import GuitarNote, GuitarTrack


def extract_guitar_tracks(midi: pretty_midi.PrettyMIDI) -> List[GuitarTrack]:
    """
    MIDI에서 기타용 노트 추출
    - 드럼 제외
    - 시작시간 기준 정렬
    """

    tracks: List[GuitarTrack] = []

    for inst in midi.instruments:
        if inst.is_drum:
            continue

        notes: List[GuitarNote] = []

        for n in inst.notes:
            if n.end <= n.start:
                continue

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

        # 시작시간 기준 정렬
        notes.sort(key=lambda x: x.start)

        tracks.append(
            GuitarTrack(
                notes=notes,
                instrument=inst
            )
        )

    return tracks
