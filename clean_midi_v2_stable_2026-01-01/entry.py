# slide 이후
bass_notes, melody_notes = split_bass_melody(notes)

write_midi(
    output_path,
    tracks={
        "Bass": bass_notes,
        "Melody": melody_notes
    }
)
