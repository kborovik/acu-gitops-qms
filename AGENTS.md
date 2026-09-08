# AGENTS.md

This repository is an `acu` YAML seed package for developing Acumatica QMS customization for
https://github.com/kborovik/acu-google-qms

The `acu` CLI lives in https://github.com/kborovik/acumatica-cli
Create github issue in that repo, not here to fix CLI defects.

The QMS customization lives in https://github.com/kborovik/acu-custom-qms
Create github issue in that repo, not here, for QM customization errors or deficiencies.

Never print `.env` secrets.

## In-product Help (this tenant)

Version-matched docs live on the CNBN instance, not help.acumatica.com.

- Public: `https://acu-26r1-dev1.lab5.ca/AcumaticaERP`
- Tenant: `CNBN` (`CompanyID=CNBN`)
- Landing: `/Help?CompanyID=CNBN`
- Build: 26.101.0225
- Creds: repo-root `.env` (`ACU_USER`, `ACU_PASSWORD`, `ACU_TENANT`)

Drop `(W(n))` from URLs (cookieless ASP.NET token). Use cookies.

### Access (verified)

Unauthenticated GET redirects to `/Frames/Login.aspx`. Grok `web_fetch` UA is rejected (`Browser not supported`). Use a Chrome User-Agent.

**UI login**, not REST:

1. GET `/Frames/Login.aspx?ReturnUrl=%2fAcumaticaERP%2fHelp&CompanyID=CNBN`
2. POST the same URL as `application/x-www-form-urlencoded`: keep hidden fields; set `ctl00$phUser$txtUser`, `ctl00$phUser$txtPass`, `ctl00$phUser$cmbCompany=CNBN`, `ctl00$phUser$btnLogin=Sign In`
3. Session cookie `.ASPXAUTH` is required for Help

Do **not** `POST /entity/auth/login` for Help — that counts as an API session and returns `API Login Limit`. This instance is trial (two concurrent UI users): GET `/Frames/Logout.aspx` when done.

Chrome DevTools works if Chrome is already running. Otherwise curl/python with the Chrome UA and the form login above.

### Search (no keyword API)

`GET /ui/help/{id}` resolves a **screen ID**, not a word. `/ui/help/username` and `/ui/help/Users` return empty `pageid=00000000-…`. Navbar Search is screen `SE.00.00.40`; GET query params do not return hits. Custom `QM*` screens have no wiki article.

Lookup order:

1. **Screen ID** (preferred). `GET /ui/help/SM201010` produces JSON `{url, wiki, article, wikiName, html}`. `article` is the form-reference `pageid`. `html` is related-topic links (`wikiname` + `PageID`), not the full article.
2. **Article text.** `GET /Wiki/ShowExport.aspx?PageID={article}&type=txt` (plain text). Concept pages: `GET /Wiki/ShowWiki.aspx?wikiname=HelpRoot_Administration&PageID={guid}` or `ShowExport` on that `PageID`.
3. **Tree.** `GET /ui/helptree` (wiki roots) leads to `GET /ui/helptree/{wiki-guid}` (children; each has `url` with `pageid`). System Administration wiki id: `20f237dd-409f-4338-b5ef-39cff26e1930`.
4. **Field contracts** (length, `InputMask`, uniqueness). Help does not state these — DAC / product source.

Example: Users (`SM201010`) leads to `/ui/help/SM201010`, then export `834cc181-97fa-4db4-a7e0-3eaba142c166`; related concept `User Access: General Information` is `PageID=4fffce52-0091-4d33-ba3c-b4a756b45670`.

