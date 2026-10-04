#!/usr/bin/env python3
"""Compile, model and render the current-image effect library against real RTL."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

from dsp_model import DSP, read_pcm, read_program, write_pcm

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
CASES = {
    'FLANGE': {'rate': (0.1, 3), 'depth': (0.2, 8), 'feedback': (0, 0.85), 'mix': (0, 1)},
    'BASSRING': {'frequency': (20, 220), 'mix': (0, 1)},
    'GROWL': {'drive': (0, 18), 'motion': (0, 1), 'mix': (0, 1)},
    'WAH': {'cutoff': (300, 2500), 'Q': (0.7, 3)},
    'VOWEL': {'mouth': (0, 1), 'Q': (1, 3)},
    'OCTFUZZ': {'drive': (0, 24), 'tone': (500, 3500), 'level': (-24, 0)},
    'DRIVE': {'drive': (0, 18), 'tone': (500, 3500), 'level': (-24, 0)},
    'LEVEL': {'level': (-24, 0)},
    'INVPHASE': {'level': (-24, 0)},
    'CLIP': {'drive': (0, 24), 'ceiling': (0.1, 1)},
    'CUBEDRV': {'drive': (0, 18), 'level': (-24, 0)},
    'OCTAVE': {'level': (-24, 0)},
    'SVFLP': {'cutoff': (30, 5000), 'Q': (0.5, 3)},
    'SVFHP': {'cutoff': (30, 5000), 'Q': (0.5, 2)},
    'SVFBP': {'cutoff': (30, 5000), 'Q': (0.5, 2)},
    'SVFNOTCH': {'cutoff': (30, 5000), 'Q': (0.5, 2)},
    'SVFLP4': {'cutoff': (50, 3500)},
    'SVFTONE': {'cutoff': (100, 3500), 'balance': (0, 1)},
}


def command(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def prepare():
    command(['make', '-C', ROOT / 'kestrel_interface', 'compile-eff'], stdout=subprocess.DEVNULL)
    # Build once, then invoke the existing executable directly for the batch.
    command([ROOT / 'kestrel_core/verilator/test/dsp_core/run.sh'], stdout=subprocess.DEVNULL)


def probe(frames):
    edges = [0, 1, -1, 32767, -32768, 16384, -16384, 0] * 32
    return [edges[i] if i < 256 else
            (8192 if i == 512 else 0) if i < 1536 else
            4096 if i < 3584 else
            round(sum(2048 * math.sin(2 * math.pi * f * i / RATE)
                      for f in (100, 1000, 8000)))
            for i in range(frames)]


def wav(path, dry, wet):
    import array
    import sys
    samples = array.array('h', (v for pair in zip(dry, wet) for v in pair))
    if sys.byteorder != 'little':
        samples.byteswap()
    with wave.open(str(path), 'wb') as file:
        file.setparams((2, 2, RATE, len(dry), 'NONE', 'not compressed'))
        file.writeframes(samples.tobytes())


def tone_gain(values, frequency):
    # Ignore the step/impulse sections and the beginning of the tone segment.
    start = 8192
    real = sum(x * math.cos(2 * math.pi * frequency * i / RATE)
               for i, x in enumerate(values[start:], start))
    imag = sum(x * math.sin(2 * math.pi * frequency * i / RATE)
               for i, x in enumerate(values[start:], start))
    return 2 * math.hypot(real, imag) / ((len(values) - start) * 2048)


def verify_case(effect, params, directory, dry):
    effect, directory = effect.resolve(), directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    program, raw_input = directory / 'program.bin', directory / 'dry.pcm'
    command([ROOT / 'kestrel_interface/bin/lib/compile_eff', effect, program,
             *[f'{name}={value}' for name, value in params.items()]])
    instructions = read_program(program)
    model = DSP(instructions)
    expected = [model.sample(x) for x in dry]
    write_pcm(raw_input, dry)
    output = directory / 'rtl.pcm'
    result = command([ROOT / 'kestrel_core/verilator/test/dsp_core/obj_dir/Vcore_test',
                      '--render-program', program, raw_input, output], capture_output=True, text=True,
                     cwd=ROOT / 'kestrel_core')
    actual = read_pcm(output)
    if len(actual) != len(expected):
        raise AssertionError(f'{effect.name}: wrong output length')
    for i, (a, b) in enumerate(zip(actual, expected)):
        if a != b:
            raise AssertionError(f'{effect.name}: sample {i}: RTL {a}, model {b}')
    if effect.stem in ('LEVEL', 'INVPHASE') and params.get('level', 0) == 0:
        polarity = -1 if effect.stem == 'INVPHASE' else 1
        assert list(actual) == [max(-32768, min(32767, polarity * x)) for x in dry]
    if effect.stem == 'CLIP':
        assert max(abs(x) for x in actual) <= math.ceil(32768 * params.get('ceiling', 0.5))
    if effect.stem in ('GROWL', 'BASSRING', 'FLANGE') and params.get('mix') == 0:
        assert list(actual) == list(dry)
    wav(directory / 'dry-wet.wav', dry, actual)
    fields = result.stdout.strip().split(',')
    record = {'effect': effect.name, 'parameters': params, 'samples': len(dry),
              'descriptor_sha256': hashlib.sha256(effect.read_bytes()).hexdigest(),
              'program_sha256': hashlib.sha256(program.read_bytes()).hexdigest(),
              'exact_matches': len(dry), 'blocks': len(instructions),
              'max_cycles': int(fields[-1]), 'peak': max(abs(x) for x in actual)}
    if len(dry) > 8192:
        record['tone_gains'] = {str(f): tone_gain(actual, f) for f in (100, 1000, 8000)}
    (directory / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def check_response(name, record):
    gains = record.get('tone_gains', {})
    if not gains:
        return
    low, center, high = (gains[str(f)] for f in (100, 1000, 8000))
    if name in ('LEVEL', 'INVPHASE'):
        assert all(abs(g - 1) < 0.015 for g in (low, center, high)), record
    elif name in ('SVFLP', 'SVFLP4'):
        assert low > 0.9 and high < 0.05, record
    elif name == 'SVFHP':
        assert low < 0.04 and high > 0.75, record
    elif name == 'SVFBP':
        assert center > 0.8 and low < 0.2 and high < 0.3, record
    elif name == 'WAH':
        assert center > 0.8 and low < 0.1 and high < 0.1, record
    elif name == 'SVFNOTCH':
        assert center < 0.2 and low > 0.8 and high > 0.7, record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-effect-library'))
    parser.add_argument('--effect', choices=CASES, help='verify just this effect')
    parser.add_argument('--defaults-only', action='store_true')
    parser.add_argument('--input', type=Path, help='render a mono PCM16 WAV at 44100 Hz')
    parser.add_argument('--param', action='append', default=[], help='override NAME=VALUE; requires --effect')
    args = parser.parse_args()
    if args.input or args.param:
        if not args.effect:
            parser.error('--input/--param requires --effect')
        params = {}
        for item in args.param:
            name, sep, value = item.partition('=')
            if not sep or name not in CASES[args.effect]:
                parser.error(f'unknown parameter: {item}')
            value = float(value)
            low, high = CASES[args.effect][name]
            if not math.isfinite(value) or not low <= value <= high:
                parser.error(f'{name} must be between {low} and {high}')
            params[name] = value
        dry = probe(RATE)
        if args.input:
            with wave.open(str(args.input), 'rb') as file:
                if (file.getnchannels(), file.getsampwidth(), file.getframerate()) != (1, 2, RATE):
                    parser.error('input must be mono PCM16 at 44100 Hz')
                import array
                import sys
                dry = array.array('h')
                dry.frombytes(file.readframes(file.getnframes()))
                if sys.byteorder != 'little':
                    dry.byteswap()
        prepare()
        record = verify_case(ROOT / 'effects' / f'{args.effect}.EFF', params, args.output, dry)
        print(json.dumps(record, indent=2))
        return
    prepare()
    records = []
    for name in ([args.effect] if args.effect else CASES):
        effect = ROOT / 'effects' / f'{name}.EFF'
        record = verify_case(effect, {}, args.output / name / 'default', probe(RATE))
        check_response(name, record)
        records.append(record)
        print(f'{name}: {record["samples"]} exact default samples, {record["max_cycles"]} cycles/sample', flush=True)
        if not args.defaults_only:
            from itertools import product
            bounds = CASES[name]
            for i, values in enumerate(product(*bounds.values())):
                record = verify_case(effect, dict(zip(bounds, values)),
                                     args.output / name / f'corner-{i}', probe(8192))
                records.append(record)
            print(f'{name}: {i + 1} control corners exact', flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'results.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'{len(records)} verified programs; reports and dry-left/wet-right WAVs: {args.output}')


if __name__ == '__main__':
    main()
