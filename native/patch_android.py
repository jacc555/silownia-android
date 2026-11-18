"""Poprawki projektu Androida wygenerowanego przez `npx cap add android`.
Każdy krok jest osobny, a błąd jednego (np. inny szablon) nie przerywa budowania."""
import os, re, shutil

A = 'android/app/src/main'
def log(*a): print('[patch]', *a)

# 1) uprawnienia: powiadomienia, dokładne alarmy, wibracje
try:
    p = A + '/AndroidManifest.xml'
    m = open(p, encoding='utf-8').read()
    add = ''
    for q in ('android.permission.POST_NOTIFICATIONS', 'android.permission.USE_EXACT_ALARM',
              'android.permission.RECEIVE_BOOT_COMPLETED', 'android.permission.VIBRATE'):
        if q not in m: add += '    <uses-permission android:name="%s" />\n' % q
    if 'SCHEDULE_EXACT_ALARM' not in m:
        add += '    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" android:maxSdkVersion="32" />\n'
    m = m.replace('<application', add + '    <application', 1)
    open(p, 'w', encoding='utf-8').write(m); log('uprawnienia dodane')
except Exception as e: log('UWAGA uprawnienia:', e)

# 2) ikony aplikacji i ikona powiadomienia (biała sylwetka)
try:
    shutil.copytree('native/res', A + '/res', dirs_exist_ok=True); log('ikony skopiowane')
except Exception as e: log('UWAGA ikony:', e)

# 3) czarny ekran startowy
try:
    n = 0
    for root, _, files in os.walk(A + '/res'):
        for f in files:
            if f == 'splash.png':
                shutil.copy('native/black.png', os.path.join(root, f)); n += 1
    p = A + '/res/values/styles.xml'
    st = open(p, encoding='utf-8').read()
    if 'windowSplashScreenBackground' not in st:
        st = re.sub(r'(<style name="AppTheme\.NoActionBarLaunch"[^>]*>)',
                    r'\1\n        <item name="windowSplashScreenBackground">#000000</item>', st, count=1)
        open(p, 'w', encoding='utf-8').write(st)
    log('splash czarny, plików:', n)
except Exception as e: log('UWAGA splash:', e)

# 4) numer wersji rośnie z każdym buildem, żeby nowy APK dało się zainstalować na poprzednim
try:
    p = 'android/app/build.gradle'
    g = open(p, encoding='utf-8').read()
    g = re.sub(r'versionCode\s+\d+', 'versionCode ' + os.environ.get('GITHUB_RUN_NUMBER', '1'), g, count=1)
    g = re.sub(r'versionName\s+"[^"]*"', 'versionName "2.' + os.environ.get('GITHUB_RUN_NUMBER', '1') + '"', g, count=1)
    open(p, 'w', encoding='utf-8').write(g); log('numer wersji ustawiony')
except Exception as e: log('UWAGA wersja:', e)
