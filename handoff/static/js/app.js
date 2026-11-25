const $ = id => document.getElementById(id);
const sampleURL = 'https://rostov.hh.ru/vacancy/139715357?query=Python&hhtmFrom=vacancy_search_list';
const sampleJob = "Python\nFastAPI\nPostgreSQL\nDocker\nPython и Django\nGit\nLinux";
const sampleCV = "Senior Python Engineer\n6 лет опыта\nPython, FastAPI, asyncio.\nPostgreSQL, ClickHouse, Redis, Apache Kafka.\nDocker, Git, Pytest.\nРазработка микросервисов, интеграция ML/AI, Agile.";
const labels = { yes: 'Есть', check: 'Проверьте', no: 'Нет' };
let rows = [], source = '', selected = 0, busy = false, timer = null, last = null, feedbackTimer = null, fileVersion = 0, fileBusy = false;

function page(result){ $('input-page').hidden = result; $('result-page').hidden = !result; window.scrollTo(0,0); if(result) $('back').focus({preventScroll:true}); }
function state(name){ for(const id of ['empty','error','result']) $(id).hidden = id !== name; page(true); }
function renderVacancyText(container, text, empty){ const lines = text.split(/\n+/).map(x=>x.trim()).filter(Boolean); if(!lines.length){ container.textContent = empty; container.classList.add('muted'); return; } container.classList.remove('muted'); container.textContent = lines.map((line, i) => `${i+1}. ${line}`).join('\n'); }
function syncVacancyPreview(){ const job=$('job').value.trim(); const node=$('vacancy-origin'); node.hidden=job!==sampleJob; node.textContent=job===sampleJob?'Пример Python-вакансии. Оригинал hh.ru недоступен; требования не подтверждены.':''; }
function fieldStatus(id){ const node = $(id + '-status'); const value = $(id).value.trim(); node.hidden = !value || $(id).hasAttribute('aria-invalid'); if(!value) return; if(id === 'url') node.textContent = '✓ Ссылка принята. Добавь описание ниже.'; if(id === 'cv') node.textContent = `✓ Текст принят · ${value.length} символов`; if(id === 'job') node.textContent = `✓ Текст принят · ${value.split(/\n+/).filter(Boolean).length} пунктов`; }
function fill(){ $('cv').value = sampleCV; $('job').value = sampleJob; $('url').value = sampleURL; for(const id of ['cv','job','url']) { clearError(id); fieldStatus(id); } syncVacancyPreview(); }
function error(id, msg){ $(id).setAttribute('aria-invalid','true'); $(id+'-error').textContent = msg; $(id+'-error').hidden = false; $(id+'-status').hidden = true; }
function clearError(id){ $(id).removeAttribute('aria-invalid'); $(id+'-error').hidden = true; }
function valid(id){ const v = $(id).value.trim(); let msg = ''; if(id==='cv' && !v) msg = 'Вставь текст резюме: из PDF/DOCX его нужно скопировать; TXT читается автоматически.'; if(id==='job' && !v) msg = 'Вставь описание выбранной вакансии или заполни пример.'; if(id==='url' && v){ try { const u = new URL(v); if(u.protocol !== 'https:') throw Error(); } catch { msg = 'Введи корректную HTTPS-ссылку или оставь поле пустым.'; } } if(msg){ error(id,msg); return false; } clearError(id); fieldStatus(id); return true; }
for(const id of ['cv','job','url']){ $(id).addEventListener('input', ()=>{ clearError(id); if(id==='url') $(id+'-status').hidden = !$(id).value.trim(); else fieldStatus(id); if(id==='job' || id==='url') syncVacancyPreview(); }); $(id).addEventListener('blur', ()=>{ if($(id).value.trim()) valid(id); }); }

async function filePicked(file){
  if(!file || busy) return;
  const version = ++fileVersion;
  fileBusy = false;
  const ext = file.name.split('.').pop().toLowerCase();
  const format = ['pdf','docx','txt'].includes(ext);
  const okay = format && file.size > 0 && file.size <= 5*1024*1024;
  $('drop').dataset.state = okay ? 'ready' : 'error';
  $('file-title').textContent = okay ? file.name : 'Файл не принят';
  $('file-title').className = 'file-name';
  $('remove-file').hidden = false;
  $('file-message').textContent = !format ? 'Недопустимый формат. Выбери PDF, DOCX или TXT.' : !file.size ? 'Файл пуст. Выбери файл с данными.' : file.size > 5*1024*1024 ? 'Файл больше 5 МБ. Выбери файл меньшего размера.' : `✓ Формат ${ext.toUpperCase()} подходит. ${ext==='txt' ? 'Читаем текст…' : 'Файл выбран; скопируй текст в поле ниже.'}`;
  if(okay && ext==='txt'){
    fileBusy = true;
    try {
      const value = await file.text();
      if(version !== fileVersion) return;
      if(!value.trim()) throw Error();
      $('cv').value = value;
      clearError('cv');
      fieldStatus('cv');
      $('file-message').textContent = '✓ Формат TXT подходит. Текст загружен.';
    } catch {
      if(version !== fileVersion) return;
      $('drop').dataset.state = 'error';
      $('file-message').textContent = 'Не удалось прочитать текст. Выбери другой файл.';
    } finally {
      if(version === fileVersion) fileBusy = false;
    }
  }
}
$('choose').onclick = () => $('file').click();
$('file').onchange = ()=> filePicked($('file').files[0]);
$('remove-file').onclick = ()=>{
  fileVersion++;
  fileBusy=false;
  $('file').value='';
  $('drop').dataset.state='idle';
  $('file-title').textContent='Перетащи файл сюда';
  $('file-title').className='';
  $('file-message').textContent='PDF, DOCX, TXT · до 5 МБ';
  $('remove-file').hidden=true;
};
for(const ev of ['dragenter','dragover']) $('drop').addEventListener(ev, e=>{ e.preventDefault(); $('drop').classList.add('is-drag'); });
for(const ev of ['dragleave','drop']) $('drop').addEventListener(ev, e=>{ e.preventDefault(); $('drop').classList.remove('is-drag'); if(ev==='drop') filePicked(e.dataTransfer.files[0]); });

