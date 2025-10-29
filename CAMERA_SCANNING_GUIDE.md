# Camera Scanning Guide - Local vs Replit Environment

## Issue Summary
Camera/barcode scanning modules work correctly in the Replit environment but fail when running locally. This is due to browser security requirements for camera access.

## Root Cause
Modern web browsers (Chrome, Firefox, Safari, etc.) enforce **strict security policies** for accessing device cameras:

1. **HTTPS Required**: Camera access is only allowed over secure (HTTPS) connections
2. **Localhost Exception**: Browsers allow camera access on `localhost` or `127.0.0.1` for development

### Why It Works in Replit
- Replit automatically provides HTTPS URLs for all web applications
- The barcode scanner's security check passes: `location.protocol === 'https:'`

### Why It Fails Locally
- Local development typically uses HTTP (e.g., `http://192.168.1.100:5000`)
- The barcode scanner enforces this check in `static/js/barcode-scanner.js` (line 60):
  ```javascript
  if (location.protocol !== 'https:' && 
      location.hostname !== 'localhost' && 
      location.hostname !== '127.0.0.1') {
      throw new Error('Camera access requires HTTPS or localhost connection');
  }
  ```

## Solutions for Local Development

### Option 1: Use Localhost (Easiest)
Access your application using `localhost` or `127.0.0.1`:

**Instead of:**
- `http://192.168.1.100:5000` ❌
- `http://your-computer-name:5000` ❌

**Use:**
- `http://localhost:5000` ✅
- `http://127.0.0.1:5000` ✅

**Limitations:**
- Only accessible from the local machine
- Cannot test from mobile devices or other computers on the network

### Option 2: Set Up HTTPS Locally (Recommended for Testing)

#### Using Self-Signed SSL Certificate

1. **Generate SSL Certificate:**
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes \
     -out cert.pem -keyout key.pem -days 365 \
     -subj "/CN=localhost"
   ```

2. **Update Gunicorn Command:**
   ```bash
   gunicorn --certfile=cert.pem --keyfile=key.pem \
     --bind 0.0.0.0:5000 main:app
   ```

3. **Access via HTTPS:**
   - `https://localhost:5000`
   - Accept the browser security warning for self-signed certificate

#### Using mkcert (Better for Development)

1. **Install mkcert:**
   ```bash
   # macOS
   brew install mkcert
   
   # Linux
   wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64
   chmod +x mkcert-v1.4.4-linux-amd64
   sudo mv mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert
   ```

2. **Create Local CA:**
   ```bash
   mkcert -install
   ```

3. **Generate Certificate:**
   ```bash
   mkcert localhost 127.0.0.1 ::1
   ```

4. **Start with HTTPS:**
   ```bash
   gunicorn --certfile=localhost+2.pem --keyfile=localhost+2-key.pem \
     --bind 0.0.0.0:5000 main:app
   ```

### Option 3: Use ngrok (For Remote Testing)

Expose your local server with HTTPS:

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   ```

2. **Start Your Application:**
   ```bash
   python -m gunicorn --bind 0.0.0.0:5000 main:app
   ```

3. **Expose via ngrok:**
   ```bash
   ngrok http 5000
   ```

4. **Use the HTTPS URL provided by ngrok**

### Option 4: Temporarily Disable Security Check (Development Only)

**⚠️ WARNING: Only for development, never deploy this!**

Comment out the HTTPS check in `static/js/barcode-scanner.js`:
```javascript
// TEMPORARILY DISABLED FOR LOCAL DEVELOPMENT
// if (location.protocol !== 'https:' && 
//     location.hostname !== 'localhost' && 
//     location.hostname !== '127.0.0.1') {
//     throw new Error('Camera access requires HTTPS or localhost connection');
// }
```

**Remember to restore this check before deployment!**

## Affected Modules

The following modules use camera scanning and are affected by this issue:

1. **GRPO Module** - Barcode scanning for goods receipt
2. **Bin Scanning Module** - Warehouse bin location scanning
3. **Pick List Module** - Item scanning during picking
4. **Inventory Transfer Module** - Serial number scanning
5. **Barcode Reprint Module** - QR/Barcode generation and validation

## Testing Checklist

- [ ] Camera access works on `localhost:5000`
- [ ] Camera access works on HTTPS (if configured)
- [ ] Barcode scanning detects codes correctly
- [ ] QR code scanning works properly
- [ ] Manual input fallback works when camera fails
- [ ] Error messages display correctly for non-HTTPS/localhost

## Production Deployment

**No changes needed for production:**
- Replit deployments automatically use HTTPS
- Published apps work correctly without modifications
- All camera scanning features function normally

## Browser Compatibility

| Browser | HTTPS Required | Localhost Allowed |
|---------|---------------|-------------------|
| Chrome  | ✅            | ✅                |
| Firefox | ✅            | ✅                |
| Safari  | ✅            | ✅                |
| Edge    | ✅            | ✅                |

## Additional Resources

- [MDN: getUserMedia Security](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia#security)
- [QuaggaJS Documentation](https://serratus.github.io/quaggaJS/)
- [mkcert GitHub](https://github.com/FiloSottile/mkcert)
- [ngrok Documentation](https://ngrok.com/docs)
