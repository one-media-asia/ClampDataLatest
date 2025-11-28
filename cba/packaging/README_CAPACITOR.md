Capacitor packaging instructions (recommended)

Overview
- Capacitor provides a cleaner workflow to wrap PWAs as native apps and works well with modern frameworks.

Quick steps (Android/iOS)
1. Install Capacitor in your project (in project root where `www` lives):
   npm install --save @capacitor/core @capacitor/cli

2. Initialize Capacitor:
   npx cap init clamping-app com.example.clamping

3. Build your web assets into `www`.

4. Add platforms:
   npx cap add android
   npx cap add ios

5. Copy web assets and open native IDE:
   npx cap copy
   npx cap open android
   npx cap open ios

6. Build via Android Studio or Xcode.

Notes
- Use `npx cap sync` after dependency changes.
- Configure `capacitor.config.json` if you want to load a remote URL (not recommended for PWA offline behavior).
