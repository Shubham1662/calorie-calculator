"""One-time helper: get a Google OAuth refresh token for the calorie app.

Use this when service-account key creation is blocked in your Google Cloud
project. It signs in as YOUR Google account (browser window opens once) and
prints the [gsheets] secrets block to paste into Streamlit Cloud.

Prerequisites (see README "Persistent storage with Google Sheets"):
1. Google Sheets API + Google Drive API enabled in your project.
2. OAuth consent screen configured (External) and PUBLISHED to "In production"
   — if left in "Testing", the token expires after 7 days.
3. An OAuth client ID of type "Desktop app", with its JSON downloaded.

Usage:
    pip install google-auth-oauthlib
    python scripts/get_google_token.py path/to/client_secret_xxx.json
"""

import sys

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/get_google_token.py <client_secret.json>")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit("Missing dependency. Run: pip install google-auth-oauthlib")

    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    if not creds.refresh_token:
        sys.exit("No refresh token returned — remove the app's access at "
                 "https://myaccount.google.com/permissions and run this again.")

    print("\nPaste this into Streamlit Cloud -> App settings -> Secrets")
    print("(or .streamlit/secrets.toml locally), filling in your sheet URL:\n")
    print("[gsheets]")
    print('spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"')
    print(f'client_id = "{creds.client_id}"')
    print(f'client_secret = "{creds.client_secret}"')
    print(f'refresh_token = "{creds.refresh_token}"')


if __name__ == "__main__":
    main()
