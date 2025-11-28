Cordova packaging instructions for the PWA

Overview
- These steps wrap your PWA in a native WebView using Cordova.
- The app will load the local `www` files; alternatively, you can configure it to load a remote URL (not recommended for offline install).

Quick steps (Android)
1. Install Cordova globally:
   npm install -g cordova

2. Create a Cordova project (if you don't already have one):
   cordova create clamping-app com.example.clamping ClampingApp
   cd clamping-app

3. Add Android platform:
   cordova platform add android

4. Copy the built PWA `www` files into `clamping-app/www`:
   - If you have a build step, point the output to `clamping-app/www`.
   - Otherwise, copy `templates` output and static files into `www`.

5. Build and run on an emulator/device:
   cordova build android
   cordova run android --device

Notes
- For iOS, use `cordova platform add ios` and build on macOS with Xcode installed.
- Configure `config.xml` (id, name, icons) as needed.
- Consider using the `cordova-plugin-wkwebview-engine` and `cordova-plugin-inappbrowser` for modern webviews and external links.
