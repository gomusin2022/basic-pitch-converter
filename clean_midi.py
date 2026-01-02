# clean_midi.py

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

# -----------------------------
# Merge notes
# -----------------------------
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

    quantize_midi(midi, quantize_division)
    merge_notes(midi, merge_gap)
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
    midi.write(output_midi_path)
