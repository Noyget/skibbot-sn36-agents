# SN68 Nova Blueprint - Complete Architecture Analysis

## Overview
SN68 is a **drug discovery subnet** on Bittensor using ML-driven molecular optimization. The system runs competitive cycles where **miners** generate candidate molecules and **validators** score them.

---

## 1. CONFIG FILES STRUCTURE (`/config`)

### config.yaml
Runtime parameters for the mining algorithm:

```yaml
protein_selection:
  num_antitargets: 2                    # Number of anti-targets to select

molecule_validation:
  antitarget_weight: 0.9                # Scoring weight for antitargets
  entropy_min_threshold: 0.25           # Entropy filtering threshold
  min_heavy_atoms: 20                   # Minimum atomic constraints
  min_rotatable_bonds: 1
  max_rotatable_bonds: 10
  num_molecules: 100                    # Validation sample size

reaction_filtering:
  random_valid_reaction: true           # One random reaction per epoch

run:
  time_budget_sec: 900                  # Sandbox timeout (default 15 min)
  competition_interval_seconds: 86400   # Daily competitions (UTC-aligned)
  min_improvement_margin: 0.05          # 5% improvement required
  min_improvement_decay_rate: 0.2       # 20% decay per epoch
```

### config_loader.py
Simple YAML loader that parses config.yaml and returns a dictionary. Called by:
- `load_config()` - returns full dict
- `load_time_budget_sec()` - fast-path for just the timeout value

### __init__.py
Empty package marker.

---

## 2. HOW VALIDATORS RECEIVE MINERS' WORK - **PULL MODEL** (NOT PUSH)

### The Flow (Automatic, No Manual Push):

#### **Step 1: Miner Submission** (Miners)
- Miners upload their code via **Submission API** using the `utils/submission_uploader.py` SDK:
  ```python
  from utils.submission_uploader import submit_from_github_url
  
  result = submit_from_github_url(
      github_url="https://github.com/<owner>/<repo>",
      wallet_name="my_wallet",
      hotkey_name="my_hotkey",
      submission_name="dock-sense2",
  )
  ```
- **Must be signed by a hotkey registered on SN68** (the winning hotkey receives emissions)
- Code is stored in **MinIO** (S3-compatible archive) at: `s3://blueprint-code-archive/{epoch}/{uid}.tar.gz`
- One active submission slot per UID per epoch (re-submitting overwrites)

#### **Step 2: Scheduler Loop** (Validator)
Located in `neurons/validator/scheduler.py`:

```python
def main():
    interval = _get_interval_seconds()  # From config: 86400 seconds (1 day)
    
    while True:
        now_ts = time.time()
        next_ts = _next_aligned_ts(now_ts, interval)  # Next UTC-aligned time
        
        # Sleep until next competition window
        wait_s = max(0, int(next_ts - now_ts))
        
        # At scheduled time:
        run_competition(...)  # Spawns validator.py
```

**Key insight:** The scheduler **PULLS** the validator on a fixed UTC-aligned 24-hour schedule. It does NOT wait for miners to push anything.

#### **Step 3: Validator Execution** (neurons/validator/validator.py)
Each competition cycle:

1. **Fetches registered miner UIDs** from Bittensor chain
2. **For each UID**, calls `code_archive.py`:
   ```python
   # From validator.py
   repo_root = download_and_extract_snapshot(
       epoch=current_epoch,
       uid=miner_uid,
       work_root=Path("/data/miner_runs"),
       dest_dir=extract_dest,
   )
   ```

3. **Downloads miner code** from MinIO:
   ```python
   # From code_archive.py
   def download_and_extract_snapshot(epoch, uid, work_root, dest_dir):
       client = _create_minio_client()  # Uses MINIO_ACCESS_KEY, SNAPSHOT_S3_ENDPOINT
       key = f"{int(epoch)}/{int(uid)}.tar.gz"  # Object key format
       
       client.fget_object(SNAPSHOT_BUCKET, key, archive_path)
       tar.extractall(path=dest_dir)
       
       repo_root = _resolve_repo_root(dest_dir)  # Finds miner.py
       return repo_root
   ```

