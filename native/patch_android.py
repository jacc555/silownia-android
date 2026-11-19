"""Poprawki projektu Androida wygenerowanego przez `npx cap add android`.
Każdy krok jest osobny, a błąd jednego (np. inny szablon) nie przerywa budowania."""
import os, re, shutil, glob

A = 'android/app/src/main'
def log(*a): print('[patch]', *a)

# 1) uprawnienia: powiadomienia, dokładne alarmy, wibracje, instalowanie APK
try:
    p = A + '/AndroidManifest.xml'
    m = open(p, encoding='utf-8').read()
    add = ''
    for q in ('android.permission.POST_NOTIFICATIONS', 'android.permission.USE_EXACT_ALARM',
              'android.permission.RECEIVE_BOOT_COMPLETED', 'android.permission.VIBRATE',
              'android.permission.REQUEST_INSTALL_PACKAGES'):
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

# 5) aktualizacje treści bez nowego APK (OTA): aplikacja sprawdza www/index.html na GitHubie
#    i przy następnym uruchomieniu używa nowszej wersji. Zmiany natywne nadal wymagają nowego APK.
OTA_SHELL = r'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<style>html,body{margin:0;background:#000}</style>
<script>
(function(){
var L=localStorage,B='__BUILD__',t=null;
try{
 var v=L.getItem('ota_try');
 if(v==='bad'||(+v||0)>=3){L.setItem('ota_bad',L.getItem('ota_h')||'');['ota_t','ota_h','ota_b','ota_try'].forEach(function(k){L.removeItem(k)})}
 else if(L.getItem('ota_b')===B&&L.getItem('ota_h')){t=L.getItem('ota_t');if(t)L.setItem('ota_try',String((+v||0)+1))}
}catch(e){t=null}
if(t){document.write(t.replace(/<head[^>]*>/i,function(m){return m+'<script src="ota.js"><\/script>'}))}
else{location.replace('app.html')}
})();
</script></head><body></body></html>
'''

OTA_JS = r'''(function(){
var B='__BUILD__',R='__REPO__',L=localStorage,bad=0;
window.addEventListener('error',function(e){if(/SyntaxError/.test(String(e&&e.message||''))||(e&&e.error&&e.error.name==='SyntaxError')){bad=1;try{L.setItem('ota_try','bad')}catch(x){}}});
var N=!!(window.Capacitor&&window.Capacitor.isNativePlatform&&window.Capacitor.isNativePlatform());
if(!N)return;
setTimeout(function(){if(!bad)try{if(L.getItem('ota_try')!=='bad')L.removeItem('ota_try')}catch(e){}},5000);
function H(s){var h=5381;for(var i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))|0;return s.length+':'+h}
function toast(m){try{var d=document.createElement('div');d.textContent=m;d.style.cssText='position:fixed;left:12px;right:12px;bottom:18px;z-index:99999;background:#222;color:#fff;padding:10px 14px;border-radius:10px;font:14px sans-serif;text-align:center;box-shadow:0 2px 10px #0008';document.body.appendChild(d);setTimeout(function(){d.remove()},5000)}catch(e){}}
var last=0;
function check(){
 if(Date.now()-last<300000||!navigator.onLine)return;last=Date.now();
 fetch('https://raw.githubusercontent.com/'+R+'/main/www/index.html?t='+Date.now(),{cache:'no-store'})
 .then(function(r){return r.ok?r.text():null}).then(function(t){
  if(!t||t.length<20000||t.indexOf('</html>')<0||t.indexOf('<script')<0)return;
  var h=H(t);
  if(h===L.getItem('ota_bad'))return;
  if(L.getItem('ota_h')===h&&L.getItem('ota_b')===B)return;
  try{
   ['ota_t','ota_h','ota_b'].forEach(function(k){L.removeItem(k)});
   L.setItem('ota_t',t);L.setItem('ota_h',h);L.setItem('ota_b',B);
   toast('Pobrano aktualizację – zobaczysz ją po ponownym uruchomieniu aplikacji')
  }catch(e){['ota_t','ota_h','ota_b'].forEach(function(k){L.removeItem(k)})}
 }).catch(function(){})
}
setTimeout(check,4000);
document.addEventListener('visibilitychange',function(){if(!document.hidden)setTimeout(check,2000)});
})();
'''

# 6) karta aktualizacji natywnej (tylko apka z APK): sprawdza najnowszy Release na GitHubie.
#    Pojawia się na środku ekranu na 3 s, potem zjeżdża w dół i ląduje WEWNĄTRZ listy Ustawienia, na jej
#    samym końcu (jako zwykły element listy, więc niczego nie zasłania). Gdy Ustawienia są zwinięte,
#    karta chowa się w środku, a przy napisie "Ustawienia" zapala się kropka, że czeka tam aktualizacja.
#    Po "Pobierz" aplikacja sama pobiera APK i uruchamia instalator Androida (wtyczka ApkInstaller).
#    Gdy wtyczki nie ma (stara wersja apki), otwiera link w przeglądarce.
#    Release po zmianie samego www/index.html jest pre-release, więc go ignoruje (to robi OTA).
UPD_JS = r'''(function(){
var B=+'__BUILD__'||0,R='__REPO__',L=localStorage,shown=0,busy=0;
if(!(window.Capacitor&&window.Capacitor.isNativePlatform&&window.Capacitor.isNativePlatform()))return;
function show(v,url){
 var d=document.createElement('div'),st=0,tm=0,dot=null,ph=null,gone=0;
 var BASE='background:var(--card,#171a1f);color:var(--tx,#eef0f3);border:1px solid var(--ac,#e8590c);border-radius:18px;padding:16px;text-align:center;font:15px/1.4 system-ui,-apple-system,sans-serif;';
 var FLOAT='position:fixed;left:12px;right:12px;max-width:536px;margin:0 auto;z-index:27;box-shadow:0 10px 34px rgba(0,0,0,.45);';
 var FLOW='position:relative;margin:0 12px 12px;box-shadow:none;';
 var bs='flex:1;border:0;border-radius:10px;padding:12px 8px;font:inherit;cursor:pointer;';
 d.style.cssText=BASE+FLOAT+'top:0;';
 d.innerHTML='<b style=\"display:block;font-size:17px\">Dostępna nowa wersja</b><div style=\"color:var(--mu,#8b94a1);font-size:13px;margin-top:2px\">Siłownia '+v+'</div><div style=\"display:flex;gap:10px;margin-top:12px\"><button id=\"upd_go\" style=\"'+bs+'background:var(--ac,#e8590c);color:#fff;font-weight:700\">Pobierz</button><button id=\"upd_no\" style=\"'+bs+'background:var(--ln,#262b33);color:inherit\">Później</button></div>';
 document.body.appendChild(d);
 d.style.top=Math.max(8,Math.round(innerHeight/2-d.offsetHeight/2))+'px';
 d.animate([{opacity:0,transform:'scale(.85)'},{opacity:1,transform:'scale(1)'}],{duration:380,easing:'cubic-bezier(.2,1.3,.4,1)'});
 function badge(on){var sm=document.querySelector('#sd>summary');if(!sm)return;if(on&&!dot){dot=document.createElement('span');dot.title='Nowa wersja';dot.style.cssText='display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--ac,#e8590c);margin-left:8px;vertical-align:middle';sm.appendChild(dot)}else if(!on&&dot){dot.remove();dot=null}}
 function inflow(){d.style.cssText=BASE+FLOW}
 function dock(){
  if(st!==0||gone)return;st=1;
  var host=document.getElementById('sd'),r0=d.getBoundingClientRect();
  if(!host){d.style.top='auto';d.style.bottom='calc(16px + env(safe-area-inset-bottom,0px))';var r1=d.getBoundingClientRect();d.animate([{transform:'translateY('+Math.round(r0.top-r1.top)+'px)'},{transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.9,.3,1)'});return}
  if(!host.open){var a=d.animate([{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(40px)'}],{duration:450,easing:'ease-in',fill:'forwards'});a.onfinish=function(){a.cancel();if(gone)return;inflow();host.appendChild(d);badge(1)};return}
  ph=document.createElement('div');ph.style.cssText='margin:0 12px 12px;height:'+d.offsetHeight+'px';host.appendChild(ph);
  d.style.right='auto';d.style.margin='0';d.style.width=r0.width+'px';d.style.left=r0.left+'px';
  var t0=performance.now();
  (function f(now){
   if(gone)return;
   var p=Math.min(1,(now-t0)/700),e=1-Math.pow(1-p,3),t=ph.getBoundingClientRect();
   if(!t.width){inflow();ph.replaceWith(d);ph=null;badge(1);return}
   d.style.left=(r0.left+(t.left-r0.left)*e)+'px';d.style.top=(r0.top+(t.top-r0.top)*e)+'px';d.style.width=(r0.width+(t.width-r0.width)*e)+'px';
   if(p<1)requestAnimationFrame(f);else{inflow();ph.replaceWith(d);ph=null}
  })(t0);
 }
 function close(){gone=1;clearTimeout(tm);d.style.pointerEvents='none';var a=d.animate([{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(30px)'}],{duration:350,easing:'ease-in',fill:'forwards'});a.onfinish=function(){badge(0);if(ph)ph.remove();d.remove()}}
 tm=setTimeout(dock,3380);
 d.querySelector('#upd_no').onclick=function(){close()};
 d.querySelector('#upd_go').onclick=function(){
  if(st===2)return;clearTimeout(tm);
  st=2;try{L.setItem('upd_dl',String(Date.now()))}catch(e){}
  function msg(t,s){d.innerHTML='<b style=\"display:block;font-size:17px\">'+t+'</b><div style=\"color:var(--mu,#8b94a1);font-size:13px;margin-top:4px\">'+s+'</div>'}
  var P=window.Capacitor.Plugins&&window.Capacitor.Plugins.ApkInstaller;
  if(!P){msg('Pobieranie ruszyło','Gdy plik się pobierze, otwórz go z powiadomienia i potwierdź instalację.');try{window.open(url,'_blank')}catch(e){}setTimeout(close,3500);return}
  msg('Pobieranie…','Za chwilę pojawi się okno instalacji.');
  P.install({url:url}).then(function(){setTimeout(close,2500)}).catch(function(e){
   try{L.removeItem('upd_dl')}catch(x){}
   if(String(e&&e.message||e).indexOf('need_permission')>=0){msg('Potrzebna zgoda','Włącz zezwolenie dla Siłowni, wróć do aplikacji i dotknij Pobierz jeszcze raz.')}
   else{msg('Nie udało się','Otwieram pobieranie w przeglądarce.');try{window.open(url,'_blank')}catch(x){}}
   setTimeout(close,5000)})
 }
}
function check(){
 var lc=0;try{lc=+L.getItem('upd_chk')||0}catch(e){}
 if(shown||busy||!navigator.onLine||Date.now()-lc<3600000)return;
 var dl=0;try{dl=+L.getItem('upd_dl')||0}catch(e){}
 if(Date.now()-dl<1800000)return;
 busy=1;
 fetch('https://api.github.com/repos/'+R+'/releases/latest',{cache:'no-store',headers:{Accept:'application/vnd.github+json'}})
 .then(function(r){return r.ok?r.json():null}).then(function(j){
  busy=0;if(j)try{L.setItem('upd_chk',String(Date.now()))}catch(e){}
  if(!j||j.draft||j.prerelease)return;
  var m=/(\d+)/.exec(j.tag_name||''),n=m?+m[1]:0;if(!n||n<=B)return;
  var u='',a=j.assets||[];for(var i=0;i<a.length;i++)if(/\.apk$/i.test(a[i].name||'')){u=a[i].browser_download_url;break}
  if(!u)return;shown=1;show('2.'+n,u)
 }).catch(function(){busy=0})
}
setTimeout(check,6000);
document.addEventListener('visibilitychange',function(){if(!document.hidden)setTimeout(check,2500)});
})();
'''

try:
    if not os.path.isfile('www/index.html'): raise Exception('brak www/index.html')
    build = os.environ.get('GITHUB_RUN_NUMBER', '1')
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    if not repo: raise Exception('brak GITHUB_REPOSITORY')
    app = open('www/index.html', encoding='utf-8').read()
    app = re.sub(r'<head[^>]*>', lambda m: m.group(0) + '<script src="ota.js"></script>', app, count=1, flags=re.I)
    open('www/app.html', 'w', encoding='utf-8').write(app)
    open('www/index.html', 'w', encoding='utf-8').write(OTA_SHELL.replace('__BUILD__', build))
    open('www/ota.js', 'w', encoding='utf-8').write((OTA_JS + UPD_JS).replace('__BUILD__', build).replace('__REPO__', repo))
    log('OTA włączone, repo:', repo, 'build:', build)
except Exception as e: log('UWAGA OTA (aplikacja działa bez aktualizacji z GitHuba):', e)

# 7) natywna instalacja APK: wtyczka Capacitora (pobiera plik i uruchamia instalator Androida)
PLUGIN_JAVA = r'''package __PKG__;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import androidx.core.content.FileProvider;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

@CapacitorPlugin(name = "ApkInstaller")
public class ApkInstallerPlugin extends Plugin {
    @PluginMethod
    public void install(final PluginCall call) {
        final String url = call.getString("url");
        final Context ctx = getContext();
        if (url == null || !url.startsWith("https://")) { call.reject("bad_url"); return; }
        if (Build.VERSION.SDK_INT >= 26 && !ctx.getPackageManager().canRequestPackageInstalls()) {
            Intent s = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + ctx.getPackageName()));
            s.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            ctx.startActivity(s);
            call.reject("need_permission");
            return;
        }
        new Thread(new Runnable() {
            public void run() {
                try {
                    File dir = new File(ctx.getCacheDir(), "updates");
                    dir.mkdirs();
                    File f = new File(dir, "update.apk");
                    if (f.exists()) f.delete();
                    HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                    c.setInstanceFollowRedirects(true);
                    c.setConnectTimeout(15000);
                    c.setReadTimeout(30000);
                    if (c.getResponseCode() != 200) { call.reject("http_" + c.getResponseCode()); return; }
                    InputStream in = c.getInputStream();
                    FileOutputStream out = new FileOutputStream(f);
                    byte[] buf = new byte[65536];
                    int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                    out.close(); in.close();
                    Uri uri = FileProvider.getUriForFile(ctx, ctx.getPackageName() + ".fileprovider", f);
                    Intent i = new Intent(Intent.ACTION_VIEW);
                    i.setDataAndType(uri, "application/vnd.android.package-archive");
                    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                    ctx.startActivity(i);
                    call.resolve();
                } catch (Exception e) {
                    call.reject("fail: " + e.getMessage());
                }
            }
        }).start();
    }
}
'''

try:
    mains = glob.glob(A + '/java/**/MainActivity.java', recursive=True)
    if not mains: raise Exception('brak MainActivity.java')
    mp = mains[0]
    ms = open(mp, encoding='utf-8').read()
    pkg = re.search(r'^package\s+([\w.]+);', ms, re.M).group(1)
    open(os.path.join(os.path.dirname(mp), 'ApkInstallerPlugin.java'), 'w', encoding='utf-8').write(
        PLUGIN_JAVA.replace('__PKG__', pkg))
    if 'ApkInstallerPlugin' not in ms:
        new_cls = ('public class MainActivity extends BridgeActivity {\n'
                   '    @Override\n'
                   '    public void onCreate(android.os.Bundle savedInstanceState) {\n'
                   '        registerPlugin(ApkInstallerPlugin.class);\n'
                   '        super.onCreate(savedInstanceState);\n'
                   '    }\n}\n')
        ms2 = re.sub(r'public class MainActivity extends BridgeActivity\s*\{\s*\}', new_cls, ms, count=1)
        if ms2 == ms: raise Exception('nietypowy MainActivity')
        open(mp, 'w', encoding='utf-8').write(ms2)
    if 'fileprovider' not in open(A + '/AndroidManifest.xml', encoding='utf-8').read().lower():
        log('UWAGA: brak FileProvider w manifeście')
    log('wtyczka ApkInstaller dodana, pakiet:', pkg)
except Exception as e: log('UWAGA instalator APK:', e)

# 8) STAŁY KLUCZ PODPISU: jawnie wskazujemy native/debug.keystore (alias androiddebugkey, hasło android).
#    Gdy się nie uda, build się przerywa (lepiej błąd niż losowy klucz i brak aktualizacji).
p = 'android/app/build.gradle'
g = open(p, encoding='utf-8').read()
ks = os.path.abspath('native/debug.keystore').replace('\\', '/')
if not os.path.isfile(ks): raise SystemExit('BRAK native/debug.keystore – przerywam build')
if 'signingConfigs.fixed' not in g:
    sc = ("    signingConfigs {\n        fixed {\n            storeFile file('%s')\n"
          "            storePassword 'android'\n            keyAlias 'androiddebugkey'\n"
          "            keyPassword 'android'\n        }\n    }\n") % ks
    g2 = re.sub(r'(\n\s*android\s*\{\n)', lambda m: m.group(1) + sc, g, count=1)
    if g2 == g: raise SystemExit('Nie znaleziono bloku android { w build.gradle')
    g3 = re.sub(r'(\n\s*buildTypes\s*\{\n)', lambda m: m.group(1) + '        debug {\n            signingConfig signingConfigs.fixed\n        }\n', g2, count=1)
    if g3 == g2: raise SystemExit('Nie znaleziono bloku buildTypes { w build.gradle')
    open(p, 'w', encoding='utf-8').write(g3)
log('stały klucz podpisu ustawiony:', ks)
