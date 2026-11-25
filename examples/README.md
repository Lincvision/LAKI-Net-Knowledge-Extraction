# How to read a patch record

Open the [LoveDA example](LoveDA.json). It is training patch `Rural/470`. Its `payload` contains the extraction for that image, and its `graph` shows how the same information is represented as nodes and edges.

## What was observed in this patch?

| Field in the payload | Recorded value | Interpretation |
|---|---|---|
| `roles.elevated_porous.presence` | `present` | The model reported a tree-like elevated structure. |
| `evidence.porous_crown_texture.state` | `present` | The model reported canopy texture, a diagnostic cue for that role. |
| `roles.open_hard_surface.presence` | `present` | The model also reported an open hard surface. |
| `R2.state` in `relations` | `not_observed` | Both roles were present. The model did not report visible evidence that the tree-like structure occludes the hard surface. |

The same record illustrates the other three relation states. For `R1`, occlusion of ground vegetation was `observed`. For `R3`, interruption of the hard surface was `unknown` because the building-associated role was uncertain. For `R4`, the vehicle-group relation was `not_applicable` because the small-rigid-group role was marked absent. These entries describe the model's observations.

## How the example maps to the archive

- **Sample identity.** Use the outer `dataset`, `split` and `id` to find the same patch in both files. Here the key is `LoveDA / Train / Rural/470`. The inner `payload.image_id` is `470`, and the outer ID includes the region. The `input_sha256` field identifies the source image file. [Knowledge records](../knowledge/LoveDA/Train.jsonl) · [Factor graphs](../graphs/LoveDA/Train.jsonl)
- **Patch-level fields.** `graph_status` summarizes the available evidence for the patch (`partial` here). `quality_flags` records boundary truncation, shadow interference and orthophoto distortion. The role, cue and relation fields carry the categorical observations.
- **Graph representation.** Each graph has five role nodes, eight cue nodes and four relation nodes. Cue-to-role edges identify the structures each cue can support. Each relation node has a source role and a target role. The protocol defines their direction and meaning. [LoveDA protocol](../protocols/LoveDA/protocol_snapshot.json)

For urban aerial imagery, see the [Potsdam RGB example](Potsdam.json) and the [Vaihingen false-color example](Vaihingen.json).
