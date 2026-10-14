# Real ESM-2 comparison

Install the optional model dependencies and use the free pretrained checkpoint:

```bash
python -m pip install -r requirements-model.txt
HF_HOME=./cache python encode_esm.py --device cuda
```

Use `--device cpu` or `--device mps` as appropriate; `--batch-size 16` and `--k 10` are the defaults. A local CSV with `sequence` plus optional `id` and `family` columns can be supplied with `--input peptides.csv`. `--reference bos` compares BOS pooling with mean residue pooling. Default reference is the 20-dimensional amino-acid frequency baseline. The encoder rejects noncanonical sequences and overlong inputs instead of truncating.

Without `--input`, it fetches the 100 candidate peptides from the maintainer's already-public structure atlas at a pinned commit. This is a selected set of predicted candidates, not a representative protein dataset or experimental benchmark. The run manifest pins ESM-2 to a commit, records data SHA-256 and package versions, and excludes special tokens/padding from mean pooling.

See `results/esm-public-atlas/manifest.json`, `input.json` and `report.json` for the actual local CPU run included with this repo. Its interpretation is limited to neighbor changes under two representations. It does not measure antimicrobial activity, homology recognition quality or downstream predictive accuracy. The model weights are downloaded to the chosen cache directory and are not committed.

Model reference: [ESM-2 8M checkpoint](https://huggingface.co/facebook/esm2_t6_8M_UR50D), [original ESM implementation](https://github.com/facebookresearch/esm). Model weights retain their MIT license. The code path was tested on CPU; GPU/MPS execution is available but has not been separately validated here.
