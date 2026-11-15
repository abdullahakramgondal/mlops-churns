# Module 7, Session 3: Answers (GitHub Actions + Hugging Face)

## 1. Lecture questions

- **What is CI/CD?** Every push automatically tests, trains, checks quality and deploys. No "works on my laptop".
- **Workflow structure:** a workflow = **trigger** (`on:`) -> **jobs** (machines) -> **steps** (commands). `needs:` orders jobs.
- **Quality gate:** a script that exits with code 1 if F1 is too low. The job fails, so the deploy job never runs.
- **Artifact handoff:** the deploy job uses exactly the model that passed the gate (upload artifact in `train`, download artifact in `deploy-hf`).
- **Secrets:** tokens are never written in code. They live in GitHub Settings (Secrets for tokens, Variables for non-secret values like the Space id).

## 2. Step 1: quality gate (TODO S3.1, `src/check_gate.py`)

```python
if f1 < min_f1:
    print(f"QUALITY GATE FAILED: f1={f1} < min_f1={min_f1}")
    sys.exit(1)
print(f"QUALITY GATE PASSED: f1={f1} >= min_f1={min_f1}")
```

| `min_f1` | Output | Exit code |
|---|---|---|
| 0.55 | `QUALITY GATE PASSED: f1=0.6293 >= min_f1=0.55` | 0 |
| 0.90 | `QUALITY GATE FAILED: f1=0.6293 < min_f1=0.9` | 1 |

`min_f1` was set back to 0.55 afterwards.

## 3. Step 4: workflow (TODO S3.2 to S3.7, `.github/workflows/ml-pipeline.yml`)

| TODO | What was done |
|---|---|
| S3.2 | Trigger: `push` on branches `main` and `dev`, plus `workflow_dispatch` (manual run from the Actions tab). `dev` was added because work is integrated on `dev`. |
| S3.3 | Step `Run DVC pipeline`: `dvc repro` (download -> prepare -> train -> evaluate). |
| S3.4 | Step `Quality gate`: `python -m src.check_gate`. If it fails, the job fails here. |
| S3.5 | `actions/upload-artifact@v4` with `name: release` and `path: release/`. |
| S3.6 | `needs: train` on the `deploy-hf` job, so it only runs after `train` succeeds. |
| S3.7 | `HF_TOKEN: ${{ secrets.HF_TOKEN }}` and `HF_SPACE: ${{ vars.HF_SPACE }}`. |

The file was moved with `git mv workflow_templates/ml-pipeline.yml .github/workflows/ml-pipeline.yml`. YAML was checked with `yaml.safe_load` (output: `YAML OK`). The Session 4 placeholder comment was left as is.

## 4. Step 5: push and watch

| Run | Trigger | Result | Duration |
|---|---|---|---|
| ML Pipeline #1 | Merge of PR #10 (workflow) into `dev` | **Success**. `train` green, `deploy-hf` skipped, artifact `release` (3.68 MB) | 57 s |
| ML Pipeline #2 | Merge of PR #12 (`min_f1: 0.90`) | **Failure** at the Quality gate step | 1 m 7 s |
| ML Pipeline #3 | Merge of PR #13 (`min_f1` back to 0.55) | **Success**, artifact `release` | 1 m 6 s |

Gate line in the logs of run #2: `QUALITY GATE FAILED: f1=0.6293 < min_f1=0.9` followed by `Process completed with exit code 1`.

## 5. Step 7: block a bad model

With `min_f1: 0.90`, job `train` failed at **Quality gate**. The steps after it (API tests, Build release folder, Upload release artifact) were skipped, no artifact was created and `deploy-hf` did not run. A bad model therefore never reaches deployment, and whatever was live before keeps running. Setting `min_f1` back to 0.55 and merging gave the green run #3.

**Discussion: in a real company, who should decide the value of `min_f1`? What if it is too low, or too high?**
It should be decided together by the data scientists and the business owner (product or domain team), because it reflects how much quality the business needs and what a wrong prediction costs. If it is set too low, weak models pass the gate and reach users. If it is set too high, good enough models are blocked, deployments stall and the team may be tempted to bypass the gate. It should be reviewed regularly and compared against a simple baseline model.

