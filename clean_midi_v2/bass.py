from .extract import extract_notes
from .strum import apply_strum
from .slide import apply_slide
from .bass import split_bass_and_guitar
from .write import write_midi


def clean_midi_v2(input_midi_path: str, output_midi_path: str):
    notes = extract_notes(input_midi_path)

    bass_notes, guitar_notes = split_bass_and_guitar(notes)

    # 🎸 기타만 스트럼 / 슬라이드
    guitar_notes = apply_strum(guitar_notes)
    guitar_notes = apply_slide(guitar_notes)

    # 🎸 기타 MIDI
    guitar_path = output_midi_path.replace(".mid", "_guitar.mid")
    write_midi(
        guitar_notes,
        guitar_path,
        program=pretty_midi.instrument_name_to_program("Acoustic Guitar (steel)")
    )

    # 🎸 베이스 MIDI
    bass_path = output_midi_path.replace(".mid", "_bass.mid")
    write_midi(
        bass_notes,
        bass_path,
        program=pretty_midi.instrument_name_to_program("Acoustic Bass")
    )
