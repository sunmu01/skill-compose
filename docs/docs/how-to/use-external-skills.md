---
sidebar_position: 5
---

# Use External Skills

Install skills from third-party repositories and assemble them into domain-specific agents.

## Overview

External skill collections provide ready-made domain expertise. Instead of writing skills from scratch, you can import them and focus on agent configuration — the system prompt and workflow logic.

**Example:** The [claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) repository provides 150+ scientific skills covering cheminformatics, bioinformatics, data analysis, and more.

## Step 1: Import Skills

### From GitHub (Recommended)

1. Go to **Skills** > **Import**
2. Enter the skill's GitHub URL:

```
https://github.com/K-Dense-AI/claude-scientific-skills/tree/main/scientific-skills/rdkit
```

3. Click **Import**

Repeat for each skill you need. The system records the GitHub source so you can pull updates later. You can also update any skill from a new source (GitHub URL, file, or folder) via the **⋯** menu > **Update Version** on the skill detail page.

### From Cloned Repository

Clone the repo and copy skill directories into `skills/`:

```bash
git clone https://github.com/K-Dense-AI/claude-scientific-skills.git /tmp/sci-skills

# Copy the skills you need
cp -r /tmp/sci-skills/scientific-skills/rdkit skills/
cp -r /tmp/sci-skills/scientific-skills/pubchem-database skills/
cp -r /tmp/sci-skills/scientific-skills/biopython skills/
```

Then go to **Skills** page — the blue "unregistered skills found" banner appears. Click to import.

### Via API

```bash
curl -X POST http://localhost:62610/api/v1/registry/import-github \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/K-Dense-AI/claude-scientific-skills/tree/main/scientific-skills/rdkit"}'
```

## Step 2: Install Dependencies

External skills often require Python packages or system libraries. Check each skill's `SKILL.md` for installation requirements.

**Example** — for a cheminformatics agent:

```bash
# System packages
apt-get install -y libxrender1 libxext6

# Python packages
pip install rdkit-pypi pubchempy biopython requests pandas pillow
```

If using Docker, either:
- Add dependencies to your API container's Dockerfile
- Use an [Executor container](/how-to/build-custom-executor) with the packages pre-installed

## Step 3: Create the Agent

Go to **Agents** > **New Agent** and configure:

| Field | Description |
|-------|-------------|
| **Name** | Domain-specific name (e.g., "ChemScout") |
| **System Prompt** | Workflow logic — when to use which skill, how to interpret results (see below) |
| **Skills** | Select the imported skills |
| **Tools** | `execute_code`, `read`, `write` (at minimum) |
| **Model** | Choose based on task complexity |

### Writing the System Prompt

The system prompt is the core of your agent. Since skills are loaded on-demand via `list_skills` / `get_skill`, the prompt should focus on:

1. **Role definition** — what the agent is and isn't
2. **Decision logic** — which skill to use for which user intent
3. **Workflow chains** — multi-step sequences ("if user mentions a compound → fetch data → compute properties → draw structure")
4. **Domain interpretation** — how to read results (thresholds, pass/fail criteria, units)
5. **Output format** — tables, images, structured reports

**Don't include** skill API details — the agent loads those from `get_skill` at runtime.

**Example prompt structure:**

```markdown
You are [Role]. You help [audience] with [task domain].

## Scope
Can do: [list capabilities]
Cannot do: [list limitations, suggest alternatives]

## Decision Logic
When a user mentions [trigger] → use [skill A] then [skill B] then [skill C]
When a user asks about [trigger] → use [skill D]

## Interpretation Guide
[Domain-specific thresholds, rules, heuristics]

## Output Format
[Tables, images, structured cards]

## Rules
[Behavioral constraints]
```

## Example: ChemScout (Drug Discovery Agent)

A complete example using skills from `claude-scientific-skills`:

**Skills:** `pubmed-database`, `pubchem-database`, `rdkit`, `pdb-database`, `biopython`

**System Prompt:**

```
You are ChemScout, an early-stage drug discovery assistant.

## Scope
Can do: literature search, compound retrieval, drug-likeness assessment
  (Lipinski/QED), 2D structure drawing, structural similarity, protein
  structure download.
Cannot do: quantum chemistry, molecular dynamics, docking, de novo generation.

## Decision Logic
When user mentions a compound name or SMILES:
  1. Retrieve data from PubChem (pubchem-database)
  2. Compute Lipinski + QED (rdkit)
  3. Draw 2D structure (rdkit)
  → Always do all three automatically.

When user asks about a disease or target:
  1. Search PubMed (pubmed-database / biopython)
  2. Download PDB structure if applicable (pdb-database)

When user asks to compare compounds:
  1. Retrieve each from PubChem
  2. Compute Lipinski for all
  3. Compute Tanimoto similarity (rdkit)
  4. Draw grid image

## Interpretation Guide
Lipinski: 0 violations = excellent, 1 = acceptable, 2+ = problematic
QED: >0.67 favorable, <0.3 unfavorable
Tanimoto: >0.85 very similar, <0.3 structurally distinct

## Rules
- Always draw molecules. Chemists think in structures.
- Always compute Lipinski when fetching a compound.
- Use tables for property comparisons.
- Include units (MW in g/mol, TPSA in Å²).
```

**Test result:** All 6 skills verified — Lipinski computation, structure image generation, similarity search, and PDB download work fully; PubMed and PubChem require NCBI-accessible network.

## Tips

- **Start with 2–3 skills** and add more as the agent's scope grows
- **Test each skill independently** before combining them into an agent
- **Check network requirements** — some skills call external APIs (NCBI, RCSB PDB) that may need specific network access
- **Use Executor containers** for skills with heavy dependencies (ML, GPU) to keep the main API container lean
- **Review traces** after test runs to see which skills the agent actually uses and how

## Related

- [Import & Export Skills](/how-to/import-export-skills) — Import methods and conflict handling
- [Create an Agent](/how-to/create-agent) — Agent configuration guide
- [Build Custom Executor](/how-to/build-custom-executor) — Dedicated execution environments
- [Skills](/concepts/skills) — How the skill system works
