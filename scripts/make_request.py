"""Print the English extraction instructions for one patch. Attach its original image separately."""
import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=("Potsdam", "Vaihingen", "LoveDA"))
    parser.add_argument("image_id", help="Image filename without its extension or region prefix")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parents[1] / "protocols" / args.dataset
    prompt = (folder / "extraction_prompt.txt").read_text(encoding="utf-8-sig").strip()
    protocol = json.loads((folder / "protocol_snapshot.json").read_bytes())
    schema = json.loads((folder / "annotation_payload.schema.json").read_bytes())
    if not re.fullmatch(schema["properties"]["image_id"]["pattern"], args.image_id):
        parser.error("The image ID does not match the dataset schema.")
    print(prompt)
    print("\nProtocol\n" + json.dumps(protocol, ensure_ascii=True))
    print("\nJSON Schema\n" + json.dumps(schema, ensure_ascii=True))
    print("\nCURRENT_IMAGE is the single image attached to this request.")
    print("IMAGE_ID=" + args.image_id)


if __name__ == "__main__":
    main()
