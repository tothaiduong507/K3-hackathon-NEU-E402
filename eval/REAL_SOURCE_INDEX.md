# Real-source index for `golden_set.json`

The golden set contains **26 cases**, including **11 cases derived from real run artifacts** already stored in the repository. A real case preserves the original query or paper title in `source_input` and points to its source file with `source_ref`.

| Case | Original input | Source artifact |
|---|---|---|
| N01 | `retrieval augmented generation for literature review` | `codebase/runs/review_20260730T102756Z_f600151b.json` |
| N02 | `Graph Neural Network for Multi-omics Classification` | `codebase/runs/review_20260730T134722Z_07603245.json` |
| N03 | `districting problem` | `codebase/runs/review_20260730T140052Z_df0d3602.json` |
| N04 | `Large Language Model Hallucination Mitigation` | `codebase/runs/review_20260730T140743Z_135c5443.json` |
| N05 | `probability-based VNS` | `codebase/runs/review_20260730T142215Z_0a929402.json` |
| N06 | `Diffusion Models for Medical Image Segmentation` | `codebase/runs/review_20260730T151428Z_f2010e3d.json` |
| N07 | `Visual Attention Network` | `codebase/runs/deep_20260730T150905Z_5a6740fb.json` |
| N08 | `Beyond Self-attention: External Attention using Two Linear Layers for Visual Tasks` | `codebase/runs/deep_20260730T151203Z_48719fd9.json` |
| A01 | `attention` | `codebase/runs/review_20260730T142745Z_b38d5df5.json` |
| A02 | `attention in NLP` | `codebase/runs/review_20260730T145703Z_f42ed38f.json` |
| D01 | `Attention Is All You Need` | `codebase/runs/deep_20260730T150456Z_3abfcfdc.json` |

## Counting method

- `source_type = "real"` means the input can be opened and checked in the referenced run JSON.
- `source_type = "synthetic"` means the team authored the case for regression, boundary, or rare-path coverage.
- Duplicate runs with the same input are not counted as additional real-source cases.
- The real-source input is not evidence from an external user study; it is evidence of actual prototype use and is labelled accordingly.

