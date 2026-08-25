"""Diagnose the Google Sheets connection using a service-account JSON key.

Usage: python scripts/diagnose_sheets.py <service_account.json>

Checks, in order: key loads -> Sheets/Drive API reachable -> which
spreadsheets the service account can see (i.e. was the sheet shared?) ->
write access to the first visible sheet.
"""

import sys

import gspread


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/diagnose_sheets.py <service_account.json>")

    print("1. Loading key...")
    import json
    with open(sys.argv[1]) as f:
        email = json.load(f)["client_email"]
    gc = gspread.service_account(filename=sys.argv[1])
    print("   OK — authenticating as:", email)

    print("2. Listing spreadsheets shared with this service account...")
    try:
        files = gc.list_spreadsheet_files()
    except Exception as e:
        print("   FAILED:", type(e).__name__, str(e)[:400])
        print("   -> Likely the Google Drive API is not enabled for this project.")
        return
    if not files:
        print("   NONE visible.")
        print("   -> The sheet has NOT been shared with the service account.")
        print("      Open the spreadsheet -> Share -> add the email above as Editor.")
        return
    for f in files:
        print(f"   visible: {f['name']}  (id: {f['id']})")

    sheet_id = files[0]["id"]
    print(f"3. Opening '{files[0]['name']}' and testing write access...")
    try:
        ss = gc.open_by_key(sheet_id)
        titles = [ws.title for ws in ss.worksheets()]
        print("   worksheets:", titles)
        ws = ss.sheet1
        ws.append_row(["__write_test__"], value_input_option="RAW")
        vals = ws.get_all_values()
        ws.delete_rows(len(vals))
        print("   OK — write + delete succeeded.")
        print("\nAll checks passed. Use this URL in secrets:")
        print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    except Exception as e:
        print("   FAILED:", type(e).__name__, str(e)[:400])
        print("   -> If 403/PERMISSION_DENIED: enable the Google Sheets API, or "
              "share the sheet as Editor (not Viewer).")


if __name__ == "__main__":
    main()
