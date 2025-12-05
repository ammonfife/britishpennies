#!/usr/bin/env python3
"""
Setup Google Analytics 4 and Search Console for britishpennies.com and britishpennies.org
Uses existing Google Ads OAuth credentials and re-authorizes with additional scopes.
"""

import json
import os
import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
AUTH_DIR = SCRIPT_DIR.parent.parent / 'auth'
CREDS_FILE = AUTH_DIR / 'google-ads.json'
TOKEN_FILE = AUTH_DIR / 'google-analytics-token.json'

DOMAINS = ['britishpennies.com', 'britishpennies.org']

# Scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/analytics.edit',
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters',
]

def install_deps():
    """Install required packages."""
    import subprocess
    packages = ['google-auth', 'google-auth-oauthlib', 'google-api-python-client', 'google-analytics-admin']
    for pkg in packages:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], check=True)

def get_credentials():
    """Get or refresh OAuth credentials with Analytics scopes."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None

    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid creds, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client config from google-ads.json
            with open(CREDS_FILE, 'r') as f:
                ads_creds = json.load(f)

            client_config = {
                "installed": {
                    "client_id": ads_creds['client_id'],
                    "client_secret": ads_creds['client_secret'],
                    "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Saved credentials to {TOKEN_FILE}")

    return creds


def setup_analytics(creds):
    """Create GA4 properties for both domains."""
    from google.analytics.admin import AnalyticsAdminServiceClient
    from google.analytics.admin_v1alpha.types import Property, DataStream

    print("\n📊 Setting up Google Analytics 4...")

    client = AnalyticsAdminServiceClient(credentials=creds)

    # List existing accounts
    accounts = list(client.list_accounts())
    if not accounts:
        print("❌ No Google Analytics accounts found.")
        print("Create one at https://analytics.google.com first.")
        return None

    account = accounts[0]
    print(f"✅ Using account: {account.display_name}")

    measurement_ids = {}

    for domain in DOMAINS:
        print(f"\n  Setting up {domain}...")

        # Check if property exists
        existing_props = list(client.list_properties(filter=f"parent:{account.name}"))
        prop = None
        for p in existing_props:
            if domain.replace('.', '') in p.display_name.lower().replace(' ', '').replace('.', ''):
                prop = p
                print(f"  ⚠️  Found existing property: {p.display_name}")
                break

        if not prop:
            # Create new property
            prop = client.create_property(
                property=Property(
                    display_name=f"British Pennies ({domain})",
                    time_zone="Europe/London",
                    currency_code="GBP",
                ),
                parent=account.name
            )
            print(f"  ✅ Created property: {prop.display_name}")

        # Check for data stream
        streams = list(client.list_data_streams(parent=prop.name))
        stream = None
        for s in streams:
            if hasattr(s, 'web_stream_data') and s.web_stream_data:
                stream = s
                measurement_ids[domain] = s.web_stream_data.measurement_id
                print(f"  ✅ Found stream: {measurement_ids[domain]}")
                break

        if not stream:
            # Create web data stream
            stream = client.create_data_stream(
                parent=prop.name,
                data_stream=DataStream(
                    display_name=f"{domain} Web Stream",
                    type_=DataStream.DataStreamType.WEB_DATA_STREAM,
                    web_stream_data=DataStream.WebStreamData(
                        default_uri=f"https://{domain}"
                    )
                )
            )
            measurement_ids[domain] = stream.web_stream_data.measurement_id
            print(f"  ✅ Created stream: {measurement_ids[domain]}")

    return measurement_ids


def setup_search_console(creds):
    """Add sites to Google Search Console."""
    from googleapiclient.discovery import build

    print("\n🔍 Setting up Google Search Console...")

    service = build('searchconsole', 'v1', credentials=creds)

    for domain in DOMAINS:
        site_url = f'https://{domain}/'
        print(f"\n  Adding {site_url}...")

        try:
            service.sites().add(siteUrl=site_url).execute()
            print(f"  ✅ Added: {site_url}")
        except Exception as e:
            if 'already' in str(e).lower():
                print(f"  ⚠️  Already exists: {site_url}")
            else:
                print(f"  ❌ Error: {e}")

        # Check verification
        try:
            site = service.sites().get(siteUrl=site_url).execute()
            print(f"  Permission: {site.get('permissionLevel', 'unknown')}")
        except:
            pass


def print_tracking_code(measurement_ids):
    """Print GA4 tracking code."""
    if not measurement_ids:
        return

    print("\n" + "=" * 60)
    print("📝 GA4 TRACKING CODE - Add to <head> of all HTML files:")
    print("=" * 60)

    # Use .org as primary (since that's the canonical)
    mid = measurement_ids.get('britishpennies.org', measurement_ids.get('britishpennies.com'))

    print(f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{mid}');
</script>
""")

    # Save measurement IDs
    ids_file = SCRIPT_DIR / 'ga_measurement_ids.json'
    with open(ids_file, 'w') as f:
        json.dump(measurement_ids, f, indent=2)
    print(f"💾 Measurement IDs saved to: {ids_file}")


def main():
    print("🚀 Google Analytics & Search Console Setup")
    print("=" * 50)
    print(f"Domains: {', '.join(DOMAINS)}\n")

    # Install dependencies
    print("📦 Checking dependencies...")
    install_deps()

    # Get credentials (will open browser for OAuth)
    print("\n🔐 Getting OAuth credentials...")
    print("A browser window will open for authorization.\n")
    creds = get_credentials()

    if not creds:
        print("❌ Failed to get credentials")
        return

    print("✅ Authentication successful!")

    # Setup Analytics
    measurement_ids = setup_analytics(creds)

    # Setup Search Console
    setup_search_console(creds)

    # Print tracking code
    print_tracking_code(measurement_ids)

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Verify domains in Search Console (DNS TXT records already added)")
    print("2. Add the tracking code above to all HTML files")
    print("3. Submit sitemaps in Search Console")


if __name__ == '__main__':
    main()
