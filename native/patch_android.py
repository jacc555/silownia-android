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
#    Pojawia się na środku ekranu na 3 s, potem zjeżdża na dół i tam zostaje.
#    Po "Pobierz" pokazuje komunikat o starcie pobierania i sama się zamyka.
#    Release po zmianie samego www/index.html jest pre-release, więc go ignoruje (to robi OTA).
UPD_JS = r'''(function(){
var B=+'__BUILD__'||0,R='__REPO__',L=localStorage,shown=0,busy=0,last=0;
if(!(window.Capacitor&&window.Capacitor.isNativePlatform&&window.Capacitor.isNativePlatform()))return;
function show(v,url){
 var d=document.createElement('div'),st=0,tm=0;
 d.style.cssText='position:fixed;left:12px;right:12px;max-width:536px;margin:0 auto;bottom:calc(16px + env(safe-area-inset-bottom,0px));z-index:27;background:var(--card,#171a1f);color:var(--tx,#eef0f3);border:1px solid var(--ac,#e8590c);border-radius:18px;padding:16px;box-shadow:0 10px 34px rgba(0,0,0,.45);text-align:center;font:15px/1.4 system-ui,-apple-system,sans-serif';
 var bs='flex:1;border:0;border-radius:10px;padding:12px 8px;font:inherit;cursor:pointer;';
 d.innerHTML='<b style="display:block;font-size:17px">Dostępna nowa wersja</b><div style="color:var(--mu,#8b94a1);font-size:13px;margin-top:2px">Siłownia '+v+'</div><div style="display:flex;gap:10px;margin-top:12px"><button id="upd_go" style="'+bs+'background:var(--ac,#e8590c);color:#fff;font-weight:700">Pobierz</button><button id="upd_no" style="'+bs+'background:var(--ln,#262b33);color:inherit">Później</button></div>';
 document.body.appendChild(d);
 var r=d.getBoundingClientRect(),dy=Math.round(innerHeight/2-r.height/2-r.top);
 d.style.transform='translateY('+dy+'px)';
 d.animate([{opacity:0,transform:'translateY('+dy+'px) scale(.85)'},{opacity:1,transform:'translateY('+dy+'px) scale(1)'}],{duration:380,easing:'cubic-bezier(.2,1.3,.4,1)'});
 function dock(){if(st!==0)return;st=1;d.style.transform='none';d.animate([{transform:'translateY('+dy+'px)'},{transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.2,.9,.3,1)'})}
 function close(){d.style.pointerEvents='none';var a=d.animate([{opacity:1,transform:'translateY(0)'},{opacity:0,transform:'translateY(30px)'}],{duration:350,easing:'ease-in',fill:'forwards'});a.onfinish=function(){d.remove()}}
 tm=setTimeout(dock,3380);
 d.querySelector('#upd_no').onclick=function(){clearTimeout(tm);close()};
 d.querySelector('#upd_go').onclick=function(){
  if(st===2)return;clearTimeout(tm);
  if(st===0){d.style.transform='none';d.animate([{transform:'translateY('+dy+'px)'},{transform:'translateY(0)'}],{duration:450,easing:'cubic-bezier(.2,.9,.3,1)'})}
  st=2;try{L.setItem('upd_dl',String(Date.now()))}catch(e){}
  d.innerHTML='<b style="display:block;font-size:17px">Pobieranie ruszyło</b><div style="color:var(--mu,#8b94a1);font-size:13px;margin-top:4px">Gdy plik się pobierze, otwórz go z powiadomienia i potwierdź instalację.</div>';
  try{window.open(url,'_blank')}catch(e){}
  setTimeout(close,3500)}
}
function check(){
 if(shown||busy||!navigator.onLine||Date.now()-last<600000)return;
 var dl=0;try{dl=+L.getItem('upd_dl')||0}catch(e){}
 if(Date.now()-dl<1800000)return;
 last=Date.now();busy=1;
 fetch('https://api.github.com/repos/'+R+'/releases/latest',{cache:'no-store',headers:{Accept:'application/vnd.github+json'}})
 .then(function(r){return r.ok?r.json():null}).then(function(j){
  busy=0;if(!j||j.draft||j.prerelease)return;
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
