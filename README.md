# gitlab-pipeline-app

## Prepare Secrets

```bash
# Create base64 encoded values for secrets
echo -n 'your-gitlab-access-token' | base64
echo -n 'https://gitlab.com' | base64
echo -n 'your-group-id' | base64
```
