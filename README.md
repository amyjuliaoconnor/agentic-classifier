# 🧠 Agentic Detector

A Python-based pipeline for **scanning, analyzing, and classifying agentic AI codebases**.  
It extracts code features, configuration details, and semantic patterns to help you **detect and categorize agent frameworks** (like LangChain, AutoGen, CrewAI, SmolAgents, LlamaIndex, and more) across your organization.

---

## 🚀 Overview

The Agentic Detector automates the process of discovering what makes code *agentic*.  
It does this by:
1. Cloning and analyzing repositories.
2. Extracting **imports, class names, functions, and API usage**.
3. Reading **README files and YAML/JSON configs** for metadata and environment variables.
4. Mining **semantic keywords** that frequently appear in agentic frameworks.
5. Generating **framework-specific keyword lists** you can use to detect and classify agentic work.

---

## 🧩 Pipeline Components

| Script | Purpose |
|--------|----------|
| `main.py` | Clones each agentic repo, extracts structural and semantic code features, and writes results to CSV/JSON. |
| `postprocess_semantics.py` | Analyzes aggregated results to build a global list of recurring “agentic” tokens. |
| `build_framework_keywords.py` | Groups discovered tokens by framework (e.g., LangChain, SmolAgents, AutoGen) to generate per-framework patterns. |
| `providers.py` | Contains a list of known agentic framework repositories (LangChain, AutoGen, CrewAI, LlamaIndex, etc.). |

---

## 🧠 Why This Matters

Agentic frameworks (LangChain, AutoGen, CrewAI, Semantic Kernel, etc.) share common building blocks:
- **Agent orchestration** (`Planner`, `Executor`, `Coordinator`)
- **Memory and context management**
- **Tool and environment integration**
- **LLM interaction and reasoning loops**

This project builds a **unified pattern vocabulary** for identifying such characteristics in any codebase — helping you classify, govern, or audit AI systems consistently.

---

## 🧰 Installation

```bash
git clone https://github.com/YOUR_USERNAME/agentic-detector.git
cd agentic-detector
pip install -r requirements.txt
```

---

## ⚙️ Usage

Run the pipeline in sequence:

```bash
# Step 1 – Scan and extract code + metadata
python main.py

# Step 2 – Mine global semantic keywords
python postprocess_semantics.py

# Step 3 – Build framework-specific keyword sets
python build_framework_keywords.py
```

---

## 📦 Output Files

| File | Description |
|------|--------------|
| `agentic_agent_profiles.json` | Structural and metadata summary for each scanned repo |
| `agentic_features_summary.csv` | Top 50 feature frequencies per category per provider |
| `agentic_semantic_keywords.json` | Globally frequent tokens across all agentic codebases |
| `framework_semantic_keywords.json` | Framework-specific keywords for detection/classification |

---

## 🧩 Example Output

### `framework_semantic_keywords.json`
```json
{
  "LangChain": [
    "llm", "chain", "prompt", "memory", "tool", "workflow", "retriever"
  ],
  "AutoGen": [
    "assistant", "groupchat", "userproxy", "planner", "functioncall"
  ],
  "SmolAgents": [
    "codeagent", "multistepagent", "toolcallingagent", "execute", "reason"
  ],
  "CrewAI": [
    "crew", "agentrole", "task", "planner", "workflow"
  ]
}
```

---

## 🧩 Use Cases

- 🕵️ **Code discovery** — Identify agentic or LLM-integrated systems across your org.  
- 🧱 **Architecture governance** — Detect frameworks used in internal AI projects.  
- 🔍 **Pattern learning** — Generate regexes or ML features for classifying agentic behavior.  
- 📚 **Research & benchmarking** — Analyze framework design trends across repositories.

---

## 🧹 Cleaning Up

Temporary cloned repositories are stored in your system temp folder and deleted automatically after analysis.  
Failed clones are logged in `clone_failures.log`.

---

## 🧩 Folder Structure

```
agentic-detector/
│
├── main.py
├── postprocess_semantics.py
├── build_framework_keywords.py
├── providers.py
├── README.md
├── requirements.txt
├── .gitignore
│
└── example_output/
    ├── agentic_agent_profiles.json
    ├── agentic_features_summary.csv
    ├── agentic_semantic_keywords.json
    └── framework_semantic_keywords.json
```

---

## 🧑‍💻 Contributing

Contributions are welcome!  
Add new frameworks, extend regex logic, or enhance semantic extraction.  
Please open a pull request with a clear description of your changes.

---

## 📜 License

MIT License © 2025

---

## 🌐 Learn More

- [LangChain](https://github.com/langchain-ai/langchain)
- [Microsoft AutoGen](https://github.com/microsoft/autogen)
- [CrewAI](https://github.com/crewAIInc/crewAI)
- [SmolAgents](https://github.com/huggingface/smolagents)
- [Semantic Kernel](https://github.com/microsoft/semantic-kernel)
- [LlamaIndex](https://github.com/run-llama/llama_index)

---

⭐ **Star this repo** if you find it useful for understanding or detecting agentic systems!
