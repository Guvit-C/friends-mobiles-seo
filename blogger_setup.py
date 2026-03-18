"""
blogger_setup.py
=================
ONE-TIME SETUP SCRIPT — run this locally to get your Blogger OAuth2 refresh token.
You only ever need to run this once. The refresh token never expires unless revoked.

Steps:
  1. Go to https://console.cloud.google.com/
  2. Create a new project (or use existing)
  3. Enable "Blogger API v3" in APIs & Services → Library
  4. Go to APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
  5. Application type: "Desktop app" — give it any name
  6. Download the credentials JSON, copy Client ID and Client Secret below
  7. Run: python blogger_setup.py
  8. Follow the browser prompt, paste the code back
  9. Copy the refresh_token printed at the end into your .env file

Also find your Blog ID:
  - Go to https://www.blogger.com/
  - Open your blog → Settings → Basic
  - Your Blog ID is the long number in the URL or listed under "Blog ID"
"""

import json
import urllib.request
import urllib.parse
import webbrowser

# ── Paste your OAuth2 Desktop credentials here ──────────────────────────────
CLIENT_ID     = "358878101930-5gb6e1pf3gv8qseber4s6j1colkqtiot.apps.googleusercontent.com"   # e.g. "123456789-abc.apps.googleusercontent.com"
CLIENT_SECRET = "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"   # e.g. "GOCSPX-..."
# ────────────────────────────────────────────────────────────────────────────

SCOPE        = "https://www.googleapis.com/auth/blogger"
AUTH_URL     = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL    = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Fill in CLIENT_ID and CLIENT_SECRET at the top of this script first.")
        return

    # Step 1: Build auth URL and open browser
    params = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPE,
        "response_type": "code",
        "access_type":   "offline",
        "prompt":        "consent",   # forces refresh_token to be returned
    })
    auth_link = f"{AUTH_URL}?{params}"

    print("\n── Blogger OAuth2 Setup ──────────────────────────────────────")
    print("Opening Google sign-in in your browser...")
    print(f"\nIf it doesn't open automatically, go to:\n{auth_link}\n")
    webbrowser.open(auth_link)

    # Step 2: User pastes the authorization code
    code = input("Paste the authorization code from the browser here: ").strip()

    # Step 3: Exchange code for tokens
    data = urllib.parse.urlencode({
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read())
    except Exception as e:
        print(f"\nERROR exchanging code for tokens: {e}")
        return

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("\nERROR: No refresh_token returned. Make sure you used 'prompt=consent' and a Desktop app credential.")
        print("Full response:", tokens)
        return

    print("\n── SUCCESS ─────────────────────────────────────────────────")
    print("Add these to your .env file and GitHub Secrets:\n")
    print(f"BLOGGER_CLIENT_ID={CLIENT_ID}")
    print(f"BLOGGER_CLIENT_SECRET={CLIENT_SECRET}")
    print(f"BLOGGER_REFRESH_TOKEN={refresh_token}")
    print("\nAlso add your Blog ID:")
    print("BLOGGER_BLOG_ID=<your blog ID from Blogger settings>")
    print("\nDone. You never need to run this script again.")


if __name__ == "__main__":
    main()
