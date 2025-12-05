#!/usr/bin/env python3
"""
Setup Google Analytics 4 and Google Search Console for britishpennies.com and britishpennies.org
"""

import json
import os
from pathlib import Path

# Check for required packages
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Installing required packages...")
    os.system("pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build

# Scopes needed for Analytics Admin and Search Console
SCOPES = [
    'https://www.googleapis.com/auth/analytics.edit',
    'https://www.googleapis.com/auth/webmasters',
]

DOMAINS = [
    'britishpennies.com',
    'britishpennies.org',
]

# Paths
SCRIPT_DIR = Path(__file__).parent
AUTH_DIR = SCRIPT_DIR.parent.parent / 'auth'
CREDENTIALS_FILE = AUTH_DIR / 'google-oauth-credentials.json'
TOKEN_FILE = AUTH_DIR / 'google-analytics-token.json'


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"\n❌ Missing OAuth credentials file: {CREDENTIALS_FILE}")
                print("\nTo create OAuth credentials:")
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download JSON and save as:", CREDENTIALS_FILE)
                print("\nAlso enable these APIs:")
                print("- Google Analytics Admin API")
                print("- Google Search Console API")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return creds


def setup_analytics(creds):
    """Create GA4 properties for both domains."""
    print("\n📊 Setting up Google Analytics 4...")

    try:
        service = build('analyticsadmin', 'v1beta', credentials=creds)

        # List existing accounts
        accounts = service.accounts().list().execute()

        if not accounts.get('accounts'):
            print("❌ No Google Analytics accounts found.")
            print("Please create an account at https://analytics.google.com first.")
            return None

        # Use first account
        account = accounts['accounts'][0]
        account_name = account['name']
        print(f"✅ Using account: {account.get('displayName', account_name)}")

        measurement_ids = {}

        for domain in DOMAINS:
            print(f"\n  Creating property for {domain}...")

            # Check if property already exists
            properties = service.properties().list(filter=f"parent:{account_name}").execute()
            existing = None
            for prop in properties.get('properties', []):
                if domain in prop.get('displayName', ''):
                    existing = prop
                    break

            if existing:
                print(f"  ⚠️  Property already exists: {existing['displayName']}")
                prop_name = existing['name']
            else:
                # Create new property
                property_body = {
                    'displayName': f'British Pennies ({domain})',
                    'timeZone': 'Europe/London',
                    'currencyCode': 'GBP',
                }

                result = service.properties().create(
                    body=property_body,
                    parent=account_name
                ).execute()

                prop_name = result['name']
                print(f"  ✅ Created property: {result['displayName']}")

            # Create web data stream
            streams = service.properties().dataStreams().list(parent=prop_name).execute()

            stream_exists = False
            for stream in streams.get('dataStreams', []):
                if stream.get('webStreamData', {}).get('defaultUri', '').endswith(domain):
                    measurement_ids[domain] = stream['webStreamData']['measurementId']
                    stream_exists = True
                    print(f"  ✅ Existing stream - Measurement ID: {measurement_ids[domain]}")
                    break

            if not stream_exists:
                stream_body = {
                    'displayName': f'{domain} Web Stream',
                    'webStreamData': {
                        'defaultUri': f'https://{domain}'
                    }
                }

                stream = service.properties().dataStreams().create(
                    parent=prop_name,
                    body=stream_body
                ).execute()

                measurement_ids[domain] = stream['webStreamData']['measurementId']
                print(f"  ✅ Created stream - Measurement ID: {measurement_ids[domain]}")

        return measurement_ids

    except Exception as e:
        print(f"❌ Analytics setup error: {e}")
        return None


def setup_search_console(creds):
    """Add sites to Google Search Console."""
    print("\n🔍 Setting up Google Search Console...")

    try:
        service = build('searchconsole', 'v1', credentials=creds)

        for domain in DOMAINS:
            site_url = f'https://{domain}/'
            print(f"\n  Adding {site_url}...")

            try:
                # Add site
                service.sites().add(siteUrl=site_url).execute()
                print(f"  ✅ Added site: {site_url}")
            except Exception as e:
                if 'already exists' in str(e).lower() or '403' in str(e):
                    print(f"  ⚠️  Site already exists or access denied")
                else:
                    print(f"  ❌ Error: {e}")

            # Get verification status
            try:
                site_info = service.sites().get(siteUrl=site_url).execute()
                print(f"  Permission level: {site_info.get('permissionLevel', 'unknown')}")
            except:
                pass

        print("\n📋 Verification options:")
        print("   - HTML file: Upload verification file to site root")
        print("   - HTML tag: Add meta tag to <head>")
        print("   - DNS: Add TXT record to domain")

        return True

    except Exception as e:
        print(f"❌ Search Console setup error: {e}")
        return None


def generate_tracking_code(measurement_ids):
    """Generate GA4 tracking code snippet."""
    if not measurement_ids:
        return None

    print("\n📝 GA4 Tracking Code to add to all HTML files:")
    print("=" * 60)

    for domain, mid in measurement_ids.items():
        print(f"\n<!-- For {domain} -->")
        print(f"""<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{mid}');
</script>""")

    print("\n" + "=" * 60)
    return measurement_ids


def main():
    print("🚀 Google Analytics & Search Console Setup")
    print("=" * 50)
    print(f"Domains: {', '.join(DOMAINS)}")

    # Get credentials
    creds = get_credentials()
    if not creds:
        return

    print("✅ Authentication successful")

    # Setup Analytics
    measurement_ids = setup_analytics(creds)

    # Setup Search Console
    setup_search_console(creds)

    # Generate tracking code
    if measurement_ids:
        generate_tracking_code(measurement_ids)

        # Save measurement IDs for later use
        ids_file = SCRIPT_DIR / 'ga_measurement_ids.json'
        with open(ids_file, 'w') as f:
            json.dump(measurement_ids, f, indent=2)
        print(f"\n💾 Measurement IDs saved to: {ids_file}")

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Verify domains in Search Console")
    print("2. Add GA tracking code to all HTML files")
    print("3. Submit sitemaps in Search Console")


if __name__ == '__main__':
    main()
