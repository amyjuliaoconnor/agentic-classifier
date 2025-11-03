import os
import re
import csv
import json
import yaml
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from providers import PROVIDERS

# ====================================================
# CONFIGURATION
# ====================================================
RELEVANT_FILETYPES = (".py", ".js", ".ts")
OUTPUT_FILE_CSV = "agentic_features_summary.csv"
OUTPUT_FILE_JSON = "agentic_agent_profiles.json"
OUTPUT_SEMANTIC_JSON = "agentic_semantic_features.json"
LOG_FILE = "clone_failures.log"
MAX_WORKERS = 6

CLONE_DIR = Path(tempfile.gettempdir()) / "agentic_repos"

# ====================================================
# LOGGING
# ====================================================
def log_failure(provider, repo_url, error_text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{provider}] {repo_url}\n")
        f.write(error_text.strip() + "\n")
        f.write("-" * 80 + "\n")

# ====================================================
# README + CONFIG PARSERS
# ====================================================
def extract_readme_info(repo_path: Path):
    readme_data = {"name": None, "description": None, "tools": [], "models": []}
    readme_files = list(repo_path.rglob("README.md"))
    if not readme_files:
        return readme_data
    try:
        with open(readme_files[0], encoding="utf-8", errors="ignore") as f:
            content = f.read()
        name_match = re.search(r"#\s*([A-Z][\w\s-]+(?:Agent|Bot|System)?)", content)
        if name_match:
            readme_data["name"] = name_match.group(1).strip()
        desc_match = re.search(
            r"(?:description|about|purpose)[:\-–]\s*(.+?)(?:\n|$)", content, re.I
        )
        if desc_match:
            readme_data["description"] = desc_match.group(1).strip()
        else:
            lines = [l.strip() for l in content.split("\n") if l.strip()]
            readme_data["description"] = " ".join(lines[:3])[:300]
        models = re.findall(
            r"\b(gpt[-\w]+|claude[-\w]+|mistral|llama[-\w]+|palm[-\w]+|vertexai|openai)\b",
            content,
            re.I,
        )
        tools = re.findall(
            r"\b(search|browser|retriever|database|calculator|codeinterpreter|slack|discord|jira)\b",
            content,
            re.I,
        )
        readme_data["models"] = list(set(models))
        readme_data["tools"] = list(set(tools))
    except Exception as e:
        print(f"⚠️ Error parsing README: {e}")
    return readme_data

def extract_config_info(repo_path: Path):
    config_data = {"env_vars": [], "models": [], "tools": []}
    for ext in ("*.yaml", "*.yml", "*.json"):
        for file in repo_path.rglob(ext):
            try:
                with open(file, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    if ext in ("*.yaml", "*.yml"):
                        data = yaml.safe_load(text)
                    else:
                        data = json.loads(text)
                    if not isinstance(data, dict):
                        continue
                    def flatten(d, parent_key=""):
                        items = []
                        for k, v in d.items():
                            new_key = f"{parent_key}.{k}" if parent_key else k
                            if isinstance(v, dict):
                                items.extend(flatten(v, new_key))
                            elif isinstance(v, list):
                                for i in v:
                                    if isinstance(i, (dict, list)):
                                        items.extend(flatten({"list_item": i}, new_key))
                                    else:
                                        items.append((new_key, str(i)))
                            else:
                                items.append((new_key, str(v)))
                        return items
                    flat_items = flatten(data)
                    for key, value in flat_items:
                        if "api_key" in key.lower() or "token" in key.lower():
                            config_data["env_vars"].append(key)
                        if "model" in key.lower():
                            config_data["models"].append(value)
                        if "tool" in key.lower():
                            config_data["tools"].append(value)
            except Exception:
                continue
    for k in config_data:
        config_data[k] = sorted(set(map(str, config_data[k])))
    return config_data

# ====================================================
# CODE FEATURE EXTRACTION
# ====================================================
def extract_features_from_code(code: str):
    imports = re.findall(r"(?:import|from)\s+([\w\.]+)", code)
    classes = re.findall(r"class\s+(\w+)", code)
    funcs = re.findall(r"def\s+(\w+)", code)
    apis = re.findall(r"(\w+)\.", code)
    return imports, classes, funcs, apis

def analyze_local_repo(repo_path: Path):
    counters = defaultdict(Counter)
    semantic_summary = defaultdict(set)
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(RELEVANT_FILETYPES):
                path = Path(root) / file
                try:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    imports, classes, funcs, apis = extract_features_from_code(code)
                    counters["imports"].update(imports)
                    counters["classes"].update(classes)
                    counters["functions"].update(funcs)
                    counters["apis"].update(apis)
                except Exception as e:
                    print(f"⚠️ Error reading {path}: {e}")
    readme_info = extract_readme_info(repo_path)
    config_info = extract_config_info(repo_path)
    return counters, readme_info, config_info

# ====================================================
# CLONE + ANALYZE
# ====================================================
def clone_and_analyze(provider, repo_url):
    repo_dir = CLONE_DIR / provider
    if repo_dir.exists():
        shutil.rmtree(repo_dir, ignore_errors=True)
    try:
        print(f"🚀 Cloning {provider} from {repo_url} ...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            print(f"❌ Failed to clone {provider}")
            log_failure(provider, repo_url, result.stderr)
            return provider, None
        counters, readme, config = analyze_local_repo(repo_dir)
        print(f"✅ Finished analyzing {provider}")
        return provider, counters, readme, config
    except Exception as e:
        log_failure(provider, repo_url, str(e))
        return provider, None
    finally:
        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)

# ====================================================
# OUTPUT WRITERS
# ====================================================
def write_outputs(results):
    csv_path = OUTPUT_FILE_CSV
    json_path = OUTPUT_FILE_JSON
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Provider", "Feature_Type", "Feature_Name", "Frequency"])
        for provider, data in results.items():
            counters = data["counters"]
            for ftype, counter in counters.items():
                for name, freq in counter.most_common(50):
                    writer.writerow([provider, ftype, name, freq])
    structured_output = {}
    for provider, data in results.items():
        structured_output[provider] = {
            "agent_profile": {
                "is_agentic": True,
                "code_features": data["counters"],
                "metadata": {
                    "readme": data["readme"],
                    "config": data["config"],
                },
            }
        }
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(structured_output, jf, indent=2)
    print(f"\n✅ Outputs written:\n - {csv_path}\n - {json_path}")

# ====================================================
# MAIN
# ====================================================
def main():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    if CLONE_DIR.exists():
        shutil.rmtree(CLONE_DIR, ignore_errors=True)
    CLONE_DIR.mkdir(exist_ok=True)
    results = {}
    print(f"🧠 Using temporary clone directory: {CLONE_DIR}")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(clone_and_analyze, provider, url): provider
            for provider, url in PROVIDERS.items()
        }
        for future in as_completed(futures):
            provider = futures[future]
            result = future.result()
            if result and len(result) == 4:
                name, counters, readme, config = result
                results[name] = {
                    "counters": counters,
                    "readme": readme,
                    "config": config,
                }
    write_outputs(results)
    if CLONE_DIR.exists():
        shutil.rmtree(CLONE_DIR, ignore_errors=True)
    print("\n🧹 Cleanup complete. Check clone_failures.log for any issues.")

if __name__ == "__main__":
    main()