function analyze(cv, job){
  const lines = cv.split(/\n/).filter(x=>x.trim());
  return job.split(/\n/).map(x=>x.trim()).filter(Boolean).map(name=>{
    const lower = name.toLocaleLowerCase('ru');
    const exact = lines.find(x=>x.toLocaleLowerCase('ru').includes(lower));
    const terms = lower.match(/[\p{L}\p{N}]+/gu)?.filter(x=>x.length > 3) || [];
    const partial = lines.find(x=>terms.some(t=>x.toLocaleLowerCase('ru').includes(t)));
    return {
      name,
      status: exact ? 'yes' : partial ? 'check' : 'no',
      quote: exact || partial || '',
      note: exact ? 'Найдено точное совпадение в тексте резюме.' : partial ? 'Есть частичное совпадение. Проверь формулировку опыта.' : 'Совпадение не найдено. Это не означает отсутствие опыта.'
    };
  });
}
function el(tag, cls, txt){ const n = document.createElement(tag); if(cls) n.className = cls; if(txt !== undefined) n.textContent = txt; return n; }
function select(i){
  selected = i;
  const r = rows[i];
  document.querySelectorAll('.requirement').forEach((n,j)=>n.setAttribute('aria-pressed', String(i===j)));
  const node = $('source');
  node.replaceChildren();
  const ix = r.quote ? source.indexOf(r.quote) : -1;
  if(ix >= 0){
    node.append(document.createTextNode(source.slice(0, ix)), el('mark','', r.quote), document.createTextNode(source.slice(ix + r.quote.length)));
  } else node.textContent = source;
  $('question').hidden = r.status === 'yes';
  $('question-text').textContent = `Есть ли у тебя реальный опыт по требованию «${r.name}»?`;
  $('answer').value='';
  $('draft').hidden=true;
}
function render(){
  const counts = { yes:0, check:0, no:0 };
  $('requirements').replaceChildren();
  $('summary').replaceChildren();
  rows.forEach((r,i)=>{
    counts[r.status]++;
    const b = $('requirement-template').content.firstElementChild.cloneNode(true);
    b.querySelector('[data-field="name"]').textContent = `${i+1}. ${r.name}`;
    const badge = b.querySelector('[data-field="status"]');
    badge.textContent = labels[r.status]; badge.dataset.status = r.status;
    b.querySelector('[data-field="quote"]').textContent = r.quote ? `Цитата: «${r.quote}»` : 'Цитата не найдена';
    b.querySelector('[data-field="note"]').textContent = r.note;
    b.onclick = ()=> select(i);
    $('requirements').append(b);
  });
  for(const k of Object.keys(counts)){
    const t = el('span','status', `${labels[k]} · ${counts[k]}`);
    t.dataset.status = k;
    $('summary').append(t);
  }
  const fit = rows.length ? Math.round(((counts.yes + counts.check * 0.5) / rows.length) * 100) : 0;
  $('fit-meter').style.setProperty('--percent', String(fit));
  $('fit-percent').textContent = String(fit);
  $('fit-note').textContent = $('job').value.trim()===sampleJob ? 'Демонстрационная оценка: не результат проверки реальной вакансии hh.ru.' : 'Индекс совпадений по введённому тексту. Не оценка вероятности трудоустройства.';
  $('result-origin').textContent = $('job').value.trim()===sampleJob ? 'Учебные требования Python-разработчика. Оригинал вакансии №139715357 недоступен.' : 'Описание введено пользователем.';
  $('score-number').textContent = `${counts.yes} / ${rows.length}`;
  $('score-fill').style.width = `${rows.length ? counts.yes / rows.length * 100 : 0}%`;
  $('done-text').textContent = `Проверено требований: ${rows.length}. Это локальная текстовая проверка.`;
  $('uncertain').hidden = counts.check === 0;
  const url = $('url').value.trim();
  $('selected-link').textContent = url ? url : 'Ссылка не указана.';
  renderVacancyText($('selected-vacancy'), $('job').value.trim(), 'Текст вакансии не заполнен.');
  state('result');
  if(rows.length) select(0);
}
function feedback(kind, title, text){
  clearTimeout(feedbackTimer);
  $('feedback').hidden=false;
  $('feedback').dataset.kind=kind;
  $('feedback-title').textContent=title;
  $('progress-text').textContent=text;
  $('feedback-icon').className = kind==='loading' ? 'spinner' : '';
  $('feedback-icon').textContent = kind==='success' ? '✓' : kind==='error' ? '!' : '';
  $('feedback-progress').hidden = kind !== 'loading';
  $('dismiss').hidden = kind === 'loading';
  if(kind==='success') feedbackTimer = setTimeout(()=>{ $('feedback').hidden=true; }, 7000);
}
$('dismiss').onclick = ()=>{ $('feedback').hidden=true; };
function lock(on){
  busy=on;
  for(const id of ['cv','job','url','choose','file','remove-file','example','hero-example','show-empty']) $(id).disabled = on;
  $('submit').disabled = on;
  if(on) $('submit').setAttribute('aria-busy','true'); else $('submit').removeAttribute('aria-busy');
  $('submit').textContent = on ? 'Сверяем…' : 'Сверить';
}
function stop(){ clearInterval(timer); timer=null; lock(false); $('feedback').hidden=true; clearTimeout(feedbackTimer); }
function start(cv, job, fail=false){
  if(busy) return;
  last={cv,job};
  page(false);
  $('form-section').scrollIntoView();
  lock(true);
  $('progress').value=0;
  feedback('loading','Сверяем резюме','Подготавливаем требования…');
  let step=0;
  timer = setInterval(()=>{
    step++;
    $('progress').value = step * 25;
    $('progress-text').textContent = ['','Читаем текст резюме…','Сопоставляем требования…','Формируем цитаты…','Готово'][step];
    if(step===4){
      stop();
      try {
        if(fail) throw Error();
        source=cv;
        rows=analyze(cv,job);
        render();
        feedback('success','Сверка завершена','Проверка закончена. Результат открыт.');
      } catch {
        state('error');
        feedback('error','Провести сверку не удалось','Сервис анализа не ответил. Данные сохранены. Повтори попытку.');
      }
    }
  }, 650);
}
$('form').onsubmit = e=>{
  e.preventDefault();
  if(busy) return;
  if(fileBusy){ feedback('error','Файл ещё читается','Дождись завершения загрузки текста.'); return; }
  if($('drop').dataset.state==='error'){ feedback('error','Файл не принят','Исправь формат или убери файл, чтобы продолжить.'); $('choose').focus(); return; }
  const errors = ['cv','url','job'].filter(id=>!valid(id));
  if(errors.length){ $(errors[0]).focus(); return; }
  start($('cv').value.trim(), $('job').value.trim(), new URLSearchParams(location.search).get('fail')==='1');
};
function back(){ stop(); page(false); $('form-section').scrollIntoView(); $('cv').focus({preventScroll:true}); }
$('back').onclick = back;
$('empty-back').onclick = back;
$('error-back').onclick = back;
$('cancel').onclick = back;
$('home-link').onclick = e=>{ e.preventDefault(); stop(); page(false); };
$('example').onclick = fill;
$('hero-example').onclick = ()=>{ fill(); start(sampleCV, sampleJob); };
$('show-empty').onclick = ()=> state(rows.length ? 'result' : 'empty');
$('retry').onclick = ()=>{ if(last) start(last.cv, last.job); };
$('save-answer').onclick = ()=>{ const answer = $('answer').value.trim(); if(!answer){ $('answer').focus(); return; } $('draft-text').textContent = answer; $('draft').hidden = false; };

