import pretty_midi
import numpy as np
from collections import Counter
import math

# -----------------------------
# Quantize
# -----------------------------
def quantize_midi(midi, division=16):
    tempo = midi.estimate_tempo()
    quarter = 60.0 / max(tempo, 30)
    grid = quarter / (division / 4)

    if grid <= 0 or math.isnan(grid):
        return

    for inst in midi.instruments:
        for note in inst.notes:
            if math.isnan(note.start) or math.isnan(note.end):
                continue

            note.start = round(note.start / grid) * grid
            note.end = round(note.end / grid) * grid

            if note.end <= note.start:
                note.end = note.start + grid

def quantize_with_strum(midi, division=16, strum_epsilon=0.03):
    tempo = midi.estimate_tempo()
    quarter = 60.0 / max(tempo, 30)
    grid = quarter / (division / 4)

    if grid <= 0 or math.isnan(grid):
        return

    for inst in midi.instruments:
        if inst.is_drum:
            continue

        # start 기준 정렬
        notes = sorted(inst.notes, key=lambda n: n.start)
        if not notes:
            continue

        groups = []
        current_group = [notes[0]]

        for note in notes[1:]:
            if abs(note.start - current_group[-1].start) <= strum_epsilon:
                current_group.append(note)
            else:
                groups.append(current_group)
                current_group = [note]

        groups.append(current_group)

        # 그룹 단위 quantize
        for group in groups:
            avg_start = mean(n.start for n in group)
            q_start = round(avg_start / grid) * grid

            # 스트럼 느낌 유지 (순서 기반 미세 오프셋)
            for i, note in enumerate(sorted(group, key=lambda n: n.pitch)):
                offset = i * 0.005  # 5ms 간격
                note.start = q_start + offset
                note.end = max(note.end, note.start + 0.03)

# -----------------------------
# Merge notes
# -----------------------------
def merge_notes_v2(
    midi,
    gap=0.05,
    slide_overlap=0.03,
    slide_semitones=2,
):
    """
    기타 연주용 노트 병합
    - 같은 pitch + 짧은 gap → 병합
    - overlap 은 병합하지 않고 유지 (슬라이드)
    - pitch 차가 작고 overlap 있으면 슬라이드로 간주
    """
    for inst in midi.instruments:
        inst.notes.sort(key=lambda n: (n.start, n.pitch))
        merged = []

        for note in inst.notes:
            if not merged:
                merged.append(note)
                continue

            prev = merged[-1]

            gap_time = note.start - prev.end
            pitch_diff = abs(note.pitch - prev.pitch)

            # 1️⃣ 같은 pitch + 짧은 gap → 병합
            if (
                note.pitch == prev.pitch
                and 0 <= gap_time <= gap
            ):
                prev.end = max(prev.end, note.end)
                continue

            # 2️⃣ 슬라이드 허용 조건
            if (
                gap_time < 0  # overlap
                and abs(gap_time) <= slide_overlap
                and pitch_diff <= slide_semitones
            ):
                # 병합 ❌ → 슬라이드 유지
                merged.append(note)
                continue

            # 3️⃣ 기본: 병합 안 함
            merged.append(note)

        inst.notes = merged

def merge_notes(midi, gap=0.05):
    for inst in midi.instruments:
        inst.notes.sort(key=lambda n: (n.pitch, n.start))
        merged = []

        for note in inst.notes:
            if not merged:
                merged.append(note)
                continue

            prev = merged[-1]
            if note.pitch == prev.pitch and note.start - prev.end <= gap:
                prev.end = max(prev.end, note.end)
            else:
                merged.append(note)

        inst.notes = merged

# -----------------------------
# Remove short notes
# -----------------------------
def remove_short_notes(midi, min_length=0.04):
    for inst in midi.instruments:
        inst.notes = [
            n for n in inst.notes
            if (n.end - n.start) >= min_length
        ]

# -----------------------------
# Sanitize
# -----------------------------
def sanitize_midi(midi):
    for inst in midi.instruments:
        inst.notes = [
            n for n in inst.notes
            if (
                n.start is not None
                and n.end is not None
                and not math.isnan(n.start)
                and not math.isnan(n.end)
                and n.end > n.start
            )
        ]
