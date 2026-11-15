# One-time setup

Everything is free. Keys go only into GitHub's encrypted Secrets, never into a file or a chat.
Claude guides each step one screen at a time.

## A. GitHub
1. Repo `growtharcco-sudo/resolveai-studio`, Public, Claude GitHub app has access.
2. Repo -> Settings -> Pages -> Source *Deploy from a branch* -> `media` / `(root)` -> Save.
   Check: https://growtharcco-sudo.github.io/resolveai-studio/ shows the ResolveAI Studio page.

## B. Instagram key (never expires): reuse the system user "unhyped-poster" and the app "Real Number Studio"
1. @resolveai.software is a Professional (Business) account linked to a Facebook Page "ResolveAI".
   Trap: switching to Business can silently create a NEW business portfolio. The account and its Page must end up
   in the **The Real Number** portfolio.
2. business.facebook.com -> The Real Number -> Settings -> Accounts: add the Page "ResolveAI" and the Instagram account.
3. Settings -> Users -> System users -> unhyped-poster -> Assign assets: the Page and the Instagram account, Full control.
   Trap: check both really show "Full control" afterwards (it can say "Nothing assigned yet").
4. Generate new token -> app Real Number Studio -> expiration **Never** -> permissions `instagram_basic`,
   `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management` -> that is `IG_TOKEN`.
5. `IG_USER_ID`: leave it out at first and run **Actions -> Check keys**: it prints the ID to use.

## C. YouTube key: a NEW Google Cloud project for ResolveAI (its own daily upload quota)
1. console.cloud.google.com -> New project "ResolveAI Studio" -> enable **YouTube Data API v3**.
2. Google Auth Platform -> Branding: app name ResolveAI Studio, support email, home page
   https://growtharcco-sudo.github.io/resolveai-studio/ , privacy .../privacy.html , terms .../terms.html ,
   authorized domain `growtharcco-sudo.github.io`. (Trap: "Publish app" stays greyed out until these are filled.)
3. Data access -> scopes `.../auth/youtube.upload` and `.../auth/youtube`. Audience -> **Publish app** (In production).
4. Clients -> Create client -> **Desktop app** -> download the JSON.
   Trap: `redirect_uri_mismatch` = wrong client type or an older client_secret file in Downloads. Use the newest file.
5. On the laptop: `pip3 install google-auth-oauthlib`, then
   `python3 tools/get_youtube_token.py ~/Downloads/client_secret_XXXX.json`. At sign-in choose the
   **ResolveAI** channel (@resolveaisoftware). It prints `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

## D. Secrets
Repo -> Settings -> Secrets and variables -> Actions -> New repository secret, one each:
`IG_TOKEN`, `IG_USER_ID`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
Paste only the value (if a label or spaces slip in, the code cleans them).

## E. Test (posts nothing publicly)
1. **Check keys** (Claude runs it by pushing to `checks/`): prints the Instagram username, YouTube channel name and IDs.
2. **Deep check** (Claude pushes `checks/deep.txt`): Instagram processes a test Reel without publishing it; YouTube gets
   an UNLISTED test upload that is checked, given the thumbnail, then deleted.
3. One real end-to-end post (a `test` slot Reel), then the daily task is switched on.

## F. Scheduled task (Claude)
ONE cloud task, "ResolveAI daily Reel", runs `ROUTINE.md` section A every day at about 2:30 PM IST.
It needs "Skip all approvals" (Automatically approve) on and no connectors it doesn't use.