4. **Executes miner in Docker sandbox** (sandbox/runner.py):
   ```python
   def run_container(workdir, outdir, period, uid):
       timeout_seconds = load_time_budget_sec()  # From config.yaml
       
       cmd = [
           "docker", "run", "--rm",
           "--read-only",
           "--cap-drop=ALL",
           "--network=none",  # No network access
           "--tmpfs", "/tmp:rw,noexec,nosuid,nodev",  # Temp only
           "-v", f"{host_workdir}:/workspace:ro",  # Input (read-only)
           "-v", f"{host_outdir}:/output:rw",      # Output (write)
           SANDBOX_IMAGE_TAG,
       ]
       
       proc = subprocess.Popen(cmd, ...)
       rc = proc.wait(timeout=timeout_seconds)
   ```

5. **Collects miner output** from `/output/result.json`:
   ```json
   {
     "molecules": ["rxn:4:…", "rxn:5:…"]
   }
   ```

6. **Scores and ranks** all miner submissions (scoring.py)
7. **Applies weights** to the winning miner's UID (weights.py)

#### **Step 4: Weight Application** (Emission to Winner)
The weights loop runs every 60 minutes:
```python
def _weights_loop(stop_event, cfg):
    winner_path = Path("/data/results/winner.json")
    
    while not stop_event.is_set():
        winner = _read_json(winner_path)
        target_uid = winner.get("emission_target_uid")
        apply_weights(target_uid)  # Send emissions to winner
```

---

## 3. MINER REQUIREMENTS

### Must Have:
- **`miner.py` at repo root** — executed as `python /workspace/miner.py`
- **Read input from `/workspace/input.json`** — contains challenge parameters
- **Write output to `/output/result.json`** — with reaction-formatted molecules only

### Input Format (`input.json`):
```json
{
  "time_budget_sec": 900,
  "protein_selection": {...},
  "molecule_validation": {...},
  "reaction_filtering": {...}
}
```

### Output Format (`result.json`):
```json
{
  "molecules": ["rxn:4:SMILES_STRING", "rxn:5:SMILES_STRING"]
}
```

### Sandbox Constraints:
- **Read-only root filesystem** (can only write to `/tmp`, `/output`)
- **No network access** (isolated Docker container)
- **Fixed time budget** (default 900s; timeout = forced exit)
- **Read-only SQLite** (for combinatorial DB):
  ```python
  sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
  ```

---

## 4. FILE UPLOAD/SUBMISSION FLOW

### Miners Upload Code:
```python
from utils.submission_uploader import submit_from_github_url

result = submit_from_github_url(
    github_url="https://github.com/your/repo",
    wallet_name="your_coldkey",
    hotkey_name="your_hotkey",
    submission_name="my_algo_v2",
)

print(result.status_code, result.request_id, result.body)
```

**Requirements:**
- Hotkey must be registered on SN68 (UID must exist on-chain)
- Only one active submission per UID per epoch
- Re-submitting in same epoch overwrites previous code
- Code is signed by the hotkey

### API Endpoint:
- Base: `SUBMISSION_API_URL` (from `.env`: `https://submission-api.metanova-labs.ai`)
- Endpoint: `POST /submit` (handles signature verification + tarball upload to MinIO)

---

## 5. VALIDATOR ARCHITECTURE COMPONENTS

| File | Purpose |
|------|---------|
| `validator.py` | Main validator logic: fetches miners, executes them, scores submissions |
| `scheduler.py` | Cron-like scheduler that runs validator on UTC-aligned 24h intervals |
| `code_archive.py` | MinIO client: downloads & extracts miner code from S3 |
| `sandbox/runner.py` | Docker executor: runs miner in isolated, sandboxed container |
| `scoring.py` | Scores miner outputs (molecule quality, binding affinity, etc.) |
| `ranking.py` | Ranks miners by score |
| `weights.py` | Applies Bittensor weights to winning miner UIDs (emissions) |
| `save_data.py` | Persists results to `/data/results/` |
| `validity.py` | Validates miner output format & molecule structure |
| `commitments.py` | Tracks miner commitments / metadata |

