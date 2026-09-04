import sys
from pathlib import Path

# Set up paths for seamless importing
ROOT = Path(__file__).resolve().parent
sys.path.extend([
    str(ROOT),
    str(ROOT / "common"),
    str(ROOT / "variants")
])

# Import original classes for backwards compatibility with benchmarks and evaluations
from variants.original.nlu_pipeline import (
    _normalize_lookup,
    RulesSemanticParser,
    LLMSemanticParser,
    Normalizer,
    Validator,
    QueryBuilder,
    NLUPipeline
)
