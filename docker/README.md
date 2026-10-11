# Container security

`lab-api/Dockerfile` uses a digest-pinned multi-stage Node image, `npm ci`, a pruned runtime dependency tree, an unprivileged UID and no build-time secrets. The runtime writes only below `/tmp`, so Compose and Kubernetes can make the root filesystem read-only.

Build with `make container-build`; scan with `make container-scan` when Docker and Trivy are installed. A clean image scan would not prove application-layer security, reachability or correct runtime policy.
