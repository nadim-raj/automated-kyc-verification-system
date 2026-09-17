# 0005 — Heavy dependencies stay optional

**Status:** accepted

## Context

The natural stack here is PyTorch for face embeddings and spaCy for name extraction. Both are large. A reader who clones a portfolio repository and hits a multi-gigabyte install, a model download, or a version conflict closes the tab.

## Decision

The base install has no dependencies. Models sit behind protocols with standard-library implementations; PyTorch, spaCy and RapidFuzz live in an `ml` extra and are imported lazily inside the adapters that need them.

## Consequences

- **`git clone && make demo` works immediately**, on a clean machine, in seconds.
- **CI needs no install step**, so it stays fast and cannot break on a dependency release.
- **Optional dependencies improve things when present** rather than being required: RapidFuzz replaces `difflib` for string similarity, spaCy replaces the heuristic name extractor, both behind the same interface.
- **The real adapters are less exercised.** `TorchFaceEmbedder` is an interface and a docstring, not a working model, and the README says so rather than implying otherwise.
