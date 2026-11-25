from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os, base64, re
H=Path(__file__).resolve().parents[1]; Q=H/'qa'; checks=[]; errors=[]
def check(name,condition):
    checks.append({'check':name,'pass':bool(condition)})
    if not condition:print('FAIL',name,flush=True)
def shot(p,n):p.screenshot(path=str(Q/'current'/n),animations='disabled')
with sync_playwright() as w:
    b=w.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox']);p=b.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce');p.on('pageerror',lambda e:errors.append(str(e)))
    def load(mode=''):
        global p
        size=p.viewport_size; p.close(); p=b.new_page(viewport=size,reduced_motion='reduce');p.set_default_timeout(5000);p.on('pageerror',lambda e:errors.append(str(e)))
        html=(H/'index.html').read_text()
        for css in ['tokens','components']:
            html=html.replace(f'<link rel="stylesheet" href="static/css/{css}.css">','<style>'+ (H/f'static/css/{css}.css').read_text()+'</style>')
        html=re.sub(r'src="(static/assets/[^"]+)"',lambda m:'src="data:image/jpeg;base64,'+base64.b64encode((H/m[1]).read_bytes()).decode()+'"',html)
        js=(H/'static/js/app.js').read_text().replace('location.search',repr(mode))
        html=html.replace('<script defer src="static/js/app.js"></script>','').replace('</body>','<script>'+js+'</script></body>')
        p.set_content(html,wait_until='load');p.evaluate('document.fonts.ready')
    def no_overflow():return p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    for width,height in [(1440,1000),(390,844),(720,1000)]:
        p.set_viewport_size({'width':width,'height':height});load();check(f'{width}: главная без горизонтального скролла',no_overflow());check(f'{width}: фото загружены',p.locator('.step-photo').evaluate_all('(xs)=>xs.every(x=>x.complete&&x.naturalWidth>0)'));shot(p,f'{width}-landing.png');p.locator('#form-section').scroll_into_view_if_needed();shot(p,f'{width}-upload.png');check(f'{width}: форма без горизонтального скролла',no_overflow())
        for mode in ['empty','loading','error','result','uncertain']:
            load('?state='+mode);check(f'{width}: {mode} без горизонтального скролла',no_overflow());check(f'{width}: {mode} показан',p.locator('#feedback-progress' if mode=='loading' else '#result' if mode=='uncertain' else '#'+mode).is_visible());
            if width!=720:shot(p,f'{width}-{mode}.png')
        load('?state=stress');check(f'{width}: 1000 требований',p.locator('.requirement').count()==1000 and no_overflow());
    p.set_viewport_size({'width':1440,'height':1000});load();check('Поля изначально пусты',all(not p.locator('#'+i).input_value() for i in ['cv','url','job']));trace=[]
    for _ in range(13):
        p.keyboard.press('Tab');trace.append(p.evaluate('document.activeElement.id || document.activeElement.textContent.trim().slice(0,35)'))
    check('Tab достигает полей и примера', 'example' in trace and 'cv' in trace and 'url' in trace);check('Фокус видим',p.evaluate("getComputedStyle(document.activeElement).outlineStyle !== 'none'"));
    load();p.locator('#submit').focus();p.keyboard.press('Enter');check('Enter: валидация пустой формы',p.locator('#cv-error').is_visible() and p.locator('#cv').evaluate('(e)=>document.activeElement===e'))
    p.locator('#file').set_input_files({'name':'bad.exe','mimeType':'text/plain','buffer':b'abc'});check('Недопустимый формат',p.locator('#drop').get_attribute('data-state')=='error');p.locator('#remove-file').click()
    p.locator('#file').set_input_files({'name':'resume.txt','mimeType':'text/plain','buffer':b'Python, Git'});p.wait_for_function("document.getElementById('cv').value==='Python, Git'");check('TXT прочитан',p.locator('#cv-status').is_visible());p.locator('#remove-file').click()
    p.locator('#example').focus();p.keyboard.press('Space');check('Space: пример заполнен',bool(p.locator('#job').input_value()));p.locator('#submit').focus();p.keyboard.press('Enter');check('Загрузка и блокировка',p.locator('#feedback-progress').is_visible() and p.locator('#submit').is_disabled());p.keyboard.press('Escape');check('Escape: отмена',p.locator('#submit').is_enabled() and not p.locator('#feedback').is_visible());p.locator('#submit').focus();p.keyboard.press('Enter');p.wait_for_selector('#result',state='visible');check('Переход к результату',p.locator('.requirement').count()==7 and p.locator('#feedback').get_attribute('data-kind')=='success');check('Фокус после перехода',p.locator('#back').evaluate('(e)=>e===document.activeElement'));check('Индекс рассчитан',p.locator('#fit-percent').inner_text()=='79');
    p.locator('.requirement').nth(4).focus();p.keyboard.press('Enter');check('Цитата и уточнение',p.locator('#source mark').count()==1 and p.locator('#question').is_visible());p.locator('#answer').fill('Уточнение опыта <script>alert(1)</script>');p.locator('#save-answer').focus();p.keyboard.press('Enter');check('Безопасный вывод текста',p.locator('#draft-text').inner_text()=='Уточнение опыта <script>alert(1)</script>');p.locator('#back').focus();p.keyboard.press('Enter');check('Возврат сохраняет ввод',p.locator('#cv').input_value()!='');
    load('?state=error');p.locator('#retry').focus();p.keyboard.press('Enter');p.wait_for_selector('#result',state='visible');check('Повтор после ошибки',p.locator('.requirement').count()==7)
    p.set_content((H/'states.html').read_text());check('Каталог состояний',p.locator('iframe').count()==5);check('Нет JS ошибок',not errors);b.close()
(Q/'results.json').write_text(json.dumps({'tests':checks,'keyboard_tab_trace':trace,'js_errors':errors},ensure_ascii=False,indent=2));print(f'{sum(c["pass"] for c in checks)}/{len(checks)}',flush=True)
