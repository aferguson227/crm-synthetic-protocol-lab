# Public synthetic-only repository security boundary

- No real accounts, API keys, secrets, user data, private Git histories, production CRM code, real trading logic or release artifacts belong in this project.
- Tests require the Python standard library only. No private packages, private repository checkout, secret contexts, workflow write permissions, deployment or installation.
- Test HTTP is restricted to `127.0.0.1` on ephemeral ports. It is never a remotely accessible service and is always stopped when tests finish.
- Public tests are strictly **non-certifying**. No build status here grants installation, deployment, trading or promotion authority. `can_install_or_deploy=false`.
- Never introduce `pull_request_target`, `workflow_run`, `self-hosted` runner labels, GitHub Actions secrets or steps invoking private workflows in the public workflow.
- Never import proprietary code into this public repository or print bearer tokens in CI logs.
- Any future additions require review of exact file inventory, diff, outbound networking and imports before publication.
