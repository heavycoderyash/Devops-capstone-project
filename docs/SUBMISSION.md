# Trivy security scan

Screenshot: [`screenshots/m6-trivy-output.png`](screenshots/m6-trivy-output.png)

## What Trivy scanned

On every pipeline run, Trivy scanned both container images before they were pushed to GHCR:

- the **operating-system packages** of each image (Debian in the Python backend image, Alpine in the
  Nginx frontend image), and
- every **Python library** installed in the backend image.

The pipeline fails if Trivy finds any HIGH or CRITICAL vulnerability that already has a fix available.

## What the result means

The final scans are **clean**: no fixable HIGH or CRITICAL vulnerabilities were found, so the gate
passed and both images were pushed.

The scan was not clean at first. Building the project, the backend image failed on 4 HIGH CVEs, for
example CVE-2025-47273, a path-traversal bug in `setuptools`, and two `urllib3` CVEs. All of them came
from libraries bundled inside `pip`, not from the application's own code. `pip` isn't needed once the
dependencies are installed, so the Dockerfile now removes it from the final image, and the scan has
been clean since.

A clean result means there were no *known, fixable* HIGH/CRITICAL CVEs at the moment of the scan. It is
not a guarantee of security. That is why the project also runs containers as non-root users, gives the
CI token only the permissions each job needs, and uses a deploy identity that can do nothing in AWS
except look up the cluster.
