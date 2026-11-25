#!/usr/bin/env python3
"""Merge a content import batch into src/data/episodes.json.

Safe to re-run:
  * records are matched on YouTube video ID, so a Creole poster title and an
    English replay title cannot become two episodes;
  * a field that already has a value is never overwritten (editors' changes win);
  * fields listed in a record's "locked_fields" are never touched;
  * a record with "editorial_updated" later than the batch date is left alone.

Usage: python3 scripts/import_content.py content/imports/2026-11-25-handover.json [--dry-run]
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "src/data/episodes.json"

def empty(v):
    return v is None or v == "" or v == [] or v == {}

def merge(store, batch):
    by_id = {e["youtube_id"]: e for e in store["episodes"]}
    as_of = batch.get("as_of", "")
    added, filled, skipped, conflicts = [], [], [], []
    for rec in batch["episodes"]:
        vid = rec.get("youtube_id")
        if not vid:
            skipped.append(("(no id)", "records without a YouTube ID are not imported"))
            continue
        cur = by_id.get(vid)
        if cur is None:
            new = dict(rec)
            store["episodes"].append(new)
            by_id[vid] = new
            added.append(vid)
            continue
        if cur.get("editorial_updated", "") > as_of:
            skipped.append((vid, "edited after this batch"))
            continue
        locked = set(cur.get("locked_fields", []))
        for k, v in rec.items():
            if k in locked or empty(v):
                continue
            if empty(cur.get(k)):
                cur[k] = v
                filled.append((vid, k))
            elif cur[k] != v:
                conflicts.append((vid, k))
    store["episodes"].sort(key=lambda e: (e.get("date") or "0000", e.get("episode") or 0), reverse=True)
    return added, filled, skipped, conflicts

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    batch = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
    store = json.loads(STORE.read_text(encoding="utf-8"))
    added, filled, skipped, conflicts = merge(store, batch)
    print(f"added {len(added)}, filled {len(filled)} empty fields, skipped {len(skipped)}, kept {len(conflicts)} existing values")
    for vid, k in conflicts:
        print(f"  kept existing {k!r} on {vid} (batch value differs)")
    if "--dry-run" not in sys.argv:
        STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
