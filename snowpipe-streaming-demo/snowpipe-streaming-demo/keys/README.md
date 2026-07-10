# Key directory

Generate local keys here:

```powershell
openssl genrsa 2048 |
  openssl pkcs8 -topk8 -inform PEM -out keys\rsa_key.p8 -nocrypt

openssl rsa -in keys\rsa_key.p8 -pubout -out keys\rsa_key.pub
```

The `.gitignore` prevents common key files from being committed. Always verify with `git status` before pushing.
