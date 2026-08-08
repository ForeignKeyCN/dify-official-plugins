"""Smoke-test the provider's declared tools against the manifest."""
import importlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LlamaParseProvider = importlib.import_module("provider.llama").LlamaParseProvider


manifest = yaml.safe_load((ROOT / "provider/llama.yaml").read_text())
provider = LlamaParseProvider()
declared_tools = {Path(tool).stem for tool in manifest["tools"]}
assert declared_tools == {"llama_parse", "llama_parse_advanced"}
assert provider.__class__.__name__ == "LlamaParseProvider"
