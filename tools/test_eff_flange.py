#!/usr/bin/env python3
"""Check complete slow sweeps and bass transients through the compiled flanger."""
import argparse
import json
import math
from pathlib import Path

from dsp_model import read_pcm
from effect_library import RATE, ROOT, prepare, verify_case


def check_comb(source, output):
    # Freeze a known 128-sample tap through the same feedback/output instructions.
    fixed = output / 'fixed-comb.eff'
    tail = source.read_text().split('\ndelay_mread')[1].split('\n', 1)[1]
    prefix = source.read_text().split('\n.CODE')[0].replace('delay_samples: 4', 'delay_samples: 128')
    fixed.write_text(prefix + '\n.CODE\ndelay_read $line c5\n' + tail)
    dry = [4096] * 8192 + [8192 if (n // 128) % 2 else -8192 for n in range(8192)]
    records = []
    for feedback in (0, 0.65, 0.85):
        directory = output / f'comb-{feedback}'
        record = verify_case(fixed, {'feedback': feedback, 'mix': 0.5}, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        gain = 1 / math.sqrt(((1-feedback)**2 + 1-feedback**2) / 4)
        # Descriptor-selected immediate precision introduces coefficient rounding.
        assert max(abs(x - 4096 * gain) for x in wet[6144:8192]) < 0.01 * 4096 * gain
        residual = max(abs(x) for x in wet[-4096:])
        # Rejection is relative to the compensated passband, not input level.
        assert residual < 8192 * gain / 100, (feedback, residual)
        record['dc_gain'] = gain
        record['notch_peak_codes'] = residual
        records.append(record)
        print(f'Comb feedback {feedback}: DC gain {gain:.3f}, notch peak {residual} codes', flush=True)
    return records


def check_wave(source, output):
    # Exercise the shipped polynomial against sine, not just a matching model.
    resource = next(line for line in source.read_text().splitlines()
                    if line.startswith('wave:'))
    effect = output / 'wave.eff'
    effect.write_text('v1.0\n.INFO\nname: "Flange Wave Test"\n.RESOURCES\n' +
                      resource + '\n.CODE\npoly c0 $wave c0\n')
    dry = list(range(-32768, 32768))
    directory = output / 'wave'
    record = verify_case(effect, {}, directory, dry)
    wet = read_pcm(directory / 'rtl.pcm')
    error = max(abs(y - 32768 * math.sin(math.pi * x / 32768))
                for x, y in zip(dry, wet))
    assert error < 64, error
    assert abs(wet[0]) <= 4 and abs(wet[-1]) <= 8, (wet[0], wet[-1])
    assert abs(wet[16384] + 32768) < 64 and abs(wet[49152] - 32767) < 64
    record['max_sine_error_codes'] = error
    print(f'Wave: all 65536 inputs exact, sine error {error:.3f} codes', flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-flange-audition'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    prepare()
    source = ROOT / 'effects/FLANGE.EFF'
    # Expose the descriptor's actual oscillator prefix through an ordinary final MOV.
    # This uses the production compiler; no oscillator opcode or model shortcut.
    oscillator = args.output / 'sweep.eff'
    oscillator.write_text(source.read_text().split('\ndelay_mread')[0] + '\nmov c4 c0\n')
    records = [check_wave(source, args.output)] + check_comb(source, args.output)
    for rate in (0.1, 0.3, 3):
        frames = math.ceil(2.6 * RATE / rate)
        directory = args.output / f'sweep-{rate}'
        record = verify_case(oscillator, {'rate': rate}, directory, [0] * frames)
        wet = read_pcm(directory / 'rtl.pcm')
        crossings = [i for i in range(1, len(wet)) if wet[i-1] <= 16384 < wet[i]]
        assert len(crossings) >= 3, (rate, crossings)
        measured = RATE * (len(crossings) - 1) / (crossings[-1] - crossings[0])
        assert abs(measured - rate) < 0.006, (rate, measured)
        assert min(wet) <= 1 and max(wet) >= 32766
        record['measured_sweep_hz'] = measured
        records.append(record)
        print(f'Sweep {rate} Hz: measured {measured:.6f}, {frames} exact samples', flush=True)

    # Repeated low-B, low-E and open-A plucks with harmonics and a decaying attack.
    dry = []
    for n in range(8 * RATE):
        note = (30.8677, 41.2034, 55)[(n // RATE) % 3]
        age = (n % RATE) / RATE
        dry.append(round(9000 * math.exp(-3 * age) * sum(
            math.sin(2 * math.pi * note * harmonic * age) / harmonic
            for harmonic in range(1, 7)) / 2))
    for params in ({}, {'mix': 0}, {'feedback': 0.85, 'depth': 8, 'rate': 3, 'mix': 1}):
        directory = args.output / f'bass-{len(records)}'
        record = verify_case(source, params, directory, dry)
        wet = read_pcm(directory / 'rtl.pcm')
        if params.get('mix') == 0:
            assert list(wet) == dry
        else:
            relative_change = math.sqrt(sum((a-b)**2 for a, b in zip(wet, dry)) /
                                        sum(a*a for a in dry))
            assert relative_change > 0.15, relative_change
            assert max(abs(x) for x in wet) < 32000
            record['relative_rms_change'] = relative_change
        records.append(record)
        print(f'Bass {params}: {len(dry)} exact samples, {record["max_cycles"]} cycles/sample', flush=True)
    record = verify_case(source, {}, args.output / 'silence', [0] * RATE)
    assert not any(read_pcm(args.output / 'silence/rtl.pcm'))
    records.append(record)
    (args.output / 'comparison.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
