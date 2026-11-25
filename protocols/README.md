# Extraction prompts and parsing

Each request supplies one original 1024 × 1024 image and its image ID. The prompt asks for categorical observations of five structures, eight visual cues and four spatial relations. When the image does not support a decision, the model can return `unknown`.

| Dataset | English prompt for reuse | Original prompt used for extraction | Field values and relation signatures | JSON Schema |
|---|---|---|---|---|
| Potsdam | [English](Potsdam/extraction_prompt.txt) | [Chinese](Potsdam/extraction_prompt.zh.txt) | [Protocol](Potsdam/protocol_snapshot.json) | [Schema](Potsdam/annotation_payload.schema.json) |
| Vaihingen | [English](Vaihingen/extraction_prompt.txt) | [Chinese](Vaihingen/extraction_prompt.zh.txt) | [Protocol](Vaihingen/protocol_snapshot.json) | [Schema](Vaihingen/annotation_payload.schema.json) |
| LoveDA | [English](LoveDA/extraction_prompt.txt) | [Chinese](LoveDA/extraction_prompt.zh.txt) | [Protocol](LoveDA/protocol_snapshot.json) | [Schema](LoveDA/annotation_payload.schema.json) |

Vaihingen uses near-infrared, red and green channels in that order. Its prompt explains how to interpret red vegetation in the false-color display and how to handle reflection padding near patch boundaries. Potsdam and LoveDA use RGB imagery. Both language versions and the accompanying specifications have published checksums. [SHA-256 checksums](../metadata/protocol_sha256.json)

## Prepare a request

From the repository root, run the command below. It prints the English prompt, dataset protocol, JSON Schema and image ID. Submit this text together with the matching image. A fresh generation can differ from the archived response.

```sh
python scripts/make_request.py Potsdam top_potsdam_2_13_r00_c00
```

## How a response becomes a record

1. **Decode the fields.** The JSON response has six required fields: `image_id`, `graph_status`, `quality_flags`, `roles`, `evidence` and `relations`. For observations saved as compact codes, `compact_to_payload` expands the codes in the fixed protocol order.
2. **Validate the observations.** The release checker applies the dataset's JSON Schema and the original `validate_payload` rules. For example, `ground_vegetation=present` requires `continuous_fine_vegetation_texture=present`. An absent endpoint makes a relation `not_applicable`. If neither endpoint is absent and either is unknown, the relation must be `unknown`. The validator returns an empty list for a record that passes its checks. [Parser and compact-code decoder](../scripts/payload_validator.py)
3. **Associate the graph with its patch.** The validated role, cue and relation states provide node attributes in a fixed graph. The archived records and graphs use the same dataset, split and patch ID. [Walk through a stored record](../examples/README.md)
