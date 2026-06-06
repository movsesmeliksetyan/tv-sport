# PimpleTV — Android TV App

Kotlin + **Jetpack Compose for TV** (`androidx.tv:tv-material`). Browses matches from the
backend API and (Phase 4) hands off to Ace Stream via `acestream://`. Implements the contract
in [`../docs/api/openapi.yaml`](../docs/api/openapi.yaml).

## Status — Phase 3 (browse + detail)

Working app, verified on the Television_4K emulator (`docs/screenshot-*.png`):
- **Featured hero** for the top live/upcoming match (logos via Coil, focusable Watch).
- Focus-scaled **match cards** in "Live now / Football / Hockey" rows with a LIVE badge.
- **Detail screen** with teams, kickoff, channel, and a Watch / "links appear ~1h before" state.

Remaining: polling refresh (T3.5), Ace Stream hand-off (Phase 4), more states (Phase 5).

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
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./gradlew assembleDebug
# run on the TV emulator:
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell monkey -p ru.pimpletv.tv -c android.intent.category.LEANBACK_LAUNCHER 1
```

## Tech

Kotlin · Jetpack **Compose for TV** (`androidx.tv:tv-material` 1.0.0, Compose BOM) · Coil ·
Retrofit 2.11 + OkHttp · Coroutines · minSdk 21 / target 35 · AGP 8.7.3 / Gradle 8.11.1
(Kotlin DSL + version catalog).

## Layout

```
app/src/main/
  AndroidManifest.xml          LEANBACK_LAUNCHER, leanback feature, TV banner
  java/ru/pimpletv/tv/
    MainActivity.kt            ComponentActivity -> setContent { PimpleApp() }
    data/                      Retrofit service, DTOs (contract), repository
    ui/
      PimpleApp.kt             root nav (browse <-> detail), theme wrapper
      MatchViewModel.kt        loads matches -> BrowseUiState
      browse/                  BrowseScreen, FeaturedHero, MatchCard, LiveBadge
      detail/DetailScreen.kt   match detail + Watch
      theme/                   Compose TV theme (color, type)
  res/values/                  Theme.PimpleTV (no-action-bar shell), colors
```
