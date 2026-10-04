#!/usr/bin/env python3
"""Check bass body and audible ring sidebands through compiled, real RTL."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm
from effect_library import RATE, ROOT, prepare, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-bass-levels'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    prepare()
    records = []
    for name in ('BASSRING', 'WAH', 'VOWEL', 'FLANGE'):
        if name == 'BASSRING':
            dry = [round(8000 * math.sin(2 * math.pi * 73 * n / RATE))
                   for n in range(2 * RATE)]
        else:
            dry = [round(sum(a * math.sin(2 * math.pi * f * n / RATE)
                             for a, f in ((4000, 55), (2000, 110),
                                          (1000, 220), (500, 440))))
                   for n in range(2 * RATE)]
        directory = args.output / name
        record = verify_case(ROOT / 'effects' / (name + '.EFF'), {}, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        gain = 10 * math.log10(sum(x*x for x in wet[RATE:]) /
                              sum(x*x for x in dry[RATE:]))
        # David prefers the quieter, DC-normalized watery flanger. Record its
        # level without making loudness compensation an acceptance requirement.
        if name != 'FLANGE':
            assert -3 < gain < 3, (name, gain)
        assert max(map(abs, wet)) < 32000, name
        record['bass_rms_gain_db'] = gain
        if name == 'VOWEL':
            energy = sum(x*x for x in dry[RATE:])
            change = math.sqrt(sum((a-b)**2 for a, b in zip(wet[RATE:], dry[RATE:])) / energy)
            assert change > 0.35, change
            record['relative_rms_change'] = change
            mouths = []
            for mouth in (0, 1):
                sweep_directory = args.output / f'VOWEL-{mouth}'
                sweep_record = verify_case(ROOT / 'effects/VOWEL.EFF', {'mouth': mouth},
                                           sweep_directory, dry)
                mouths.append(read_pcm(sweep_directory / 'rtl.pcm'))
                records.append(sweep_record)
            motion = math.sqrt(sum((a-b)**2 for a, b in zip(mouths[0][RATE:], mouths[1][RATE:])) / energy)
            assert motion > 0.5, motion
            record['mouth_relative_rms_change'] = motion
        if name == 'BASSRING':
            carrier = round(55 * 32768 / RATE) * RATE / 32768
            sidebands = []
            for frequency in (73 - carrier, 73 + carrier):
                re = sum(x * math.cos(2 * math.pi * frequency * n / RATE)
                         for n, x in enumerate(wet[RATE:], RATE))
                im = sum(x * math.sin(2 * math.pi * frequency * n / RATE)
                         for n, x in enumerate(wet[RATE:], RATE))
                amplitude = 2 * math.hypot(re, im) / RATE
                assert amplitude > 4000, (frequency, amplitude)
                sidebands.append(amplitude)
            record['sideband_amplitudes'] = sidebands
        records.append(record)
        print(f'{name}: {gain:+.3f} dB, {len(dry)} exact outputs', flush=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
