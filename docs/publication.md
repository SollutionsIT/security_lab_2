# Publication checklist

Only publish this standalone sanitized directory, never its parent workspace or a customer's repository. Use new history: text replacement in the working tree does not clean old commits.

1. Read `LICENSE` and `NOTICE.md`. This is source-available/non-commercial, not OSI open source. Obtain legal review if commercial enforcement is important; prior valid license grants cannot be revoked retroactively.
2. Run `make publication-check secrets`. The preflight reviews tracked and non-ignored untracked working-tree candidates, rejects force-added ignored files and links, checks PNG metadata and secret-scans a temporary copy. Review screenshots and business information manually: a denylist and a secret scanner are not complete personal-data detectors.
3. Verify no `.env`, local reports, IDE data, private notes, real endpoints/tokens or dependency directories will be staged. Generated runtime reports are intentionally ignored.
4. Keep private interview preparation outside this repository. `docs/15-interview-guide.md` is a public English technical guide, not personal interview notes.
5. Initialize fresh Git metadata if needed; configure commit identity explicitly using the Sollutions brand and a valid hosting-provider noreply address. Do not guess an address or expose your personal email.
6. Review the exact staged files/diff and remote destination. Obtain approval before external upload. Public visibility makes new uploads immediately readable.
7. After publishing, inspect files through GitHub and inspect the first Actions run. Update the ledger with real remote results and enable appropriate required checks.

No screenshot in this repository represents a GitHub Actions execution. Local preparation is not proof of remote execution or publication.

## Public portfolio readiness

This repository is ready to present as a working synthetic AppSec/DevSecOps reference lab, not as a fully verified production security platform. `PROJECT_STATUS.md` and the reviewed files under `docs/evidence/` are intentionally public: they retain dated, sanitized results and distinguish actual local execution from configured integrations. Do not replace them with raw reports or customer evidence. `gitignore_example` is a readable example only; Git applies `.gitignore`, not this example filename.

Recommended publication sequence: review the first commit; push to the new private repository; inspect the actual native GitHub Actions result on canonical Python 3.13; fix failures and retain the run URL/artifacts; then deliberately change visibility after a final data review. Additional scanner/platform jobs remain separately marked until actually executed. The first remote run cannot be verified before the code is pushed; no script performs that push or changes visibility.

Production readiness is a separate goal requiring the deployment-specific controls and validation described in the adoption guide. Remaining dev-dependency warnings and unexecuted integrations must stay visible, not be described as a clean audit. Confirm your right to publish any material originating from a client; this public tree must remain limited to the independent synthetic implementation and reviewed, non-customer evidence.

## Safe transfer without old history

Prefer `make publication-bundle` to copying the whole working directory. It creates `reports/publication/company-security-lab.tar.gz` containing the checked working-tree snapshot only. It excludes ignored data and `.git`, strips file ownership/xattrs/personal path metadata, and refuses to overwrite a previous export. The local `reports/publication/manifest.json` lists candidate paths and SHA-256 hashes. The archive and manifest are ignored, not portfolio source.

Extract into an empty destination working tree or copy its contents into a separately initialized empty repository. Keep that destination's own `.git`; never import the source `.git`. Check that existing destination files will not be overwritten. Configure only the new intended remote, not the customer's remote. A fresh folder does not clean a populated remote, old clones, forks or Actions logs.

`.gitignore` excludes environment files, credentials, private keys, cloud/kube authentication, IaC state and populated variables, dumps, backups, private office documents, assistant history, dependency caches and raw evidence. Required synthetic `.env.example` files, Kubernetes placeholder secrets, reviewed PNGs and the inert test PDF remain included. Do not populate templates with real values. Public Markdown under `docs/`, including the English technical interview guide, is intentional.

## Review before your first commit

Open the destination root in your IDE, not its parent workspace. Suggested commands, run from the destination:

```sh
git status --short
git remote -v
git log --all --oneline
git diff --cached --stat
git diff --cached --check
git diff --cached
```

For a new repository without commits, an empty history is expected. Staged files are a review proposal, not a published commit. Inspect their content in the IDE's Commit view; `.idea` must not appear there. The preflight checks working-tree bytes, not previously staged blob contents: rerun checks and restage any subsequent edits before commit. Do not use `git add -f` or disable secret scanning.

Use `Sollutions` as the local Git author name and your account's verified GitHub noreply address. Obtain the exact address from GitHub Settings → Emails; do not invent it. Local Git identity settings do not travel with copied files, and repository licensing does not hide commit metadata.

Only after review, create the first commit in the IDE or terminal. Confirm it has no parent, check its author/email and exact files, and push only to the independently verified empty destination. Publishing and changing visibility require a deliberate user action; no script here pushes or changes visibility.

## Credential incident boundary

No real credential found by a scanner is not proof that historical credentials were never exposed. If real credentials were ever committed or shared, revoke/rotate them through the owning provider. This preparation does not rotate customer credentials or clean old repositories, clones, forks or cached references.

References: [GitHub ignore behavior](https://docs.github.com/en/get-started/git-basics/ignoring-files) and [removing sensitive data / rotating leaked credentials](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
