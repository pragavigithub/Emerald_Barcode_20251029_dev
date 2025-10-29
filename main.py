import sys
import os
import logging
from app import app

# Import routes and APIs
import routes
import api_cascading_dropdowns

if __name__ == "__main__":
    # Check if we're in Replit environment (skip license validation)
    if os.environ.get('REPL_ID') or os.environ.get('DATABASE_URL'):
        logging.info("🚀 Running in Replit environment - skipping license validation")
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        # Original license validation for local deployment
        from Lic.license_validator import load_public_key, validate_license_file

        pub_key_path = os.path.join("C:\\tmp\\", "sap_login", "public_key.pem")
        license_path = os.path.join("C:\\tmp\\", "sap_login", "license.lic")

        try:
            pub = load_public_key(pub_key_path)
            ok, info = validate_license_file(license_path, pub)
            if not ok:
                logging.info("❌ License validation failed:", info)
                sys.exit(1)
            else:

                logging.info("✅ License validated Successfully")
                print("✅ License validated Successfully")
        except Exception as e:
            logging.info(f"❌ License check error: {e}")
            sys.exit(1)

        # Start Flask app only if license is valid
        app.run(host="0.0.0.0", port=5000, debug=True)
