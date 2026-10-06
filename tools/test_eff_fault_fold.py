#!/usr/bin/env python3
"""Compare the shipped fold stages with an independent saturating triangle reference."""
import argparse
from pathlib import Path

from dsp_model import read_pcm
from effect_library import ROOT, verify_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threshold', type=float, action='append', choices=(0.05, 0.22, 0.5))
    parser.add_argument('--output', type=Path, default=Path('/tmp/kestrel-fault-fold'))
    args = parser.parse_args()
    directory = args.output
    directory.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'effects/experimental/FAULT.EFF').read_text()
    code = source.split('.CODE\n', 1)[1].splitlines()
    start = code.index('add c4 [fold] c5')
    stop = code.index('delay_write c4 $first')
    probe = directory / 'FOLD.EFF'
    probe.write_text('v1.0\n.INFO\nname: "Fold probe"\n.PARAMETERS\n'
                     'fold: (name: "Fold", default: 0.22, min: 0.05, max: 0.5)\n'
                     '.CODE\nmov c0 c4\n' + '\n'.join(code[start:stop]) + '\nmov c4 c0\n')
    dry = list(range(-32768, 32768))
    def clamp(x):
        return max(-32768, min(32767, x))
    def fold(x, threshold):
        high = min(32767, abs(clamp(x + threshold)))
        low = min(32767, abs(clamp(x - threshold)))
        return clamp(clamp(high - low) - x)
    for value in args.threshold or (0.05, 0.22, 0.5):
        case = directory / ('default' if value == 0.22 else str(value))
        record = verify_case(probe, {'fold': value}, case, dry)
        wet = list(read_pcm(case / 'rtl.pcm'))
        threshold = round(value * 32768)
        expected = [fold(fold(x, threshold), threshold) for x in dry]
        error = max(abs(x-y) for x,y in zip(wet, expected))
        print(f'{value}: {record["samples"]} model/RTL matches; maximum independent fold error {error}', flush=True)
        assert error <= 4, (error, [(dry[i], wet[i], expected[i]) for i in range(len(dry))
                                  if abs(wet[i]-expected[i]) > 4][:8])


if __name__ == '__main__':
    main()
