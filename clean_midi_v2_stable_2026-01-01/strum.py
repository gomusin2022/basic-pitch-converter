from typing import List
import math

from .types import GuitarNote, StrumGroup


def build_strum_groups(
    notes: List[GuitarNote],
    epsilon: float = 0.03
) -> List[StrumGroup]:
    """
    시작 시간이 epsilon 이내인 노트들을 스트럼 그룹으로 묶음
    """
    if not notes:
        return []

    groups: List[StrumGroup] = []

    current = [notes[0]]

    for n in notes[1:]:
        if abs(n.start - current[0].start) <= epsilon:
            current.append(n)
        else:
            groups.append(StrumGroup(notes=current))
            current = [n]

    groups.append(StrumGroup(notes=current))
    return groups


def quantize_strum_groups(
    groups: List[StrumGroup],
    grid: float
) -> None:
    """
    스트럼 그룹 단위로만 quantize
    """
    if grid <= 0 or math.isnan(grid):
        return

    for g in groups:
        base = g.notes[0].start
        q_base = round(base / grid) * grid
        offset = q_base - base

        for n in g.notes:
            n.start += offset
            n.end += offset
