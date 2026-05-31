# Dremio Lakehouse Authentication Setup

**Last verified:** 2026-05-30
**Tool version/release checked:** JGI Lakehouse Dremio live service (not versioned); Dremio REST API docs current [26.x]; local token helper script has no upstream release.
**Official docs/manual:** https://docs.dremio.com/current/security/authentication/personal-access-tokens/ ; https://docs.dremio.com/current/reference/api/sql/ ; https://docs.dremio.com/current/reference/api/job/job-results/
**Release/source:** `skills/jgi-lakehouse/scripts/get_dremio_token.sh`; `skills/jgi-lakehouse/scripts/rest_client.py`; https://lakehouse.jgi.lbl.gov

## Endpoints
- Lakehouse URL: https://lakehouse.jgi.lbl.gov

## Generate a Token

The public Lakehouse UI is protected by Cloudflare Access. Use a Dremio Personal Access Token (PAT) when the UI exposes PAT management for your account; otherwise use the local `get_dremio_token.sh` helper from an internal network or SSH tunnel to create a short-lived login token.

### 1. Access Dremio UI
1. Open browser and navigate to: https://lakehouse.jgi.lbl.gov
2. Authenticate through Cloudflare Access (SSO)
3. Login with your JGI credentials

### 2. Generate PAT if available
1. Click your profile icon (top right)
2. Go to **Account Settings**
3. Navigate to **Personal Access Tokens** tab
4. Click **"New Token"**
5. Set token properties:
   - **Label**: "CLI API Access" (or your preferred name)
   - **Expiration**: Choose a duration allowed by the deployment policy
6. Click **Create**
7. **IMPORTANT**: Copy the token immediately (shown only once)

### 3. Store Token Securely
Run this command with your generated token:

```bash
echo "YOUR_TOKEN_HERE" > ~/.secrets/dremio_pat
chmod 600 ~/.secrets/dremio_pat
```

### 4. Configure Environment
Add to your shell profile (~/.bashrc or ~/.zshrc):

```bash
# Dremio Lakehouse Authentication
export DREMIO_PAT=$(cat ~/.secrets/dremio_pat 2>/dev/null)
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### 5. Verify Access
Test the token (from LBNL network or SSH tunnel):

```bash
uv run --with requests python << 'EOF'
import os
import sys

sys.path.insert(0, "scripts")
from rest_client import show_schemas

token = os.getenv("DREMIO_PAT")
if not token:
    token = open(os.path.expanduser("~/.secrets/dremio_pat")).read().strip()
    os.environ["DREMIO_PAT"] = token

schemas = show_schemas()
print("✓ Successfully connected to JGI Lakehouse!")
print(f"Schema count: {len(schemas)}")
EOF
```

## Alternative: SSH Tunnel (If on JGI Network)

If you have SSH access to JGI internal network:

```bash
# Create tunnel
ssh -L 9047:lakehouse-1.jgi.lbl.gov:9047 your-jgi-server.lbl.gov

# Then in another terminal, use the token script
export DREMIO_HOST=localhost
./scripts/get_dremio_token.sh <username>
```

## Security Notes
- Never commit ~/.secrets/* to git (already gitignored)
- Token file permissions are 600 (read/write owner only)
- Rotate tokens according to the deployment's token lifetime and local security policy
- Revoke tokens from Dremio UI if compromised

## Operational Pitfalls (Important)

### 1. Set `DREMIO_PAT` before importing `rest_client`

If your script does:

```python
from rest_client import query
os.environ["DREMIO_PAT"] = token
```

you may get auth failures depending on client version. Always set token first:

```python
os.environ["DREMIO_PAT"] = token
from rest_client import query
```

### 2. Token lifetime depends on how token was created

- **Dremio UI PAT**: configurable expiration when PATs are enabled for the deployment
- **`get_dremio_token.sh` (`/apiv2/login`)**: short-lived token (~30 hours)
