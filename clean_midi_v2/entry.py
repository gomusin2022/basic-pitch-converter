from typing import List
from .types import GuitarNote
from .extract import extract_guitar_tracks
from .strum import apply_strum_groups
from .slide import apply_slides
from .write import write_midi_dual_track

def clean_midi_v2(midi_obj, output_path: str):
    # 1. 트랙 추출 및 정제
    tracks = extract_guitar_tracks(midi_obj)
    if not tracks:
        return False

    all_notes: List[GuitarNote] = []
    for t in tracks:
        all_notes.extend(t.notes)

    # 2. 스트럼 그룹화 및 퀀타이즈 (grid=0은 퀀타이즈 안 함)
    all_notes = apply_strum_groups(all_notes, epsilon=0.05, grid=0.0)

    # 3. 슬라이드 감지
    all_notes = apply_slides(all_notes)

    # 4. 최종 MIDI 쓰기 (기타/베이스 분리)
    write_midi_dual_track(all_notes, output_path)
    return True