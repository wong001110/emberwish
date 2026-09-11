"""Windows-only tests against the real Tauri process/WebView2 over W3C WebDriver.
Uses Python stdlib, tauri-driver and Microsoft EdgeDriver. No mocked native API.
The test owns a fresh CI user's app data; do not run against a personal session.
"""
from pathlib import Path
import base64, json, os, shutil, subprocess, time, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'.reports';REPORT.mkdir(exist_ok=True)
if os.name!='nt' or os.getenv('CI')!='true':raise SystemExit('Native automation is restricted to Windows CI to avoid touching a personal session')
EXE=ROOT/'src-tauri/target/debug/emberwish.exe'
log=(REPORT/'tauri-driver.log').open('w',encoding='utf-8')
proc=subprocess.Popen([shutil.which('tauri-driver') or 'tauri-driver'],stdout=log,stderr=subprocess.STDOUT)
BASE='http://127.0.0.1:4444'
session=None;results=[]
def request(method,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=40) as response:return json.load(response).get('value')
    except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode()) from e

def execute(script,args=None,asynchronous=False):
    return request('POST',f'/session/{session}/execute/'+('async' if asynchronous else 'sync'),{'script':script,'args':args or []})
def invoke(command,args=None):
    value=execute("const done=arguments[arguments.length-1];window.__TAURI__.core.invoke(arguments[0],arguments[1]).then(value=>done({ok:true,value}),e=>done({ok:false,error:String(e)}));",[command,args or {}],True)
    if not value.get('ok'):raise RuntimeError(value.get('error'))
    return value.get('value')
def wait(predicate,seconds=30):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if predicate():return
        time.sleep(.15)
    raise AssertionError('Timed out waiting for native condition')
def element(css):
    value=request('POST',f'/session/{session}/element',{'using':'css selector','value':css})
    return value['element-6066-11e4-a52e-4f735466cecf']
def click(css):request('POST',f'/session/{session}/element/{element(css)}/click',{})
def start():
    global session
    value=request('POST','/session',{'capabilities':{'alwaysMatch':{'browserName':'wry','tauri:options':{'application':str(EXE)}}}})
    session=value['sessionId']
    wait(lambda:execute("return Boolean(window.__TAURI__ && document.querySelector('#light') && !document.querySelector('#light').disabled)"))
def stop():
    global session
    if session:
        try:invoke('desktop_action',{'action':'quit'})
        except Exception:pass
        try:request('DELETE',f'/session/{session}')
        except Exception:pass
        session=None
try:
    def driver_ready():
        if proc.poll() is not None:raise RuntimeError('tauri-driver exited before session creation')
        try: return request('GET','/status') is not None
        except (OSError, RuntimeError): return False
    wait(driver_ready)
    start()
    assert execute("return document.body.classList.contains('native')")
    assert not execute("return document.querySelector('#notice').textContent"),'Native startup raised a notice'
    results.append('real WebView2 app initialized without a mock bridge')
    invoke('desktop_action',{'action':'expand'})
    el=element('#wish');request('POST',f'/session/{session}/element/{el}/value',{'text':'A native wish','value':list('A native wish')})
    click('#light');wait(lambda:execute("return document.querySelector('#status-text').textContent==='A wish is quietly burning'"))
    wait(lambda: json.loads(invoke('load_state') or '{}').get('ritual',{}).get('status')=='burning')
    snapshot=json.loads(invoke('load_state'));assert snapshot['ritual']['wish']=='A native wish'
    results.append('real UI lighting reached bounded native file persistence')
    for bad in ['{}','x'*16385]:
        try:invoke('save_state',{'json':bad})
        except RuntimeError:pass
        else:raise AssertionError('Native backend accepted invalid data')
    assert json.loads(invoke('load_state'))==snapshot
    try:invoke('desktop_action',{'action':'run_shell'})
    except RuntimeError:pass
    else:raise AssertionError('Unknown native action was accepted')
    results.append('invalid native input rejected without changing saved state')
    png=request('GET',f'/session/{session}/screenshot');(REPORT/'native-expanded.png').write_bytes(base64.b64decode(png))
    click('#compact');wait(lambda:execute("return document.body.classList.contains('compact')"))
    assert execute('return innerWidth')<=320
    invoke('desktop_action',{'action':'pin'});invoke('desktop_action',{'action':'unpin'})
    png=request('GET',f'/session/{session}/screenshot');(REPORT/'native-compact.png').write_bytes(base64.b64decode(png))
    results.append('compact/expand native sizing and pin commands completed')
    invoke('desktop_action',{'action':'hide'});time.sleep(.2)
    count=execute("return Number(document.querySelector('#incense').dataset.renderCount)");time.sleep(.4)
    assert count==execute("return Number(document.querySelector('#incense').dataset.renderCount)"),'Hidden scene kept rendering'
    second=subprocess.Popen([str(EXE)]);second.wait(timeout=15)
    wait(lambda:execute("return Number(document.querySelector('#incense').dataset.renderCount)")>count)
    results.append('native hide stops drawing; second instance restores visibility and interaction')
    stop();time.sleep(.4);start()
    assert json.loads(invoke('load_state'))['ritual']['startedAt']==snapshot['ritual']['startedAt']
    wait(lambda:execute("return document.querySelector('#status-text').textContent==='A wish is quietly burning'"))
    results.append('actual process restart retains the original ritual deadline')
    stop()
    print(json.dumps({'passed':len(results),'checks':results,'not_tested':['tray-menu pointer interaction','real underlay click routing','monitor hotplug/DPI','physical-machine power profile']},indent=2))
finally:
    stop()
    if proc.poll() is None:proc.terminate()
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:proc.kill()
    log.close()
    (REPORT/'native.json').write_text(json.dumps({'checks':results,'note':'Partial native checks only; no implied tray, input-underlay, DPI or power acceptance.'},indent=2),encoding='utf-8')
