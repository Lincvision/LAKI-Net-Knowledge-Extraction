# Class-presence audit

The audit asks whether a structural role marked `present` has **at least one valid pixel of the corresponding class in the same test patch**. Each positive role claim contributes once to the denominator. A patch can contribute up to four claims. Pixels with the ignore label 0 provide no class evidence.

| Dataset | Test patches | Positive claims | Claims with no matching class pixel |
|---|---:|---:|---:|
| Potsdam | 504 | 1,824 | 10 (0.55%) |
| Vaihingen | 113 | 444 | 1 (0.23%) |
| **Total** | **617** | **2,268** | **11 (0.49%)** |

## Which roles account for the flags?

Each cell below gives flagged claims divided by positive claims. Eight of the eleven flags concern the building-associated role on Potsdam.

| Structural role | Reference class (disk label) | Potsdam | Vaihingen |
|---|---|---:|---:|
| `open_hard_surface` | Impervious surface (1) | 1 / 498 | 0 / 112 |
| `elevated_closed_rigid` | Building (2) | 8 / 446 | 0 / 112 |
| `ground_vegetation` | Low vegetation (3) | 0 / 406 | 0 / 108 |
| `elevated_porous` | Tree (4) | 1 / 474 | 1 / 112 |

The results file lists each flagged patch, role and class ID. For example, the building-associated role was flagged for Potsdam patch `Urban/top_potsdam_4_14_r01_c04`. A matching class anywhere in a patch satisfies the criterion, so passing this check does not establish that the model identified the intended object. The small-rigid-group role requires evidence of multiple objects. The class masks also lack labels for textures and spatial relations. Hallucination rates for those claims remain unmeasured. [Full counts and flagged patch IDs](isprs_test.json)

## Reproduce the counts

From the repository root, install the [requirements](../../readme/requirements.txt) and supply the single-channel ISPRS evaluation masks with disk labels 0–6. Within the mask directory, each filename must match the record's `payload.image_id` followed by `.png`. Replace the example mask paths below with your own.

```sh
python scripts/class_presence_audit.py Potsdam knowledge/Potsdam/Test.jsonl /path/to/Potsdam/Test/Urban/masks_png
python scripts/class_presence_audit.py Vaihingen knowledge/Vaihingen/Test.jsonl /path/to/Vaihingen/Test/Urban/masks_png
```

For each dataset, the script prints `images` (patches checked), `positive` (positive role claims), `unmatched` (flagged claims), `by_role` (pairs of unmatched and positive counts), and `flags` (the individual cases). Compare these fields with the [published JSON](isprs_test.json). [Audit script](../../scripts/class_presence_audit.py)
