# Public Synthetic CRM Protocol Lab

This independent public repository contains **synthetic-only** HTTP/session security fixtures. It is not the private Crypto Regime Manager application, installer, phone-link, release candidate, or trading system. No private source, Git history, credentials, trading logic or runtime data may be added.

All fixtures use the Python standard library. The HTTP test server binds only to disposable local `127.0.0.1` ports; no exchange or external network access is required. `can_install_or_deploy` is always `false`.

## Offline checks

`python -S -m unittest discover -s tests -t . -v`

The public workflow runs these same checks with Linux Python 3.11, Linux Python 3.13 and hosted Windows Python 3.11. Passing public tests provides development feedback only. It **never** certifies private CRM Stage 103 and never enables installation, deployment or trading authority.

See [SECURITY.md](SECURITY.md) for the publishing and isolation boundary. The private CRM must undergo separate mandatory exact-head security and release certification.
