from pathlib import Path
import re, json, base64
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
old=next((P.parent/'practice-3').glob('*.html'))
new=[P/n for n in ['index.html','components.html','tokens.css','styles.css','app.js']]
def count(files):
    s='\n'.join(p.read_text() for p in files)
    return {'colors':sorted(set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,6}\b',s))), 'px':sorted(set(map(int,re.findall(r'(\d+)px\b',s))))}
print('BEFORE',count([old]));print('AFTER',count(new))
checks=[]
def check(name, ok):
    checks.append((name,bool(ok))); assert ok,name
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def load(mode=None, gallery=False):
        global page
        size=page.viewport_size
        page.close()
        page=browser.new_page(viewport=size,device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_default_timeout(5000)
        html=(P/('components.html' if gallery else 'index.html')).read_text()
        for css in ['tokens.css','styles.css']:
            html=html.replace(f'<link rel="stylesheet" href="{css}">','<style>'+ (P/css).read_text()+'</style>')
        for img in (P/'assets').glob('*.jpg'):
            html=html.replace('assets/'+img.name,'data:image/jpeg;base64,'+base64.b64encode(img.read_bytes()).decode())
        if not gallery:
            js=(P/'app.js').read_text().replace('location.search',repr('?state='+mode if mode else ''))
            html=html.replace('<script defer src="app.js"></script>','').replace('</body>','<script>'+js+'</script></body>')
        page.set_content(html,wait_until='load')
        if mode!='loading':page.evaluate('window.scrollTo(0,0)')
    load();check('Поля изначально пустые',all(not page.locator('#'+i).input_value() for i in ['cv','url','job']));check('Четыре локальные фотографии загружены',page.locator('.step-photo').count()==4 and page.locator('.step-photo').evaluate_all('els=>els.every(e=>e.complete&&e.naturalWidth>0)'));page.screenshot(path=str(P/'screenshots/01-landing.png')); widths=page.locator('.step').evaluate_all('els=>els.map(e=>e.offsetWidth)');hero_height=page.locator('#home').evaluate('e=>e.offsetHeight');page.locator('.step').first.hover();page.wait_for_timeout(450);check('Этап раскрывается при наведении',page.locator('.step').first.evaluate('e=>e.offsetWidth')>widths[0]);check('Высота главного экрана стабильна при наведении',page.locator('#home').evaluate('e=>e.offsetHeight')==hero_height);page.screenshot(path=str(P/'screenshots/17-step-hover.png'));page.mouse.move(0,0);page.locator('#form-section').scroll_into_view_if_needed();page.screenshot(path=str(P/'screenshots/02-input.png'))
    check('Форма: одинаковая ширина и высота полей',page.evaluate("""()=>{const a=document.querySelector('#cv').getBoundingClientRect(),b=document.querySelector('#job').getBoundingClientRect();return Math.abs(a.width-b.width)<1&&Math.abs(a.height-b.height)<1&&Math.abs(a.top-b.top)<1}"""))
    check('Форма: выровнены зоны файла и ссылки',page.evaluate("""()=>{const a=document.querySelector('#drop').getBoundingClientRect(),b=document.querySelector('.link-entry').getBoundingClientRect();return Math.abs(a.width-b.width)<1&&Math.abs(a.height-b.height)<1&&Math.abs(a.top-b.top)<1}"""))
    check('Нет учебных подписей на главной',page.evaluate("()=>!(/практика|учебный проект|учебный прототип/i.test(document.title+' '+document.body.innerText))"))
    page.locator('#submit').click();check('Пустая форма: подсказки и фокус',page.locator('#cv-error').is_visible() and page.locator('#job-error').is_visible() and page.locator('#cv').evaluate('(e)=>e===document.activeElement'))
    page.screenshot(path=str(P/'screenshots/03-validation.png'))
    page.locator('#file').set_input_files({'name':'wrong.exe','mimeType':'text/plain','buffer':b'abc'});check('Неверный формат файла',page.locator('#drop').get_attribute('data-state')=='error')
    page.screenshot(path=str(P/'screenshots/15-invalid-file.png'));page.locator('#file').set_input_files({'name':'resume.pdf','mimeType':'application/pdf','buffer':b'%PDF-demo'});check('Выбор файла с явным ограничением',page.locator('#drop').get_attribute('data-state')=='ready');page.locator('#remove-file').click()
    page.locator('#file').set_input_files({'name':'resume.txt','mimeType':'text/plain','buffer':b'Python developer'});page.wait_for_function("document.getElementById('cv').value==='Python developer'");check('TXT читается и показывает подтверждение',page.locator('#cv-status').is_visible());page.screenshot(path=str(P/'screenshots/16-valid-file.png'));page.locator('#remove-file').click()
    page.locator('#example').click();check('Резюме из PDF и пометка учебной вакансии', 'шестилетним' in page.locator('#cv').input_value() and 'не подтверждены' in page.locator('#vacancy-origin').inner_text());page.locator('#submit').click();check('Блокировка повторной отправки',page.locator('#submit').is_disabled());check('Индикатор на форме справа снизу',page.locator('#input-page').is_visible() and page.locator('#feedback').is_visible() and page.locator('#feedback').evaluate("e=>getComputedStyle(e).position==='fixed'"));page.wait_for_selector('#result',state='visible');check('Успех после перехода',page.locator('#feedback').get_attribute('data-kind')=='success' and page.locator('#feedback').is_visible());check('Семь требований',page.locator('.requirement').count()==7);check('Три статуса',all(page.locator(f'.summary [data-status={s}]').count()==1 for s in ['yes','check','no']))
    page.locator('.requirement').nth(4).click();check('Подсветка и уточнение',page.locator('#source mark').count()==1 and page.locator('#question').is_visible());page.locator('#answer').fill('Учебный проект по базам данных.');page.locator('#save-answer').click();check('Черновик только из ответа',page.locator('#draft-text').inner_text()=='Учебный проект по базам данных.')
    page.locator('#back').click();check('Данные сохранены при возврате',bool(page.locator('#cv').input_value()));page.locator('#submit').click();page.locator('#cancel').click();check('Отмена загрузки',page.locator('#input-page').is_visible() and page.locator('#submit').is_enabled())
    for state,filename in [('empty','04-empty'),('loading','05-loading'),('error','06-error'),('result','07-result'),('uncertain','08-uncertain'),('stress','09-stress')]:
        load(state);page.wait_for_timeout(150);page.screenshot(path=str(P/f'screenshots/{filename}.png'),full_page=state in ['result','uncertain']);check(f'{state}: нет горизонтального переполнения',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        if state=='error':
            page.locator('#retry').click();page.wait_for_selector('#result',state='visible');check('Повтор после ошибки',page.locator('.requirement').count()==7)
        if state=='stress':
            check('1000 требований',page.locator('.requirement').count()==1000)
            page.locator('.requirement').first.click(); long='Длинный ответ о выполненном проекте. '*100;page.locator('#answer').fill(long);page.locator('#save-answer').click();check('Длинный ответ не обрезан',page.locator('#draft-text').inner_text()==long.strip() and page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    load(gallery=True)
    page.screenshot(path=str(P/'screenshots/10-components.png'),full_page=True)
    page.locator('#button-specimen').screenshot(path=str(P/'screenshots/13-button-states.png'))
    check('Матрица: два типа × шесть состояний',page.locator('.button-matrix .btn').count()==12)
    for name in ['primary','secondary']:
        b=page.locator('#demo-'+name)
        b.hover();page.wait_for_timeout(250)
        check(name+': плавное наведение',b.evaluate("e=>getComputedStyle(e).transform!=='none' && getComputedStyle(e).transitionDuration.includes('0.22s')"))
        b.focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab')
        check(name+': видимый фокус клавиатуры',b.evaluate("e=>e.matches(':focus-visible') && getComputedStyle(e).outlineStyle==='solid'"))
        b.hover();page.mouse.down();page.wait_for_timeout(180)
        check(name+': анимация нажатия',b.evaluate("e=>new DOMMatrix(getComputedStyle(e).transform).a<1"))
        page.mouse.up()
        if not b.is_disabled(): b.click()
        check(name+': блокировка и спиннер',b.is_disabled() and b.get_attribute('aria-busy')=='true' and b.evaluate("e=>getComputedStyle(e,'::before').animationName==='spin'"))
        if name=='primary':page.locator('#button-specimen').screenshot(path=str(P/'screenshots/14-button-loading.png'))
        page.wait_for_function("id=>!document.getElementById(id).disabled",arg='demo-'+name)
        check(name+': возврат после загрузки',b.is_enabled() and b.get_attribute('aria-busy') is None)
    page.emulate_media(reduced_motion='reduce');b=page.locator('#demo-primary');b.hover()
    check('Reduced motion: отключены переходы и смещения',b.evaluate("e=>getComputedStyle(e).transitionDuration==='0s' && getComputedStyle(e).transform==='none'"))
    b.click();check('Reduced motion: отключено вращение',b.evaluate("e=>getComputedStyle(e,'::before').animationName==='none'"));page.emulate_media(reduced_motion='no-preference')
    page.set_viewport_size({'width':390,'height':844});load('stress');check('Мобильный стресс: нет горизонтального скролла',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));page.screenshot(path=str(P/'screenshots/11-mobile-stress.png'))
    load();check('Мобильный ввод: нет горизонтального скролла',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));page.locator('#form-section').scroll_into_view_if_needed();page.screenshot(path=str(P/'screenshots/12-mobile-input.png'))
    check('Нет ошибок JavaScript',not errors);browser.close()
(P/'test-results.json').write_text(json.dumps({'before':count([old]),'after':count(new),'tests':checks},ensure_ascii=False,indent=2)+'\n')
print('PASS',len(checks))
