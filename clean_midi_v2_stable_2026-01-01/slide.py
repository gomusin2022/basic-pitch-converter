from typing import List

from .types import GuitarNote


def merge_slides(
    notes: List[GuitarNote],
    max_pitch_diff: int = 2,
    max_gap: float = 0.04
) -> List[GuitarNote]:
    """
    슬라이드로 판단되는 연속 노트 병합
    """
    if not notes:
        return []

    notes = sorted(notes, key=lambda n: (n.start, n.pitch))
    merged: List[GuitarNote] = [notes[0]]

    for n in notes[1:]:
        prev = merged[-1]

        pitch_diff = abs(n.pitch - prev.pitch)
        gap = n.start - prev.end

        if pitch_diff <= max_pitch_diff and gap <= max_gap:
            # 슬라이드 → 하나의 노트처럼 연결
            prev.end = max(prev.end, n.end)
            prev.pitch = n.pitch  # 최종 pitch 기준
        else:
            merged.append(n)

    return merged
