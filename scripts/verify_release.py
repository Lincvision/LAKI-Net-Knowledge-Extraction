"""Validate the released payloads, graph alignment, protocol hashes and split counts."""
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from payload_validator import validate_payload


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_lines(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def verify():
    counts = read_json(ROOT / "metadata" / "split_counts.json")
    hashes = read_json(ROOT / "metadata" / "protocol_sha256.json")
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"File differs from its published checksum: {name}")
    total = 0
    for dataset, splits in counts.items():
        folder = ROOT / "protocols" / dataset
        protocol = read_json(folder / "protocol_snapshot.json")
        schema = read_json(folder / "annotation_payload.schema.json")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        dataset_ids = set()
        for split, expected in splits.items():
            filename = f"{split}.jsonl"
            records = read_lines(ROOT / "knowledge" / dataset / filename)
            graphs = read_lines(ROOT / "graphs" / dataset / filename)
            count = 0
            for row, item in zip(records, graphs, strict=True):
                payload = row["payload"]
                key = (dataset, split, row["id"])
                if key != (row["dataset"], row["split"], row["id"]) or key != (item["dataset"], item["split"], item["id"]):
                    raise ValueError(f"Dataset, split or sample mismatch at {key}")
                if row["id"] in dataset_ids or row["id"].split("/")[-1] != payload["image_id"]:
                    raise ValueError(f"Duplicate or mismatched ID at {key}")
                validator.validate(payload)
                errors = validate_payload(payload, protocol)
                if errors:
                    raise ValueError(f"{key}: {errors}")
                graph = item["graph"]
                if (graph["image_id"] != payload["image_id"] or graph["schema_version"] != protocol["schema_version"]
                    or len(graph["nodes"]) != 17 or len(graph["edges"]) != 17):
                    raise ValueError(f"Graph mismatch at {key}")
                dataset_ids.add(row["id"])
                count += 1
            if count != expected:
                raise ValueError(f"Expected {expected} records in {dataset}/{split}, found {count}")
            total += count
        print(f"{dataset}: {len(dataset_ids)} validated records and graphs")
    print(f"Total: {total} matched pairs")


if __name__ == "__main__":
    verify()
