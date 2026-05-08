# Secrets directory

Do not store secret values in this directory.

Allowed examples:

```yaml
credential_refs:
  github_token: env:GITHUB_TOKEN
  web_api_key: keyring:hisys/web_api_key
```

Prohibited examples:

```yaml
password: [REDACTED]
api_key: [REDACTED]
```
