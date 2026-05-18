"""First contact with Claude. Run: python scripts/hello_claude.py"""
from __future__ import annotations
 
import asyncio
import sys
from pathlib import Path
 
# Make `src/` importable when running this script directly.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
 
from shopllm.providers.anthropic_adapter import AnthropicAdapter  # noqa: E402
 
 
async def main() -> None:
    adapter = AnthropicAdapter()
    prompt = (
        "In 2 sentences, write a punchy product description for a pair of "
        "vegan leather sneakers, white, unisex, size 42."
    )
    result = await adapter.chat(prompt, max_tokens=200)
    print("=" * 60)
    print(f"Model:   {result.model}")
    print(f"Tokens:  in={result.input_tokens}  out={result.output_tokens}")
    print("=" * 60)
    print(result.text)
    print("=" * 60)
 
 
if __name__ == "__main__":
    asyncio.run(main())