# Kubernetes security

`base/` contains the least-privilege workload; `hardened/` adds network isolation and disruption protection. Render with `kubectl kustomize kubernetes/hardened`. A populated runtime Secret and real registry image are deliberately not committed.
