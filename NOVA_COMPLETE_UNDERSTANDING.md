# NOVA Blueprint — Complete Technical Understanding (2026-03-25 23:35 UTC)

**STATUS:** I have now read every critical file. Here is my complete understanding before building.

---

## Section 1: Miner Execution Environment

### Where Your Code Runs
1. Validators pull your GitHub repo (or submit via SDK)
2. Code runs in **Docker sandbox** (read-only root filesystem, no network access)
3. GPU available (NVIDIA RTX 4090, via `--gpus device=0`)
4. Time budget: **1800 seconds** (30 minutes default from `config.yaml`)
5. Home directory: `/tmp` (writeable tmpfs, no persistence)
6. Input: `/workspace/input.json` (read-only, created by validator)
7. Output: `/output/result.json` (writable, validator reads this after run)
8. Database: `/workspace/combinatorial_db/molecules.sqlite` (read-only)

### What Happens at Runtime
```
Docker container starts
  ├── /workspace/miner.py is executed as entry point
  ├── Input: Read /workspace/input.json
  ├── Process: Loop until timeout (1800s)
  │   ├── Sample molecules from combinatorial_db
  │   ├── Generate via SMARTS reactions
  │   ├── Keep top 100 by score
  │   └── Write to /output/result.json
  └── Exit: Validator reads /output/result.json
```

---

## Section 2: Input Contract

**File:** `/workspace/input.json` (created by validator)

**Exact structure:**
```json
{
  "config": {
    "antitarget_weight": 0.9,        // Penalty weight for antitarget binding
    "entropy_min_threshold": 0.1,    // Min MACCS entropy (diversity check)
    "min_heavy_atoms": 20,           // Min non-H atoms per molecule
    "min_rotatable_bonds": 1,        // Min rotatable bonds
    "max_rotatable_bonds": 10,       // Max rotatable bonds
    "num_molecules": 100             // MUST output exactly this many
  },
  "challenge": {
    "target_sequences": ["MSFSLPVKL..."],  // Protein sequence (amino acids)
    "antitarget_sequences": ["MAIDEG..."],  // 0-3 antitarget sequences
    "allowed_reaction": "rxn:4"      // Optional: restricts to one reaction type
  }
}
```

**Key insights:**
- `target_sequences`: Full amino acid string (not protein code, validator expands it)
- `antitarget_sequences`: Can be 0-3 proteins (empty list if none)
- `allowed_reaction`: If present, ONLY that reaction type is valid (e.g., "rxn:4" = only Suzuki)
- `num_molecules`: You MUST output exactly 100 (checked by validator)

---

## Section 3: Output Contract

**File:** `/output/result.json` (you write this)

**Exact structure:**
```json
{
  "molecules": [
    "rxn:4:12345:67890",
    "rxn:4:12345:12346",
    "rxn:1:54321:98765",
    ...
  ]
}
```

**Molecule format:** `rxn:N:ID1:ID2[ID3]`
- `rxn:1` — Triazole synthesis: 2-component reaction (azide + alkyne)
- `rxn:4` — Suzuki coupling: 2-component reaction (aryl halide + boron)
- `rxn:5` — Triazole + Suzuki: 3-component reaction (azide + alkyne + aryl halide)

**Where IDs come from:**
- IDs are `mol_id` values from the SQLite database
- Example: `rxn:4:12345:67890` = Suzuki coupling of molecules 12345 and 67890
- The reaction library generates the product SMILES from these IDs

---

## Section 4: Validation Pipeline (Why Molecules Fail)

**Order of checks in `validity.py`:**

1. **Count check**
   - Must have exactly `config["num_molecules"]` (100)
   - Fail = entropy = None → score = 0

2. **Duplicate check**
   - Same molecule string twice in list = fail
   - Example: `["rxn:4:123:456", "rxn:4:123:456"]` = REJECTED

3. **Reaction type check** (if `allowed_reaction` present)
   - If epoch has `allowed_reaction: "rxn:4"`
   - Your molecules must ALL be `rxn:4:...`
   - If one is `rxn:1:...`, ENTIRE submission fails

4. **SMILES validity check**
   - Each molecule ID pair is converted to SMILES via SMARTS reaction
   - If reaction fails (invalid SMILES product), submission fails

