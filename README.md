# Curio for Android

A swipeable feed of short learning cards: new findings, fundamentals, myths and quizzes, in topics you pick. A fresh batch lands every morning, and a reminder nudges you to open it.

## Install

1. On your Android phone, open **Releases → latest** in this repo and download `curio.apk`.
2. Open the file. If Android asks, allow your browser or file manager to install unknown apps.
3. Open Curio and allow notifications when asked.

Every new build installs over the previous one, so updating is the same steps.

## How it works

- **Cards:** a scheduled Claude task researches ~28 cards each morning (6:12 am India time) and writes them to `feed/latest.json` (the last 31 days). Images, when available, go in `feed/img/`.
- **App:** a small native Android shell (plain Java, no extra libraries) around the Curio interface in `app/src/main/assets/index.html`. It downloads the feed, keeps a copy for offline use, and stores your topics, saved cards and what you've seen on the phone.
- **Reminder:** set on the phone itself (default 7:30 am, change it under *Morning reminder*). It shows how many new cards arrived and the first headline. It re-arms itself after a restart.
- **Build:** every push to `main` that touches the app builds a signed APK with GitHub Actions and publishes it as the `latest` release.

## Updating the interface

The page is generated from the published Curio artifact:

```
python3 tools/make_page.py path/to/curio.html app/src/main/assets/index.html
```

## Notes

- The feed is public, since the app reads it without signing in. It contains only the cards and their sources.
- `app/curio.keystore` is committed so builds can be signed without extra setup. That's fine for a personal sideloaded app; publish to an app store with a private key instead.
- Fonts: Bricolage Grotesque, Atkinson Hyperlegible and IBM Plex Mono, all under the SIL Open Font License.