const mode = new URLSearchParams(location.search).get('state');
syncVacancyPreview();
if(mode){
  fill();
  if(mode==='empty') state('empty');
  if(mode==='loading'){
    page(false); $('form-section').scrollIntoView(); lock(true); $('progress').value=50;
    feedback('loading','Сверяем резюме','Сопоставляем требования… (демонстрация состояния)');
  }
  if(mode==='error'){
    last={cv:sampleCV,job:sampleJob};
    state('error');
    feedback('error','Провести сверку не удалось','Сервис анализа не ответил. Данные сохранены. Повтори попытку.');
  }
  if(mode==='result'){
    source=sampleCV; rows=analyze(source,sampleJob); render();
    feedback('success','Сверка завершена','Проверка закончена. Результат открыт.');
  }
  if(mode==='stress'){
    source=sampleCV+'\n'+'Очень длинный фрагмент резюме без подтверждения. '.repeat(12);
    const job = Array.from({length:1000},(_,i)=>i===0 ? 'Очень длинное название требования к разработчику распределённых систем с большим количеством подробностей и уточнений' : `Требование ${i+1}`).join('\n');
    $('job').value = job; $('url').value = sampleURL; syncVacancyPreview(); rows=analyze(source,job); render();
  }
  if(mode==='uncertain'){
    source=sampleCV; rows=analyze(source,sampleJob); render(); select(4);
  }
}

document.addEventListener('keydown', e=>{if(e.key==='Escape' && !$('feedback').hidden){if(busy) back(); else $('dismiss').click();}});
