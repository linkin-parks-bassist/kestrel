#!/usr/bin/env python3
"""Check discovery queries against parser-retained .eff metadata on the host.

Replicas preserve authored tags and deliberately tie names. They are a scale
fixture, not a representative large library or evidence of carrier latency.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
AXES = ("keywords", "instruments", "types", "genres")


def metadata(compiler, path):
    reply = subprocess.run([str(compiler), "--info", str(path)], check=True,
                           capture_output=True, text=True).stdout
    return decode_metadata(reply, path)


def decode_metadata(reply, path):
    if "KEST eff-info result=0\n" not in reply:
        raise ValueError(f"Incomplete metadata: {path}")
    result, counts = {}, {}
    for field, count in re.findall(r"^KEST eff-info field=(\w+) count=(\d+)$", reply, re.M):
        result[field] = []
        counts[field] = int(count)
    for field, index, value in re.findall(
            r"^KEST eff-info field=(\w+) index=(\d+) hex=([0-9a-f]*)$", reply, re.M):
        value = bytes.fromhex(value).decode("utf-8")
        if field in AXES:
            if int(index) != len(result[field]):
                raise ValueError(f"Noncontiguous {field}: {path}")
            result[field].append(value)
        else:
            if int(index) != 0 or field in result:
                raise ValueError(f"Duplicate scalar {field}: {path}")
            result[field] = value
    if set(counts) != set(AXES) or any(len(result[k]) != counts[k] for k in AXES):
        raise ValueError(f"Invalid list counts: {path}")
    if not result.get("name") or not result.get("cname"):
        raise ValueError(f"Missing identity: {path}")
    return result


def metadata_only(reader, paths):
    marker = "KEST eff-info result=0\n"
    values = []
    # Keep process arguments bounded independently of the library size.
    for start in range(0, len(paths), 64):
        batch = paths[start:start + 64]
        reply = subprocess.run([str(reader), *map(str, batch)], check=True,
                               capture_output=True, text=True).stdout
        blocks = reply.split(marker)
        if len(blocks) != len(batch) + 1 or blocks[-1].strip():
            raise ValueError("Incomplete metadata-only batch")
        values.extend(decode_metadata(block + marker, path)
                      for block, path in zip(blocks, batch))
    return values


def sql_predicate(tree):
    op, *items = tree
    if op in ("all", "any"):
        if not items:
            return ("1" if op == "all" else "0"), []
        parts = [sql_predicate(item) for item in items]
        return "(" + (" AND " if op == "all" else " OR ").join(p[0] for p in parts) + ")", \
            [value for _, values in parts for value in values]
    if op == "not":
        sql, values = sql_predicate(items[0])
        return f"NOT ({sql})", values
    if op not in AXES:
        raise ValueError(op)
    return "EXISTS(SELECT 1 FROM facet f WHERE f.axis=? AND f.value=? AND f.effect_id=c.id)", \
        [op, items[0]]


def matches(tree, effect):
    op, *items = tree
    if op == "all":
        return all(matches(item, effect) for item in items)
    if op == "any":
        return any(matches(item, effect) for item in items)
    if op == "not":
        return not matches(items[0], effect)
    return items[0] in effect[op]


def required_facets(tree):
    """Only seed from memberships that every matching row must possess."""
    op, *items = tree
    if op in AXES:
        return {(op, items[0])}
    if op == "not":
        return set()
    sets = [required_facets(item) for item in items]
    if not sets:
        return set()
    return set.union(*sets) if op == "all" else set.intersection(*sets)


def branch_facets(tree):
    """Positive candidates for this bounded experiment, preserving OR branches."""
    op, *items = tree
    if op in AXES:
        return [{(op, items[0])}]
    if op == "not":
        return [set()]
    if not items:
        return [set()] if op == "all" else []
    children = [branch_facets(item) for item in items]
    if op == "any":
        return [branch for child in children for branch in child]
    size = 1
    for child in children:
        size *= len(child)
    if size > 32:
        raise ValueError("Experiment exceeds 32 candidate branches")
    return [set.union(*branches) for branches in product(*children)]


def check(effects, copies, page_size, extra_cases=None):
    db = sqlite3.connect(":memory:")
    try:
        db.executescript("""
            CREATE TABLE effect(id INTEGER PRIMARY KEY,name TEXT NOT NULL,description TEXT);
            CREATE INDEX effect_name ON effect(name,id);
            CREATE TABLE facet(axis TEXT,value TEXT,effect_id INTEGER,
                PRIMARY KEY(axis,value,effect_id)) WITHOUT ROWID;
            CREATE TABLE facet_page(axis TEXT,value TEXT,name TEXT,effect_id INTEGER,
                PRIMARY KEY(axis,value,name,effect_id)) WITHOUT ROWID;
        """)
        records = [effect for _ in range(copies) for effect in effects]
        with db:
            for id, effect in enumerate(records, 1):
                db.execute("INSERT INTO effect VALUES(?,?,?)",
                           (id, effect["name"], effect.get("description")))
                db.executemany("INSERT INTO facet VALUES(?,?,?)",
                               ((axis, value, id) for axis in AXES for value in sorted(set(effect[axis]))))
            db.execute("INSERT INTO facet_page SELECT axis,value,name,effect_id "
                       "FROM facet JOIN effect ON effect.id=facet.effect_id")
        counts = {(axis, value): count for axis, value, count in db.execute(
            "SELECT axis,value,count(*) FROM facet GROUP BY axis,value")}
        cases = {
            "bass": ("instruments", "bass"),
            "bass_delay_or_modulation": ("all", ("instruments", "bass"),
                                          ("any", ("types", "delay"), ("types", "modulation"))),
            "delay_and_modulation": ("all", ("types", "delay"), ("types", "modulation")),
            "ring_or_rectifier": ("any", ("keywords", "ring modulation"), ("keywords", "rectifier")),
            "grouped": ("any", ("all", ("types", "delay"), ("keywords", "feedback")),
                        ("all", ("types", "filter"), ("keywords", "manual sweep"))),
            "non_distortion": ("all", ("instruments", "bass"), ("not", ("types", "distortion"))),
            "unassigned_genre": ("genres", "ambient"),
            "literal_sql_text": ("keywords", "'); DROP TABLE effect; --"),
            "idempotent": ("any", ("types", "delay"), ("types", "delay")),
            "unsafe_union_seed": ("any", ("types", "delay"), ("types", "filter")),
            "empty_all": ("all",),
            "empty_any": ("any",),
            "empty_negation": ("not", ("any",)),
            "group_identity": ("all", ("instruments", "bass"), ("all",),
                               ("not", ("any",))),
        }
        cases.update(extra_cases or {})
        results = {}
        for label, tree in cases.items():
            predicate, bindings = sql_predicate(tree)
            expected = sorted(((id, e["name"]) for id, e in enumerate(records, 1) if matches(tree, e)),
                              key=lambda row: (row[1].encode("utf-8"), row[0]))
            required = required_facets(tree)
            seed = min(required, key=lambda x: (counts.get(x, 0), x)) if required else None
            source = "(SELECT effect_id AS id,name FROM facet_page WHERE axis=? AND value=?) c"
            strategies = {"ordered": [("effect c", [])]}
            if seed:
                strategies["covering"] = [(source, list(seed))]
            branches = branch_facets(tree)
            if all(branches):
                seeds = sorted({min(branch, key=lambda x: (counts.get(x, 0), x)) for branch in branches})
                if len(seeds) > 1:
                    strategies["covering_union"] = [(source, list(s)) for s in seeds]
            results[label] = {}
            for strategy, sources in strategies.items():
                seen, cursor, pages, max_us = [], None, 0, 0
                while True:
                    bounds = " AND (c.name,c.id)>(?,?)" if cursor else ""
                    start = time.perf_counter_ns()
                    sql, values = [], []
                    for source, seed_bindings in sources:
                        sql.append(f"SELECT c.id AS id,c.name AS name FROM {source} "
                                   f"WHERE {predicate}{bounds}")
                        values.extend(seed_bindings + bindings + (list(cursor) if cursor else []))
                    rows = db.execute(" UNION ".join(sql) + " ORDER BY name,id LIMIT ?",
                                      values + [page_size]).fetchall()
                    max_us = max(max_us, (time.perf_counter_ns() - start) // 1000)
                    if rows != expected[len(seen):len(seen) + page_size]:
                        raise AssertionError((label, strategy, pages, rows))
                    seen.extend(rows)
                    pages += 1
                    if len(rows) < page_size:
                        break
                    cursor = (rows[-1][1], rows[-1][0])
                assert seen == expected
                results[label][strategy] = {"matches": len(seen), "pages": pages,
                                            "max_host_page_us": max_us,
                                            "seeds": [values for _, values in sources if values]}
        assert db.execute("SELECT count(*) FROM effect").fetchone()[0] == len(records)
        return {"effects": len(records), "database_bytes": len(db.serialize()), "cases": results}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    readers = parser.add_mutually_exclusive_group()
    readers.add_argument("--compiler", type=Path, default=ROOT / "kestrel_interface/bin/lib/compile_eff")
    readers.add_argument("--info-reader", type=Path,
                         help="Experimental metadata-only reader; does not validate DSP code")
    parser.add_argument("--copies", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--effects-dir", type=Path,
                        help="Import .eff files directly from a directory without shell glob expansion")
    parser.add_argument("effects", type=Path, nargs="*")
    args = parser.parse_args()
    if args.copies < 1 or args.page_size < 1:
        parser.error("copies and page-size must be positive")
    if bool(args.effects) == bool(args.effects_dir):
        parser.error("provide effect files or --effects-dir, exclusively")
    if args.effects_dir:
        args.effects = sorted(p for p in args.effects_dir.iterdir()
                              if p.is_file() and p.suffix.lower() == ".eff")
        if not args.effects:
            parser.error("effects directory contains no .eff files")
    values = metadata_only(args.info_reader, args.effects) if args.info_reader else \
        [metadata(args.compiler, p) for p in args.effects]
    sources = [{"file": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "metadata": value} for p, value in zip(args.effects, values)]
    if len({s["metadata"]["cname"] for s in sources}) != len(sources):
        parser.error("duplicate effect identity")
    report = {"sqlite_version": sqlite3.sqlite_version, "copies": args.copies,
              "page_size": args.page_size, "sources": sources,
              "reader": {"mode": "info_only" if args.info_reader else "full_parser",
                         "file": str(args.info_reader or args.compiler),
                         "sha256": hashlib.sha256((args.info_reader or args.compiler).read_bytes()).hexdigest()},
              **check([s["metadata"] for s in sources], args.copies, args.page_size)}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