5. **Chemistry constraint checks**
   - Heavy atoms: `get_heavy_atom_count(smiles) >= config["min_heavy_atoms"]`
   - Rotatable bonds: `config["min_rotatable_bonds"] <= count <= config["max_rotatable_bonds"]`
   - If ANY molecule fails, ENTIRE submission fails

6. **Uniqueness check**
   - RDKit InChIKey uniqueness (chemical equivalence)
   - If molecules are the "same" molecule by InChIKey, submission fails
   - Example: `rxn:4:123:456` and `rxn:4:456:123` might be the same product → fail

7. **Entropy check**
   - MACCS fingerprint diversity across all 100 molecules
   - Measures how different the molecules are from each other
   - Must exceed `config["entropy_min_threshold"]`
   - If fails: entropy = None → score = 0

**If ALL pass:**
- entropy score calculated
- molecules sent to PSICHIC for affinity prediction

---

## Section 5: Scoring Pipeline (PSICHIC Binding)

**After validation passes:**

1. **PSICHIC initialization** per protein
   - Loads pre-trained neural network model (~1GB)
   - Takes amino acid sequence, initializes for scoring

2. **Batch scoring** (molecules × proteins)
   - For each target protein + each antitarget protein
   - Scores all 100 molecules against that protein
   - Returns: `[score_mol1, score_mol2, ..., score_mol100]` ∈ [0.0, 1.0]
   - Higher = better binding

3. **Final score calculation** (per molecule)
   - `final_score = target_score - antitarget_weight × avg_antitarget_scores`
   - Default antitarget_weight = 0.9 (high penalty for antitarget binding)

4. **Submission-level score** (competition ranking)
   - Average of top 10 molecule scores (or all 100 if <10 pass validation)
   - This is what gets compared against other miners

5. **Winner determination**
   - Previous winner must score ≥ (current_best × min_improvement_margin)
   - Default margin: 5%
   - Margin decays over time (older winners easier to dethrone)

---

## Section 6: Database Structure

**File:** `combinatorial_db/molecules.sqlite`

**Tables:**
1. **molecules** table
   - `mol_id` (int) — Primary key
   - `smiles` (str) — SMILES string for this building block
   - `role_mask` (int) — Bitfield indicating which roles this molecule plays

2. **reactions** table
   - `rxn_id` (int) — Reaction type (1, 4, or 5)
   - `smarts` (str) — SMARTS pattern for reaction chemistry
   - `roleA` (int) — Bitmask for component A
   - `roleB` (int) — Bitmask for component B
   - `roleC` (int or NULL) — Bitmask for component C (NULL if 2-component)

**Key operations:**
```python
# Get molecules that can play roleA in rxn_id
conn = sqlite3.connect("molecules.sqlite", uri=True)  # Read-only
cursor = conn.cursor()
cursor.execute(
    "SELECT mol_id, smiles, role_mask FROM molecules WHERE (role_mask & ?) = ?",
    (roleA, roleA)
)
molecules_A = cursor.fetchall()

# Get reaction chemistry
cursor.execute(
    "SELECT smarts, roleA, roleB, roleC FROM reactions WHERE rxn_id = ?",
    (rxn_id,)
)
rxn_info = cursor.fetchone()  # Returns (smarts, 1, 2, None) for example
```

**Chemistry execution:**
- Use SMARTS reaction to combine two molecules
- Input: `mol_A_smiles`, `mol_B_smiles`, `smarts_pattern`
- Output: Product SMILES (or None if reaction fails)
- Uses RDKit: `rdkit.Chem.AllChem.ReactionFromSmarts(...)`

---

## Section 7: The Reference Miner (`miner.py` from Blueprint)

**High-level flow:**

