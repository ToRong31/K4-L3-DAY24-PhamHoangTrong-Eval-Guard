"""Submission checker. Reads saved evidence; no API calls; pytest is opt-in."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import ROOT_DIR
from src.experiment_support import read_json
from src.report_contracts import (require, validate_answers, validate_markdown, validate_metadata, validate_team,
                                  validate_phase_a, validate_phase_b, validate_phase_c)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(ROOT_DIR))
    parser.add_argument("--with-tests", action="store_true",
                        help="Run offline pytest once; default only checks saved artifacts")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    failures = []
    def check(name, callback):
        try:
            callback()
        except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
            failures.append(name)
            print(f"FAIL {name}: {error}")
        else:
            print(f"PASS {name}")
    for name in ("README.md", "doc/ASSIGNMENT.md", "doc/SUBMISSION.md", "doc/CHECKPOINTS.md",
                 "doc/RULES.md", "doc/RUBRIC.md", "doc/ENVIRONMENT.md",
                 "doc/PIPELINE_INTERFACE.md", "doc/REPORT_SCHEMAS.md"):
        check(name, lambda name=name: require((root / name).is_file(), "Missing document."))
    check("doc/TEAM.md", lambda: validate_team(root / "doc/TEAM.md"))
    for name in ("doc/reports/failure_clusters.md",
                 "doc/reports/bias_report.md", "doc/reports/blueprint.md"):
        check(name, lambda name=name: validate_markdown(root / name))
    for name in ("m1_chunking.py", "m2_search.py", "m3_rerank.py", "m4_eval.py", "m5_enrichment.py"):
        check(name, lambda name=name: require((root / "src" / name).is_file(),
                                              "Missing pipeline module; see PIPELINE_INTERFACE.md."))
    for name in ("phase_a_ragas.py", "phase_b_judge.py", "phase_c_guard.py"):
        def complete(name=name):
            code = (root / "src" / name).read_text(encoding="utf-8")
            require("# TODO" not in code, "Unfinished student TODOs.")
        check(name, complete)

    paths = {name: root / ("artifacts" if name == "answers_50q.json" else "fixtures") / name
             for name in ("test_set_50q.json", "answers_50q.json",
             "human_labels_10q.json", "adversarial_set_20.json", "clean_set_8.json", "output_set_4.json")}
    schema_dir = root / "doc/schemas"
    def answers_check():
        validate_answers(read_json(paths["answers_50q.json"]), read_json(paths["test_set_50q.json"]),
                         schema_dir=schema_dir)
    check("answers_50q.json", answers_check)
    def phase_a():
        report = read_json(root / "artifacts/ragas_50q.json")
        validate_phase_a(report, read_json(paths["answers_50q.json"]), schema_dir=schema_dir)
        validate_metadata(report, [paths["answers_50q.json"], paths["test_set_50q.json"]])
    def phase_b():
        report = read_json(root / "artifacts/judge_results.json")
        validate_phase_b(report, read_json(paths["answers_50q.json"]),
                         read_json(paths["test_set_50q.json"]), read_json(paths["human_labels_10q.json"]),
                         schema_dir=schema_dir)
        validate_metadata(report, [paths[n] for n in
                          ("answers_50q.json", "test_set_50q.json", "human_labels_10q.json")])
    def phase_c():
        report = read_json(root / "artifacts/guard_results.json")
        validate_phase_c(report, read_json(paths["adversarial_set_20.json"]),
                         read_json(paths["clean_set_8.json"]), read_json(paths["output_set_4.json"]),
                         schema_dir=schema_dir)
        validate_metadata(report, [paths[n] for n in
                          ("adversarial_set_20.json", "clean_set_8.json", "output_set_4.json")])
    for name, callback in (("Phase A artifact", phase_a), ("Phase B artifact", phase_b),
                           ("Phase C artifact", phase_c)):
        check(name, callback)
    if args.with_tests:
        def tests():
            result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-m", "not integration",
                                     "-q", "--tb=short"], cwd=root)
            require(result.returncode == 0, "Offline student/support tests failed.")
        check("offline pytest", tests)
    print(f"{len(failures)} failed checks (not a rubric score).")
    return int(bool(failures))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
