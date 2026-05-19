"""Proof that our gateway is OpenAI-SDK compatible."""
from openai import OpenAI
 
client = OpenAI(api_key="not-needed-yet", base_url="http://localhost:8000/v1")
 
resp = client.chat.completions.create(
    model="claude-haiku-4-5",
    messages=[
        {"role": "system", "content": "You are a witty product copywriter."},
        {"role": "user", "content": "One-liner for a stainless steel water bottle."},
    ],
    max_tokens=80,
)
print(resp.choices[0].message.content)
print(f"Usage: {resp.usage}")