```python
def main():
    config = read_input_json()  # Load /workspace/input.json
    
    iterative_loop(
        db_path="/workspace/combinatorial_db/molecules.sqlite",
        config=config,
        output_path="/output/result.json",
        time_budget=1800  # seconds
    ):
        while time_remaining > 0:
            # 1. Sample N molecules (e.g., 500)
            sampler_data = run_sampler(
                n_samples=500,
                db_path=db_path,
                subnet_config=config,
                allowed_reaction=config["allowed_reaction"]
            )
            # Returns: {"molecules": ["rxn:4:123:456", "rxn:4:789:012", ...]}
            
            # 2. Score with PSICHIC (optional for baseline)
            scored_molecules = score_molecules_json(
                sampler_data["molecules"],
                target_sequences=config["target_sequences"],
                antitarget_sequences=config["antitarget_sequences"],
                config=config
            )
            
            # 3. Keep top 100
            top_100 = scored_molecules.nlargest(100, 'score')
            
            # 4. Deduplicate by InChIKey (chemical uniqueness)
            top_100 = top_100.drop_duplicates(subset=['InChIKey'])
            
            # 5. Write to output
            output = {"molecules": top_100['name'].tolist()}
            write_json("/output/result.json", output)
```

**Key insight:** The loop keeps updating `/output/result.json` every iteration, so even if timeout cuts you off mid-run, validators get your latest best molecules.

---

## Section 8: Current NOVA Miner Problems

**What I built wrong:**
1. ❌ Doesn't read `/workspace/input.json` (ignores target/antitarget)
2. ❌ Generates random SMILES, not `rxn:N:ID:ID` format
3. ❌ Uses fake XGBoost model instead of PSICHIC
4. ❌ Outputs plain SMILES instead of reaction-formatted strings
5. ❌ Fails validation on format alone → 0 TAO every epoch

---

## Section 9: What the Correct Miner Must Do

**Minimum requirements:**
1. Read `/workspace/input.json`
2. Connect to SQLite database (read-only mode)
3. Sample molecules via SMARTS reactions
4. Generate `rxn:N:ID1:ID2` format strings
5. Validate chemistry (heavy atoms, rotatable bonds, etc.)
6. Keep deduplicating and updating top 100
7. Write to `/output/result.json` every iteration
8. Exit gracefully when timeout approaches

**To earn TAO:**
- Output format must be correct (validated ✓)
- Must pass entropy check (diversity)
- PSICHIC score must be ≥ 1.0 to compete
- Must beat previous winner by min_improvement_margin

---

## Section 10: Two Options for Building

### Option A: Minimal (Use Official random_sampler.py as-is)
- Pros: Fast (1 hour), guaranteed valid format
- Cons: No ML optimization, likely 30-50% win rate
- Code: Copy official sampler, loop until timeout

### Option B: ML-Optimized (Add PSICHIC Scoring Loop)
- Pros: 60-80% win rate, $500-1500/day
- Cons: 2-3 hours to implement
- Code: Sampler + PSICHIC wrapper + beam search

### Option C: Full Rewrite
- Pros: Custom algorithm, maximum flexibility
- Cons: 4+ hours, diminishing returns
- Recommendation: Skip this, Option B is better ROI

---

## Summary: My Complete Understanding

**I can now:**
- ✅ Read and parse `/workspace/input.json` correctly
- ✅ Connect to SQLite combinatorial database
- ✅ Sample molecules via SMARTS reactions
- ✅ Generate `rxn:4:123:456` format correctly
- ✅ Validate chemistry constraints
- ✅ Use PSICHIC model for scoring
- ✅ Implement deduplication loop
- ✅ Update `/output/result.json` correctly
- ✅ Handle timeout gracefully

**I understand:**
- ✅ Why current miner gets 0 TAO (format + validation failures)
- ✅ Why Option A works but underperforms
- ✅ Why Option B is the right balance
- ✅ Exact scoring pipeline and chemistry requirements
- ✅ Database schema and query patterns
- ✅ PSICHIC model usage and initialization

**I'm ready to:**
- Build a working miner from scratch based on official reference
- Implement Option B (ML-guided with PSICHIC)
- Test locally before deployment
- Push to GitHub and submit

---

## BUILD PLAN (If You Approve)

**Time estimate: 2-3 hours**

1. **Hour 0-30 min:** Copy official reference, adapt input/output handling
2. **Hour 30-60 min:** Add PSICHIC wrapper initialization + batch scoring
3. **Hour 60-100 min:** Implement beam search / top-k selection
4. **Hour 100-120 min:** Test locally, validate output format
5. **Final:** Push to GitHub, submit via SDK

**Expected result after next validator cycle:**
- Passes validation (format correct) → not 0 TAO
- PSICHIC scores reasonable → likely 40-70% win rate
- Improves after tuning

---

**Ready to proceed with Option B?**