def muse_score_safe_mode(midi):
    for inst in midi.instruments:
        inst.notes.sort(key=lambda n: (n.start, n.pitch))
        inst.is_drum = False

    midi.time_signature_changes = midi.time_signature_changes[:1]
    midi.key_signature_changes = midi.key_signature_changes[:1]

    midi._tick_scales = [(0, 1.0)]

    # tick scale 안전 처리
    if hasattr(midi, "_tick_scales"):
        midi._tick_scales = [
            ts for ts in midi._tick_scales
            if ts[0] is not None and not math.isnan(ts[0])
        ]

# -----------------------------
# Key estimation
# -----------------------------
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
     2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
     2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)

def estimate_key(midi):
    energy = np.zeros(12)
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            energy[n.pitch % 12] += (n.end - n.start)

    if energy.sum() == 0:
        return "C", "major"

    energy /= energy.sum()
    best, key, mode = -np.inf, 0, "major"

    for i in range(12):
        for profile, m in [(MAJOR_PROFILE, "major"), (MINOR_PROFILE, "minor")]:
            score = np.corrcoef(np.roll(profile, i), energy)[0, 1]
            if score > best:
                best, key, mode = score, i, m

    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    return names[key], mode

# -----------------------------
# Time Signature estimation
# -----------------------------
def estimate_time_signature(midi):
    onsets = sorted(
        n.start for inst in midi.instruments if not inst.is_drum for n in inst.notes
    )

    if len(onsets) < 10:
        return 4, 4

    intervals = np.diff(onsets)
    intervals = intervals[intervals > 0.05]

    if len(intervals) == 0:
        return 4, 4

    beat = Counter(np.round(intervals, 2)).most_common(1)[0][0]
    bars = np.round(intervals / beat).astype(int)
    bars = bars[(bars >= 2) & (bars <= 12)]

    if len(bars) == 0:
        return 4, 4

    b = Counter(bars).most_common(1)[0][0]
    if b == 3:
        return 3, 4
    if b == 6:
        return 6, 8
    return 4, 4

# -----------------------------
# Main
# -----------------------------
def clean_midi(
    input_midi_path,
    output_midi_path,
    quantize_division=16,
    min_note_length=0.04,
    merge_gap=0.05,
):
    midi = pretty_midi.PrettyMIDI(input_midi_path)

    quantize_with_strum(
    midi,
    quantize_division,
    strum_epsilon=0.03
    )
    merge_notes_v2(
    midi,
    gap=merge_gap,
    slide_overlap=0.03,
    slide_semitones=2,
    )

    remove_short_notes(midi, min_note_length)

    key, mode = estimate_key(midi)
    num, den = estimate_time_signature(midi)

    midi.key_signature_changes = [
        pretty_midi.KeySignature(
            pretty_midi.key_name_to_key_number(f"{key} {mode}"), 0.0
        )
    ]
    midi.time_signature_changes = [
        pretty_midi.TimeSignature(num, den, 0.0)
    ]

    sanitize_midi(midi)
    muse_score_safe_mode(midi)

def musescore_safe_mode(midi):
    # 1. 모든 Control Change 제거
    for inst in midi.instruments:
        inst.control_changes = []

    # 2. pitch bend 제거 (MuseScore crash 원인 1순위)
    for inst in midi.instruments:
        inst.pitch_bends = []

    # 3. 프로그램 체인지 정리
    for inst in midi.instruments:
        inst.program = max(0, min(inst.program, 127))

    # 4. tempo NaN 방지
    try:
        tempo = midi.estimate_tempo()
        if math.isnan(tempo) or tempo <= 0:
            midi._tempo_changes = ([0.0], [120.0])
    except:
        midi._tempo_changes = ([0.0], [120.0])

    print("🛡 MuseScore safe mode...")
    musescore_safe_mode(midi)

    midi.write(output_midi_path)

def clean_midi_v2(
    input_midi_path: str,
    output_midi_path: str,
    quantize_division: int = 16,
    min_note_length: float = 0.04,
    merge_gap: float = 0.05,
):
    # 내부에서 기존 clean_midi_v1 로직 or v2 로직 수행
    ...
