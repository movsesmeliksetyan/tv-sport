# PimpleTV — Android TV App

Kotlin + AndroidX **Leanback** TV app. Browses matches from the backend API and (Phase 4)
hands off to Ace Stream via `acestream://`. Implements the contract in
[`../docs/api/openapi.yaml`](../docs/api/openapi.yaml).

## Status — Phase 0 scaffold (T0.5b)

Runnable skeleton: a `BrowseSupportFragment` that fetches `/api/matches` and groups cards by
sport with a LIVE badge. Detail, stream chooser, Ace Stream hand-off, and polling come in
Phases 3–5 ([../docs/tasks.md](../docs/tasks.md)).

## Open in Android Studio

1. **File → Open** → select this `androidtv/` folder.
2. On first sync Studio will prompt to install **SDK Platform 35** + **Build-Tools** — accept.
3. Run on an **Android TV emulator** (Tools → Device Manager → TV profile) or a real TV via adb.

## Backend address

`app/build.gradle.kts` sets `API_BASE_URL`:
- **Emulator** → `http://10.0.2.2:8000/` (host loopback; default).
- **Real TV on the LAN** → change to the Pi, e.g. `http://raspberrypi.local:8000/` or `http://<pi-ip>:8000/`.

Cleartext HTTP is enabled (`usesCleartextTraffic="true"`) for the local/LAN backend.

Start the backend first:
```bash
cd ../backend && docker compose up -d --build   # mock data until Phase 1
```

## CLI build (optional)

Uses the Gradle wrapper + Android Studio's bundled JDK 21:
```bash
export JAVA_HOME="$HOME/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./gradlew assembleDebug      # requires the Android SDK installed (Studio does this)
```

## Tech

Kotlin · Leanback 1.0.0 · Retrofit 2.11 + OkHttp · Glide 4.16 · Coroutines · minSdk 21 / target 35 ·
AGP 8.7.3 / Gradle 8.11.1 (Kotlin DSL + version catalog).

## Layout

```
app/src/main/
  AndroidManifest.xml          LEANBACK_LAUNCHER, leanback feature, TV banner
  java/ru/pimpletv/tv/
    MainActivity.kt            hosts the browse fragment
    MainFragment.kt            BrowseSupportFragment (rows of match cards)
    data/                      Retrofit service, DTOs (contract), repository
    ui/MatchCardPresenter.kt   ImageCardView + LIVE badge
  res/                         theme (Theme.Leanback), strings, colors, banner
```
