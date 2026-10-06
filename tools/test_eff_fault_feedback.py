#!/usr/bin/env python3
"""Check Fault Choir's signed feedback/tap recurrence in its linear fold region."""
from pathlib import Path

from dsp_model import read_pcm, read_program
from effect_library import ROOT, verify_case
from test_eff_fault import check_topology


def main():
    directory = Path('/tmp/kestrel-fault-feedback')
    dry = [0] * 40000
    dry[30000], dry[31000] = 8192, -4096
    params = {'feedback': 0.5, 'drive': 1, 'fold': 0.5, 'mix': 1, 'dry': 0}
    record = verify_case(ROOT / 'effects/experimental/FAULT.EFF', params, directory, dry)
    program = read_program(directory / 'program.bin')
    check_topology(program, params)
    qa, qb = program[5][1], program[6][1]
    taps = [750, 500]
    history, expected, dark = [], [], 0
    rounded = lambda value, coef: (value * coef + 16384) // 32768
    for n, sample in enumerate(dry):
        long = history[n-taps[0]] if n >= taps[0] else 0
        short = history[n-taps[1]] if n >= taps[1] else 0
        difference = rounded(long, 16384) + rounded(short, -16384)
        dark = rounded(dark, qa) + rounded(difference, qb)
        written = rounded(sample, 16384) + rounded(dark, 16384)
        assert abs(written) < 16384  # Both folds are identity within this region.
        history.append(written)
        expected.append(dark)
    actual = list(read_pcm(directory / 'rtl.pcm'))
    assert actual == expected
    assert not any(actual[:30500]) and actual[30500] < 0
    print(f'{record["samples"]} exact independent feedback outputs; {record["max_cycles"]} cycles/sample', flush=True)


if __name__ == '__main__':
    main()
