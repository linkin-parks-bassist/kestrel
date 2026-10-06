#!/usr/bin/env python3
"""Check composed fixture/query results in memory; timings are not carrier evidence."""
from pathlib import Path
import argparse
import os
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rows", type=int, default=10000)
args = parser.parse_args()
if not 1 <= args.rows <= 1000000:
    parser.error("--rows must be between 1 and 1000000")
root = Path(__file__).resolve().parent
amalgamation = Path(os.environ["SQLITE_AMALGAMATION_DIR"])
with tempfile.TemporaryDirectory(prefix="kestrel-sqlite-composed-") as directory:
    work = Path(directory)
    (work / "freertos").mkdir()
    (work / "freertos/FreeRTOS.h").write_text("")
    (work / "freertos/task.h").write_text("static inline void vTaskDelay(int ticks) {(void)ticks;}\n")
    (work / "esp_timer.h").write_text("#include <stdint.h>\nint64_t esp_timer_get_time(void);\n")
    (work / "main.c").write_text(r'''
#include <sqlite3.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
int probe_composed(sqlite3 **);
int probe_sd_publish(sqlite3 **db) {(void)db;return SQLITE_OK;}
int probe_sd_reopen(sqlite3 **db) {(void)db;return SQLITE_OK;}
void probe_read_reset(void) {}
void probe_read_report(int test,int strategy,int repeat) {(void)test;(void)strategy;(void)repeat;}
int64_t esp_timer_get_time(void) {
    struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return (int64_t)t.tv_sec*1000000+t.tv_nsec/1000;
}
int main(void) {
    sqlite3 *db=NULL;
    assert(sqlite3_open(":memory:",&db)==SQLITE_OK);
    assert(probe_composed(&db)==SQLITE_OK);
    assert(sqlite3_close(db)==SQLITE_OK);
    return 0;
}
''')
    subprocess.run(["cc", "-std=c11", "-D_POSIX_C_SOURCE=200809L", "-O0",
                    "-DSQLITE_THREADSAFE=0", "-DSQLITE_OMIT_LOAD_EXTENSION",
                    f"-DKT_PROBE_ROWS={args.rows}",
                    "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter", "-I", str(work),
                    "-I", str(amalgamation),
                    str(root / "main/composed.c"), str(work / "main.c"),
                    str(amalgamation / "sqlite3.c"), "-lm", "-o", str(work / "check")], check=True)
    result = subprocess.run([str(work / "check")], stdout=subprocess.PIPE, text=True)
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    identity = ("case", "strategy", "visit", "after", "rows")
    phases = ("build_us", "prepare_us", "bind_us", "step_us", "reset_us", "finalize_us")
    navigation, pages = [], []
    for line in result.stdout.splitlines():
        if not line.startswith(("NAV ", "PAGE ")):
            continue
        fields = {key: int(value) for key, value in
                  (field.split("=", 1) for field in line.split()[1:])}
        key = tuple(fields[field] for field in identity)
        if line.startswith("NAV "):
            navigation.append(key)
        else:
            if any(fields[phase] < 0 for phase in phases) or \
                    fields["query_us"] != sum(fields[phase] for phase in phases):
                raise SystemExit(f"Invalid page timing breakdown: {line}")
            pages.append(key)
    if not pages or navigation != pages:
        raise SystemExit("Navigation results and complete page timings do not match")
    print(f"HOST pages={len(pages)} timing breakdowns verified")
