# SYNTH-001 — Attachment ownership was missing during implementation

- **Evidence state:** FIXED / RETESTED IN SYNTHETIC LAB
- **Asset:** synthetic attachment
- **Source:** implementation review followed by unit and Python integration regression
- **Preconditions:** authenticated user knows another synthetic `storedName`
- **Trust boundary:** TB-02 API authorization boundary
- **Impact:** confidentiality; cross-owner file read
- **Severity / priority / confidence:** High / P1 during implementation / High
- **Remediation:** bind attachment owner server-side; permit owner or admin; conceal denial with 404; emit structured denial event
- **Retest:** `UploadService` cross-owner test and `test_valid_file_uses_server_name_and_safe_download_headers`
- **Residual risk:** in-memory metadata and local disk do not model object-store ACL drift

Only synthetic lab behavior is represented; no customer or production endpoint was tested.
