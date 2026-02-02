# Dremio Lakehouse Authentication Setup

## Endpoints
- Lakehouse URL: https://lakehouse.jgi.lbl.gov

## Generate Personal Access Token (Recommended)

The lakehouse is protected by Cloudflare Access. To use the API programmatically:

### 1. Access Dremio UI
1. Open browser and navigate to: https://lakehouse.jgi.lbl.gov
2. Authenticate through Cloudflare Access (SSO)
3. Login with your JGI credentials

### 2. Generate PAT
1. Click your profile icon (top right)
2. Go to **Account Settings**
3. Navigate to **Personal Access Tokens** tab
4. Click **"New Token"**
5. Set token properties:
   - **Label**: "CLI API Access" (or your preferred name)
   - **Expiration**: Choose duration (recommend 90 days or longer)
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
Test the token:

```bash
python3 << 'EOF'
import os
import pyarrow.flight as flight

token = os.getenv("DREMIO_PAT")
if not token:
    token = open(os.path.expanduser("~/.secrets/dremio_pat")).read().strip()

client = flight.FlightClient("grpc+tls://lakehouse.jgi.lbl.gov:443")
headers = [(b"authorization", f"Bearer {token}".encode("utf-8"))]
options = flight.FlightCallOptions(headers=headers)

# Test query
info = client.get_flight_info(
    flight.FlightDescriptor.for_command("SHOW SCHEMAS"),
    options
)
print("✓ Successfully connected to JGI Lakehouse!")
print(f"Available schemas: {info}")
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
- Rotate tokens periodically (every 90 days recommended)
- Revoke tokens from Dremio UI if compromised
