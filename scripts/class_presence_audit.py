"""Patch-level positive structural claims checked against valid ISPRS class IDs."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
from PIL import Image


# Four individual land-cover roles. The small rigid group also encodes multiplicity.
ROLE_CLASSES = {"open_hard_surface": 1, "elevated_closed_rigid": 2,
                "ground_vegetation": 3, "elevated_porous": 4}


def audit(pairs):
    positive = Counter({k: 0 for k in ROLE_CLASSES})
    unmatched = positive.copy()
    flagged = []
    seen = set()
    for sample, roles, mask_path in pairs:
        assert sample not in seen
        seen.add(sample)
        with Image.open(mask_path) as im:
            gt = np.asarray(im)
            assert gt.ndim == 2 and gt.max() <= 6 and gt.max() > 0
            labels = np.bincount(gt.ravel(), minlength=7)
        for role, cls in ROLE_CLASSES.items():
            if roles[role]["presence"] == "present":
                positive[role] += 1
                if labels[cls] == 0:
                    unmatched[role] += 1
                    flagged.append({"image_id": sample, "role": role, "class_id": cls})
    return dict(images=len(seen), positive=sum(positive.values()), unmatched=sum(unmatched.values()),
                by_role={k: [unmatched[k], positive[k]] for k in ROLE_CLASSES}, flags=flagged)


def audit_records(dataset, records, mask_root):
    return audit((r["id"], r["payload"]["roles"], mask_root / (r["payload"]["image_id"] + ".png"))
                 for r in records if r["dataset"] == dataset and r["split"] == "Test")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", choices=["Potsdam", "Vaihingen"])
    ap.add_argument("records", type=Path, help="Path to the dataset's Test.jsonl file")
    ap.add_argument("mask_root", type=Path, help="Directory of original evaluation masks, IDs 0..6")
    args = ap.parse_args()
    rows = [json.loads(l) for l in args.records.read_text(encoding="utf-8").splitlines()]
    print(json.dumps(audit_records(args.dataset, rows, args.mask_root), indent=2))
