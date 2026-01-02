import pretty_midi
import math
from typing import List

from .types import GuitarNote


def write_midi(
    notes: List[GuitarNote],
    output_path: str,
    program: int = pretty_midi.instrument_name_to_program(
        "Acoustic Guitar (steel)"
    ),
):
    """
    GuitarNote 리스트를 PrettyMIDI로 변환
    - 스트럼 / 슬라이드 결과 그대로 유지
    - MuseScore / TAB 안정성 보장
    """

    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=program)

    for n in notes:
        # ---- 시간 보정 ----
        start = float(n.start)
        end = float(n.end)

        if math.isnan(start) or math.isnan(end):
            continue

        # 음수 방지
        start = max(0.0, start)

        # 길이 보장 (짧으면 MuseScore가 음을 날림)
        if end <= start:
            end = start + 0.03
        else:
            end = max(end, start + 0.02)

        pitch = int(n.pitch)
        if pitch < 0 or pitch > 127:
            continue

        inst.notes.append(
            pretty_midi.Note(
                velocity=80,
                pitch=pitch,
                start=start,
                end=end,
            )
        )

    # -----------------------
    # 빈 MIDI 방지
    # (MuseScore / Guitar Pro crash 방지)
    # -----------------------
    if not inst.notes:
        inst.notes.append(
            pretty_midi.Note(
                velocity=1,
                pitch=60,
                start=0.0,
                end=0.05,
            )
        )

    midi.instruments.append(inst)

    # -----------------------
    # MuseScore Safe Mode
    # (NaN tick 제거)
    # -----------------------
    if hasattr(midi, "_tick_scales"):
        midi._tick_scales = [
            ts for ts in midi._tick_scales
            if ts
            and ts[0] is not None
            and not math.isnan(ts[0])
        ]

    midi.write(output_path)
