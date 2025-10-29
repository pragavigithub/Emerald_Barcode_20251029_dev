# SAP B1 Connectivity Guide for Replit Environment

## Issue Summary
The MultiGRN module's BusinessPartners dropdown is not populating because the SAP B1 server at `10.112.253.173:50000` cannot be reached from the Replit cloud environment.

## Root Cause
- **Private IP Address**: The configured SAP server (`10.112.253.173`) is a private IP address
- **Network Isolation**: Replit runs in a cloud environment that cannot directly access private/internal networks
- **No VPN/Tunnel**: There's no established tunnel or VPN connection to the internal network

## Recent Fixes Applied (October 13, 2025)

### 1. Fixed SAP Credentials Loading
**Problem**: MultiGRN service was reading from `os.environ` which returned empty strings.

**Solution**: Updated `modules/multi_grn_creation/services.py` to use Flask's `current_app.config`:
```python
# Before
self.base_url = os.environ.get('SAP_B1_SERVER', '')

# After  
self.base_url = current_app.config.get('SAP_B1_SERVER', '')
```

### 2. Enhanced Error Logging
Added comprehensive error messages to help diagnose connectivity issues:
- Connection errors now explicitly mention network accessibility
- Timeout errors are clearly distinguished
- Configuration validation shows which credentials are missing

## Solutions for SAP Connectivity

### Option 1: Use a Public SAP Server (Recommended for Production)
If you have a public-facing SAP B1 server:

1. Set environment variables in Replit:
```bash
SAP_B1_SERVER=https://your-public-sap-server.com:50000
SAP_B1_USERNAME=your_username
SAP_B1_PASSWORD=your_password
SAP_B1_COMPANY_DB=your_company_db
```

2. Ensure the server has:
   - Valid SSL certificate (or set `SAP_SSL_VERIFY=false` for self-signed certs)
   - Firewall rules allowing Replit IP ranges
   - CORS configured for your Replit domain

### Option 2: Set Up a Tunnel/Proxy
Use a service to create a secure tunnel from Replit to your internal network:

**Using Ngrok or Cloudflare Tunnel:**
1. Install the tunnel on a machine in your internal network
2. Configure it to forward to your SAP server (10.112.253.173:50000)
3. Get the public URL (e.g., `https://abc123.ngrok.io`)
4. Update SAP_B1_SERVER environment variable with the tunnel URL

**Example with Ngrok:**
```bash
# On your internal network machine
ngrok http 10.112.253.173:50000

# Then in Replit, set:
SAP_B1_SERVER=https://abc123.ngrok.io
```

### Option 3: Development/Testing Mode
For development without SAP connectivity, you can:

1. **Mock SAP Data**: Create a mock service that returns sample business partners
2. **Use Test Data**: Populate dropdown from a local database table
3. **API Proxy**: Create an intermediate API on your internal network

#### Quick Mock Implementation
Create `modules/multi_grn_creation/mock_sap.py`:
```python
def get_mock_customers():
    return {
        'success': True,
        'customers': [
            {'CardCode': 'C00001', 'CardName': 'ABC Corporation'},
            {'CardCode': 'C00002', 'CardName': 'XYZ Industries'},
            {'CardCode': 'C00003', 'CardName': 'Sample Customer Ltd.'},
        ]
    }
```

Update `routes.py` to use mock when SAP is unavailable:
```python
@multi_grn_bp.route('/api/customers-dropdown')
@login_required
def api_customers_dropdown():
    sap_service = SAPMultiGRNService()
    result = sap_service.fetch_all_valid_customers()
    
    # Fallback to mock data if SAP is unavailable
    if not result['success']:
        from modules.multi_grn_creation.mock_sap import get_mock_customers
        logging.warning("⚠️ Using mock customer data - SAP unavailable")
        return jsonify(get_mock_customers())
    
    return jsonify(result)
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SAP_B1_SERVER` | SAP B1 Service Layer URL | `https://sap.company.com:50000` |
| `SAP_B1_USERNAME` | SAP B1 username | `manager` |
| `SAP_B1_PASSWORD` | SAP B1 password | `YourPassword123` |
| `SAP_B1_COMPANY_DB` | SAP Company Database name | `SBODemoUS` |
| `SAP_SSL_VERIFY` | SSL verification (set to 'false' for self-signed certs) | `false` |

## Testing SAP Connectivity

### 1. Check Logs
After logging in and accessing `/multi-grn/create/step1`, check the workflow logs for:
- `🔐 Attempting SAP login to...` - Connection attempt
- `✅ SAP B1 login successful` - Successful connection
- `❌ SAP B1 connection failed` - Connection error

### 2. Test from Browser Console
Open browser developer tools and check for error messages when the dropdown loads.

### 3. Manual API Test
Test the endpoint directly:
```bash
curl http://your-replit-url/multi-grn/api/customers-dropdown
```

## Troubleshooting

### Error: "Cannot connect to SAP server"
- **Cause**: Network connectivity issue
- **Fix**: Verify SAP server is publicly accessible or set up a tunnel

### Error: "SAP authentication failed"
- **Cause**: Invalid credentials
- **Fix**: Verify username, password, and company DB are correct

### Error: "SSL verification failed"
- **Cause**: Self-signed certificate
- **Fix**: Set `SAP_SSL_VERIFY=false` (development only)

### Dropdown Shows "Loading..." Forever
- **Cause**: API call timing out or failing silently
- **Check**: Browser console for JavaScript errors
- **Check**: Workflow logs for SAP connection errors

## Next Steps

1. **Choose a connectivity solution** from the options above
2. **Configure environment variables** in Replit Secrets
3. **Test the connection** using the troubleshooting steps
4. **Monitor logs** to verify successful SAP integration

## Database Migration Status

✅ **MySQL Migration Complete**: The MultiGRN module tables are already created via `mysql_multi_grn_migration.py`
- `multi_grn_batches`
- `multi_grn_po_links`
- `multi_grn_line_selections`

No database changes were needed for the SAP connectivity fix.

---

**Last Updated**: October 13, 2025
**Module**: Multiple GRN Creation
**Status**: ✅ Code Fixed | ⚠️ SAP Connectivity Required
