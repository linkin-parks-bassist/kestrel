#!/usr/bin/env python3
"""Exercise discovery with generated skew, mixed instruments and rare matches.

Authored metadata supplies templates; generated entries are not a real library.
Host timing does not establish carrier/SD/UI performance.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sqlite3

from library_check import AXES, ROOT, check, metadata


def fixture(templates, rows, seed):
    rng = random.Random(seed)
    instruments = ['bass', 'guitar', 'voice', 'synth', 'drums']
    genres = ['ambient', 'noise', 'jazz', 'rock', 'metal']
    records = []
    for i in range(rows):
        base = rng.choice(templates)
        effect = {**base, 'keywords': list(base['keywords'])}
        effect['cname'] = f'generated_{i}'
        # Repeated names, punctuation and non-ASCII ordering are intentional.
        prefix = rng.choice(['Echo', 'Écho', '夜', "' quoted"]) if i % 19 == 0 else base['name']
        effect['name'] = f'{prefix} {i % 31:02d}'
        effect['instruments'] = [] if rng.random() < .1 else rng.choices(
            instruments, weights=[60, 25, 8, 5, 2], k=1 + (rng.random() < .2))
        effect['genres'] = [] if rng.random() < .2 else rng.choices(
            genres, weights=[65, 15, 10, 5, 5], k=1 + (rng.random() < .3))
        if i % 997 == 0:
            effect['keywords'].append('rare anchor')
        if i % 211 == 0:
            effect['keywords'].append("'); DROP TABLE effect; --")
        if i % 173 == 0:
            effect['keywords'].extend(['FEEDBACK', 'feedback', 'feedback'])
        if i % 64 == 0:
            effect['description'] = base.get('description', '') + (' Detail.' * 256)
        if i == rows - 1:
            effect['name'] = 'zzzz final match'
            effect['keywords'].append('late only')
        records.append(effect)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', type=Path, default=ROOT / 'kestrel_interface/bin/lib/compile_eff')
    parser.add_argument('--rows', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=31)
    parser.add_argument('--page-size', type=int, default=50)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('effects', type=Path, nargs='+')
    args = parser.parse_args()
    if args.rows < 1 or args.page_size < 1:
        parser.error('rows and page-size must be positive')
    sources = [{'file': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                'metadata': metadata(args.compiler, p)} for p in args.effects]
    records = fixture([s['metadata'] for s in sources], args.rows, args.seed)
    cases = {
        'mixed_instruments': ('any', ('instruments', 'bass'), ('instruments', 'guitar')),
        'ambient_delay': ('all', ('genres', 'ambient'), ('types', 'delay')),
        'rare_non_distortion': ('all', ('keywords', 'rare anchor'), ('not', ('types', 'distortion'))),
        'pure_negation': ('not', ('instruments', 'bass')),
        'unrestricted_union': ('any', ('keywords', 'late only'), ('not', ('types', 'filter'))),
        'negated_group': ('not', ('any', ('types', 'filter'), ('genres', 'ambient'))),
        'late_only': ('keywords', 'late only'),
        'case_sensitive': ('keywords', 'FEEDBACK'),
    }
    report = {'fixture': 'generated mixed/skewed metadata, not an authored library',
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'query_checker_sha256': hashlib.sha256(Path(__file__).with_name('library_check.py').read_bytes()).hexdigest(),
              'sqlite_version': sqlite3.sqlite_version, 'seed': args.seed,
              'page_size': args.page_size, 'sources': sources,
              'facet_counts': {axis: dict(sorted(Counter(
                  value for effect in records for value in set(effect[axis])).items())) for axis in AXES},
              **check(records, 1, args.page_size, cases)}
    assert report['cases']['late_only']['ordered']['matches'] == 1
    assert report['cases']['literal_sql_text']['ordered']['matches'] > 0
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{args.rows} generated entries; {len(report["cases"])} predicates; '
          f'{sum(s["pages"] for c in report["cases"].values() for s in c.values())} checked pages')


if __name__ == '__main__':
    main()