## 6. Hugging Face part (Steps 2, 3 and 6)

The HF deployment was **not repeated inside this repository**, with the instructor's permission. A Space deployed earlier with a Docker template is shown instead.

| Item | Answer |
|---|---|
| Existing Space project | Helmet Detection API (YOLO model `best.pt`, 22.5 MB), a different project from the churn API |
| Space page | https://huggingface.co/spaces/abdullahakramgondal7/Helmet_Detection_api |
| Live API URL | https://abdullahakramgondal7-helmet-detection-api.hf.space (Swagger at `/docs`) |
| Status | Running |
| Space SDK | Docker (the Space has a `Dockerfile`; container logs show Uvicorn running on port 7860) |
| Endpoints | `GET /` returns `{"message":"Helmet Detection API is running!"}`, `POST /detect` runs detection |
| Visibility | `<fill in: public/private>` |

**How the pipeline would deploy to HF (Steps 2, 3, 4):**

1. Create a Docker Space (for example `churn-api`) and a **Write** access token on huggingface.co.
2. In GitHub **Settings -> Secrets and variables -> Actions**: Secret `HF_TOKEN` = the token, Variable `HF_SPACE` = `your-hf-username/churn-api`.
3. After `train` passes, `deploy-hf` downloads the `release` artifact and runs `scripts/deploy_hf.py`, which calls `HfApi.upload_folder` to push `release/` to the Space. HF then builds the Docker image (2 to 5 minutes).
4. Smoke test: `python scripts/smoke_test.py https://username-churn-api.hf.space`, and open `/docs`. `/version` shows the git commit that built it.

**Why the `deploy-hf` job shows as skipped here:** it has `if: vars.HF_SPACE != ''`. The `HF_SPACE` variable is not set, so the job is skipped without any error. `HF_TOKEN` is a Secret, `HF_SPACE` is a Variable (Variables tab, not Secrets).

## 7. Wrap-up questions (Part C)

1. **Show your Actions history: one blocked run and one deployed run.**
   Run #2 is the blocked run (red, failed at Quality gate, `deploy-hf` skipped). Runs #1 and #3 are green runs that passed all `train` steps and created the `release` artifact. The final upload to Hugging Face was not done from this repo (see section 6).
2. **Show `/version` on your Space and match it to a commit.**
   `/version` reads `models/release.json`, which `build_release.sh` writes with `git_commit`, `built_at` and the metrics. Comparing `git_commit` with the latest commit on GitHub shows which code is live. Locally and in Docker it returns `{"release": "local-dev"}` because no release file exists there. The existing Helmet Detection Space is a separate project and has no `/version` endpoint (only `/` and `/detect`), so the commit matching is explained here on the churn API design instead of shown live. In the churn pipeline the `release` artifact contains this `release.json`, so a Space deployed from it would show the commit that built it.
3. **Why does the deploy job download an artifact instead of retraining?**
   Each job runs on a fresh machine. Retraining would waste time and could produce a slightly different model than the one that passed the gate. Downloading the artifact guarantees that exactly the tested model is deployed.

## 8. "Done when" checklist

- [ ] Green run that deployed to Hugging Face. **Skipped**: green run #1/#3 passed up to the artifact; HF shown from the existing Space.
- [x] Red run where the gate blocked deployment (run #2)
- [ ] Smoke test passes on the HF URL. **Skipped** for this repo; the existing Space is shown.

## 9. Notes on differences from the lab sheet

- The lab trigger is `push` on `main` only. This project also triggers on `dev` so the pipeline can be tested without pushing to `main`.
- The lab shows F1 around 0.6219 (original settings). This project uses the best settings from Session 1 (exp-04), so F1 is 0.6293.

## 10. Troubleshooting notes (from the lab and from our work)

| Problem | Fix |
|---|---|
| `deploy-hf` skipped on a green run | `HF_SPACE` variable missing (Variables tab, not Secrets) |
| 401/403 on upload | Token must be **Write** type; check `HF_SPACE` spelling |
| Space shows "Build error" | Space -> Logs; usually a Dockerfile problem |
| Workflow not starting | File must be in `.github/workflows/` and the trigger must match the branch |
| A PR was opened against `main` by mistake | Close it without merging; open a new one with base `dev` |
