from typing import List  # <--- 이 부분이 누락되어 에러가 났습니다.

from .types import GuitarNote

def detect_slides(
    notes: List[GuitarNote],
    max_gap: float = 0.08,
    max_pitch_diff: int = 4,
) -> None:
    if len(notes) < 2:
        return

    for i in range(len(notes) - 1):
        prev = notes[i]
        curr = notes[i+1]
        
        gap = curr.start - prev.end
        pitch_diff = abs(curr.pitch - prev.pitch)

        if 0 <= gap <= max_gap and 0 < pitch_diff <= max_pitch_diff:
            curr.is_slide = True
            # 레가토 연결: 음이 끊기지 않게 끝점 연장
            if prev.end < curr.start:
                prev.end = curr.start
            # 벨로시티 보정 (슬라이드 음은 부드럽게)
            curr.velocity = int(prev.velocity * 0.8)

def apply_slides(
    notes: List[GuitarNote],
    max_gap: float = 0.08,
    max_pitch_diff: int = 4,
) -> List[GuitarNote]:
    if not notes:
        return notes

    detect_slides(
        notes,
        max_gap=max_gap,
        max_pitch_diff=max_pitch_diff,
    )

    return notes