import re
import json
from collections import Counter

INPUT_JSON = "agentic_agent_profiles.json"
OUTPUT_JSON = "agentic_semantic_keywords.json"

def tokenize_identifier(name):
    # Split CamelCase and snake_case
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", name)
    parts = [p.lower() for p in parts if len(p) > 1]
    return parts

def build_global_semantic_keywords():
    with open(INPUT_JSON, encoding="utf-8") as f:
        data = json.load(f)

    token_counter = Counter()

    for provider, repo in data.items():
        code_feats = repo["agent_profile"]["code_features"]
        for section in ("imports", "classes", "functions", "apis"):
            for name in code_feats.get(section, {}):
                for token in tokenize_identifier(name):
                    if len(token) > 2 and token not in {"self", "init", "main"}:
                        token_counter[token] += 1

    top_tokens = token_counter.most_common(500)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump({"semantic_keywords": top_tokens}, out, indent=2)
    print(f"✅ Extracted {len(top_tokens)} candidate semantic keywords → {OUTPUT_JSON}")

if __name__ == "__main__":
    build_global_semantic_keywords()
