# Security Policy

## Scope

Wayward Stone is a **research prototype**. It is not designed for production deployment or handling sensitive user data. Use at your own risk.

## Reporting a Vulnerability

If you discover a security issue, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email: **phi9t@users.noreply.github.com** with a description of the vulnerability.
3. Allow reasonable time for a fix before public disclosure.

## Known Considerations

- **Docker permissions**: The audiobook container workflows run with `--gpus=all` and `--net=host`. Review `audiobook/zephyr_launch_container.sh` before running on shared infrastructure.
- **HF_TOKEN handling**: HuggingFace tokens are passed via Docker environment variables. Never commit tokens to the repository. The `.gitignore` excludes `.env` files, but always verify before pushing.
- **No authentication**: There is no auth layer on any service in this repo. Do not expose any component to untrusted networks.
