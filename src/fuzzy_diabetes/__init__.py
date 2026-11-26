"""Educational fuzzy inference; not a clinical screening or diagnostic system."""

from .engine import InferenceError, infer, load_model, membership

__all__ = ["InferenceError", "infer", "load_model", "membership"]
__version__ = "2.0.0"