---

## 6. ENVIRONMENT & CONFIGURATION

### Validator `.env`:
```bash
BT_WALLET_COLD=your_cold_wallet_name
BT_WALLET_HOT=your_hotkey_name
SUBTENSOR_NETWORK=finney
SNAPSHOT_S3_ENDPOINT=s3.metanova-labs.ai          # MinIO endpoint
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
SUBMISSION_API_URL=https://submission-api.metanova-labs.ai
SUBMISSION_API_KEY=your_submission_read_api_key
BT_WALLETS_DIR=$HOME/.bittensor/wallets           # Optional
```

### Key Paths:
- **Miner artifacts:** `./data/miner_runs/` (work directories)
- **Validator results:** `./data/results/` (scores, winner.json)
- **Docker image:** `urdof7/miner-sandbox:latest`
- **MinIO bucket:** `blueprint-code-archive`

---

## 7. COMPETITION CYCLE TIMELINE

```
00:00 UTC (Day N)
  ↓
[Validator waits 24h]
  ↓
00:00 UTC (Day N+1) — Scheduler triggers validator
  ↓
Validator fetches all registered miner UIDs
  ↓
For each miner UID:
  - Download code from MinIO: s3://blueprint-code-archive/{epoch}/{uid}.tar.gz
  - Extract to /data/miner_runs/{run_id}/
  - Copy input.json (challenge params)
  - Run Docker sandbox (timeout: time_budget_sec = 900s)
  - Collect /output/result.json
  ↓
Score all submissions
  ↓
Determine winner (highest score)
  ↓
Save winner to /data/results/winner.json
  ↓
Weights loop (every 60 min) picks up winner, applies emissions to winner's UID
  ↓
[Next 24h cycle]
```

---

## 8. KEY INSIGHT: **PULL vs PUSH MODEL**

### ❌ **NOT** a push model:
- Miners do NOT push their work every cycle
- Miners do NOT have a server running 24/7
- Miners do NOT need to listen for validator requests

### ✅ **IS** a pull model:
- Miners **submit code once** via the Submission API
- Code is archived in MinIO with their UID as the key
- **Validators pull miner code on a fixed schedule** (every 24h UTC-aligned)
- Each competition, validators fetch the LATEST version of each UID's submission
- If a miner hasn't updated their submission, validators use the old version

### Workflow:
1. **Miner uploads code** → MinIO stores it at `{epoch}/{uid}.tar.gz`
2. **Validator waits 24h**
3. **At scheduled time, validator pulls** all miners' latest code
4. **Validator executes locally in Docker**
5. **Validator scores and posts weights**

---

## 9. DISCOVERY PHASE (Your Current Status)

From your health check:
- ✅ Miner running fine (PID 3227918, CPU 22%, RAM 232MB)
- ✅ Registered on subnet 68 (coldkey + hotkey setup correct)
- ⏳ **No validator traffic in logs yet** = **Waiting for 00:00 UTC competition cycle**

**What happens next:**
1. At **00:00 UTC tomorrow**, the validator scheduler triggers
2. Validator fetches your UID's latest submission from MinIO
3. Validator runs your miner.py in the sandbox
4. Validator scores your molecules
5. Your UID receives weights (if you score well)

**Until then:** Your miner is correctly registered and **waiting for the next cycle**. No action needed—the system automatically discovers you when the competition runs.

---

## 10. SUMMARY TABLE

| Aspect | Details |
|--------|---------|
| **Model** | Pull-based (validators fetch miners) |
| **Submission** | One-time code upload via Submission API → MinIO |
| **Discovery** | Automatic at 00:00 UTC each day |
| **Execution** | Docker sandbox (isolated, read-only, 900s timeout) |
| **Scoring** | Binding affinity, entropy, molecular validity |
| **Emission** | Weights applied hourly to current winner's UID |
| **Miner Requirements** | miner.py, read /workspace/input.json, write /output/result.json |
| **Validator Arch** | Scheduler → Validator.py → CodeArchive → Runner → Scoring → Weights |

