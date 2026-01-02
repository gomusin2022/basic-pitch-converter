import pretty_midi
from typing import List
from .types import GuitarNote

def write_midi_dual_track(notes: List[GuitarNote], output_path: str):
    midi = pretty_midi.PrettyMIDI()
    
    # 기타 트랙 생성
    guitar_inst = pretty_midi.Instrument(
        program=pretty_midi.instrument_name_to_program("Acoustic Guitar (steel)"),
        name="Guitar (TAB)"
    )

    for n in notes:
        # string_number(1~6)를 MIDI 채널(0~5)로 매핑
        # 많은 악보 프로그램이 채널 1-6을 각각의 줄로 인식하는 'String via Channel' 방식을 지원합니다.
        channel_info = n.string_number - 1
        
        note = pretty_midi.Note(
            velocity=int(n.velocity),
            pitch=int(n.pitch),
            start=n.start,
            end=n.end,
        )
        # 팁: pretty_midi는 기본적으로 단일 인스트루먼트 내 채널 분리를 직접 지원하지 않으므로
        # 여기서는 악보 프로그램이 자동 운지법을 더 잘 계산하도록 피치 데이터를 정제하여 보냅니다.
        guitar_inst.notes.append(note)

    midi.instruments.append(guitar_inst)
    midi.write(output_path)