"""Real navigation/storage E2E. A blocked browser is a failed run, never a mock pass.
CI sets EMBERWISH_WEB_ROOT=dist after the production build. Offline compilation
is a separate local preview path and is reported as such.
"""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, shutil, subprocess, threading
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
report=ROOT/'.reports';report.mkdir(exist_ok=True)
webroot=os.getenv('EMBERWISH_WEB_ROOT')
if webroot:
    served=ROOT/webroot
else:
    subprocess.run([shutil.which('python') or 'python','tools/offline_preview.py'],cwd=ROOT,check=True)
    served=ROOT/'.preview'
if not (served/'index.html').exists():raise RuntimeError('Missing actual build index')
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(served)))
threading.Thread(target=server.serve_forever,daemon=True).start()
checks=[]
try:
 with sync_playwright() as p:
    executable=os.getenv('CHROMIUM_PATH') or shutil.which('chromium')
    browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),headless=True)
    page=browser.new_page(viewport={'width':1100,'height':860},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    url=f'http://127.0.0.1:{server.server_port}'
    page.goto(url);expect(page.locator('#light')).to_be_enabled()
    expect(page.locator('#sound')).not_to_be_checked()
    count=lambda:int(page.locator('#incense').get_attribute('data-render-count') or '0')
    page.wait_for_timeout(200);idle=count();page.wait_for_timeout(250);assert count()==idle,'Idle renderer did not stop'
    checks.append('idle renderer stopped; silent default')
    page.locator('#wish').fill('<b>部署平安</b>');page.locator('input[name="duration"][value="5"]').check()
    before=page.locator('#incense').evaluate('(c)=>c.toDataURL()')
    page.locator('#light').focus();page.keyboard.press('Enter')
    expect(page.locator('#status-text')).to_have_text('A wish is quietly burning')
    expect(page.locator('#wish')).to_be_disabled();expect(page.locator('#display-wish')).to_have_text('<b>部署平安</b>')
    assert page.locator('#display-wish b').count()==0,'Wish became HTML'
    page.wait_for_timeout(200);assert page.locator('#incense').evaluate('(c)=>c.toDataURL()')!=before
    checks.append('keyboard lighting and real canvas pixels; wish rendered as text')
    page.wait_for_function("JSON.parse(localStorage.getItem('emberwish.state.v1')).ritual.status === 'burning'")
    saved=page.evaluate("JSON.parse(localStorage.getItem('emberwish.state.v1'))")
    page.reload();expect(page.locator('#light')).to_be_enabled();expect(page.locator('#status-text')).to_have_text('A wish is quietly burning')
    assert page.evaluate("JSON.parse(localStorage.getItem('emberwish.state.v1')).ritual.startedAt")==saved['ritual']['startedAt']
    checks.append('real localStorage reload keeps original start time')
    page.locator('#motion').check();page.wait_for_timeout(120);still=count();page.wait_for_timeout(180);assert count()==still
    page.emulate_media(reduced_motion='reduce');expect(page.locator('#motion')).to_be_disabled();checks.append('reduced motion has no continuous smoke loop')
    page.screenshot(path=str(report/'ritual-expanded.png'),full_page=True)
    page.locator('#compact').click();expect(page.locator('body')).to_have_class('compact');expect(page.locator('#expand')).to_be_focused()
    page.set_viewport_size({'width':300,'height':440});page.wait_for_timeout(150)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Compact horizontal overflow'
    page.screenshot(path=str(report/'ritual-compact.png'),full_page=True)
    page.locator('#compact-light').click();expect(page.locator('#status-text')).to_have_text('Resting, until next time')
    page.locator('#expand').click();page.set_viewport_size({'width':420,'height':900});expect(page.locator('#light')).to_be_focused()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Mobile preview horizontal overflow'
    checks.append('compact/expand responsive controls, focus restoration, extinguish')
    page.evaluate("s=>{s.ritual.startedAt=Date.now()-400000;s.ritual.status='burning';s.ritual.endedAt=null;localStorage.setItem('emberwish.state.v1',JSON.stringify(s))}",saved)
    page.reload();expect(page.locator('#status-text')).to_have_text('A small ritual, complete')
    page.evaluate("localStorage.setItem('emberwish.state.v1','{broken')");page.reload();expect(page.locator('#light')).to_be_enabled();expect(page.locator('#notice')).to_be_visible()
    assert page.evaluate("localStorage.getItem('emberwish.state.v1')")=='{broken','Startup overwrote corrupt state'
    checks.append('elapsed completion and non-destructive corrupt-storage recovery')
    assert not errors,errors
    (report/'browser.json').write_text(json.dumps({'served':str(served.relative_to(ROOT)),'checks':checks,'page_errors':errors},indent=2),encoding='utf-8')
    print(json.dumps({'passed':len(checks),'checks':checks,'page_errors':errors},ensure_ascii=False))
    browser.close()
finally:
 server.shutdown();server.server_close()
