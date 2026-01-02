from typing import List
import math
from .types import GuitarNote, StrumGroup

def build_strum_groups(notes: List[GuitarNote], epsilon: float = 0.05) -> List[StrumGroup]:
    if not notes: return []
    notes.sort(key=lambda x: x.start)
    groups: List[StrumGroup] = []
    current_notes = [notes[0]]
    group_id = 0

    for i in range(1, len(notes)):
        if notes[i].start - current_notes[-1].start <= epsilon:
            current_notes.append(notes[i])
        else:
            current_notes.sort(key=lambda x: x.pitch)
            groups.append(StrumGroup(id=group_id, start=current_notes[0].start, notes=current_notes))
            group_id += 1
            current_notes = [notes[i]]
    
    current_notes.sort(key=lambda x: x.pitch)
    groups.append(StrumGroup(id=group_id, start=current_notes[0].start, notes=current_notes))
    return groups

def apply_strum_groups(notes: List[GuitarNote], epsilon: float = 0.05, grid: float = 0.0) -> List[GuitarNote]:
    groups = build_strum_groups(notes, epsilon=epsilon)
    
    for g in groups:
        # 피치가 낮은 음부터 6번줄, 5번줄... 순서로 할당
        # 실제 기타 연주와 유사하게 낮은 음이 낮은 번호 줄(6, 5, 4...)에 배치되도록 함
        g.notes.sort(key=lambda x: x.pitch)
        for i, n in enumerate(g.notes):
            # i=0(가장 낮은음) -> 6번줄, i=1 -> 5번줄 ... i=5 -> 1번줄
            n.string_number = max(1, 6 - i)
            n.string_group = g.id

    return notes