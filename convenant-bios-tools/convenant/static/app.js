'use strict';
const $ = id => document.getElementById(id);
let token = '', files = [], lastResult = null, preparation = null, selectedWrite = '';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function notice(message, error = false) {
  const node = $('notification'); node.hidden = false; node.textContent = message;
  node.classList.toggle('error', error);
}
function tab(name) {
  document.querySelectorAll('.page').forEach(n => n.classList.toggle('active', n.id === name));
  document.querySelectorAll('.nav').forEach(n => n.classList.toggle('active', n.dataset.tab === name));
  $('section-title').textContent = document.querySelector(`[data-tab="${name}"]`).textContent.trim().toUpperCase();
}
async function api(path, data, method = data === undefined ? 'GET' : 'POST') {
  const response = await fetch(path, {method, headers: {'X-Convenant-Token': token, 'Content-Type': 'application/json'},
    body: data === undefined ? undefined : JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Falha HTTP ${response.status}`);
  return result;
}
async function perform(task, message) {
  document.body.classList.add('busy');
  if (message) notice(message);
  try { await task(); } catch (error) { notice(error.message, true); }
  finally { document.body.classList.remove('busy'); }
}
function button(text, onClick, className = '') {
  const node = document.createElement('button'); node.textContent = text; node.className = className;
  node.addEventListener('click', onClick); return node;
}
function paragraph(text, className = '') {
  const node = document.createElement('p'); node.textContent = text; node.className = className; return node;
}
function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 10000);
}
async function downloadFile(file) {
  try {
    const response = await fetch('/api/download/' + file.id, {headers: {'X-Convenant-Token': token}});
    if (!response.ok) throw new Error('Não foi possível baixar o arquivo.');
    downloadBlob(await response.blob(), file.name);
  } catch (error) { notice(error.message, true); }
}
function result(title, data, summaries = [], artifacts = []) {
  lastResult = data; $('results').hidden = false; $('result-title').textContent = title;
  $('result-json').textContent = JSON.stringify(data, null, 2);
  $('result-summary').replaceChildren(...summaries.map(s => paragraph(s.text || s, s.className || '')));
  $('result-artifacts').replaceChildren(...artifacts.map(file => button('Salvar ' + file.name, () => downloadFile(file))));
  $('results').scrollIntoView({behavior: 'smooth', block: 'nearest'});
}
async function refreshFiles() {
  files = await api('/api/files');
  document.querySelectorAll('.file-select').forEach(select => {
    const old = select.value;
    select.replaceChildren(new Option('Selecione um arquivo…', ''),
      ...files.map(f => new Option(`${f.name} · ${(f.size / 1024 / 1024).toFixed(2)} MiB · ${f.sha256.slice(0, 8)}`, f.id)));
    if (files.some(f => f.id === old)) select.value = old;
  });
  const items = files.map(file => {
    const row = document.createElement('div'), text = document.createElement('div'), title = document.createElement('strong');
    row.className = 'file-item'; title.textContent = file.name;
    const detail = document.createElement('small'); detail.textContent = `${file.size.toLocaleString('pt-BR')} bytes · SHA-256 ${file.sha256}`;
    text.append(title, detail); row.append(text, button('Salvar BIN', () => downloadFile(file))); return row;
  });
  $('file-list').replaceChildren(...(items.length ? items : [paragraph('Adicione um BIN ou faça seu primeiro backup.')]));
}
function requiredFile(id) {
  if (!$(id).value) throw new Error('Selecione um arquivo para esta operação.');
  return $(id).value;
}
async function upload(selected) {
  for (const file of selected) {
    if (file.size === 0 || file.size > 16 * 1024 * 1024) throw new Error('Use arquivos de até 16 MiB.');
    const response = await fetch('/api/upload?name=' + encodeURIComponent(file.name),
      {method: 'POST', headers: {'X-Convenant-Token': token}, body: file});
    const data = await response.json(); if (!response.ok) throw new Error(data.error);
  }
  await refreshFiles(); notice(`${selected.length} arquivo(s) adicionado(s). Selecione abaixo para analisar.`);
}
async function hardware(payload) {
  const start = await api('/api/job', payload);
  notice('Autorize a operação no sistema. Aguarde a conclusão; não feche a ferramenta durante gravação.');
  let state = start;
  while (state.status === 'running') { await sleep(700); state = await api('/api/jobs/' + start.id); }
  await refreshFiles();
  result(state.ok ? 'Operação concluída' : 'Operação interrompida', state,
    [state.ok ? 'Confira o resultado e preserve os arquivos gerados.' : state.error], state.artifacts || []);
  if (!state.ok) throw new Error(state.error);
  return state;
}
document.querySelectorAll('[data-tab]').forEach(node => node.addEventListener('click', () => tab(node.dataset.tab)));
document.querySelectorAll('[data-go]').forEach(node => node.addEventListener('click', () => tab(node.dataset.go)));
$('upload').addEventListener('change', event => perform(() => upload([...event.target.files]), 'Adicionando arquivos à pasta local…'));
$('probe').addEventListener('click', () => perform(async () => {
  const state = await hardware({action: 'probe'}), p = state.result.permissions;
  const text = p.me ? `SPS: leitura ${p.me.read ? 'permitida' : 'bloqueada'}; gravação ${p.me.write ? 'permitida' : 'bloqueada'}.` :
    'Confira o log do motor para as permissões e os detalhes do chip.';
  result('Chip e permissões', state, [text, 'Esta consulta não altera o chip.']); notice('Consulta concluída.');
}, 'Consultando o controlador…'));
$('backup').addEventListener('click', () => perform(async () => {
  const region = document.querySelector('input[name="region"]:checked').value;
  const state = await hardware({action: 'backup', region}), data = state.result;
  const readings = data.reports.map(r => r.analysis);
  const errors = readings.some(a => a.issues?.length || (a.deep?.available && !a.deep.passed));
  result('Backup e comparação', state, [
    {text: data.identical ? 'As duas leituras são idênticas.' : 'As leituras são diferentes. Não use para gravação.', className: data.identical ? 'status-good' : 'status-bad'},
    errors ? 'A análise encontrou erros no conteúdo. Igualdade entre leituras não comprova integridade.' :
      region === 'sps' ? 'SPS isolado: integridade dos módulos não verificada.' : 'Confira a análise dos arquivos no relatório. Boot e recuperação integral não foram validados.'
  ], state.artifacts);
  notice(errors || !data.identical ? 'Backup salvo, mas não aprovado como imagem íntegra.' : 'Leituras concluídas e preservadas.', errors || !data.identical);
}, 'Preparando duas leituras…'));
$('analyze').addEventListener('click', () => perform(async () => {
  const report = await api('/api/analyze', {file: requiredFile('analysis-file')});
  const bad = report.issues.length || (report.deep.available && !report.deep.passed);
  const summaries = [{text: bad ? 'Foram encontrados erros. Não use este arquivo para gravação.' : 'As verificações executadas não encontraram erros estruturais.', className: bad ? 'status-bad' : 'status-good'},
    `Tamanho: ${report.size.toLocaleString('pt-BR')} bytes. SHA-256: ${report.sha256}`];
  if (report.bios_id) summaries.push(`Identificação: ${report.bios_id}. Perfil: ${report.profile}.`);
  if (report.microcodes?.length) summaries.push('Microcódigos: ' + report.microcodes.map(m => `${m.cpuid} / ${m.revision} (${m.checksum_valid ? 'checksum válido' : 'checksum inválido'})`).join('; '));
  if (report.sps_bup) summaries.push('BUP do SPS: ' + report.sps_bup.status + '. Os demais módulos SPS não foram verificados.');
  summaries.push(report.deep.available ? 'Descompressão conferida com UEFIExtract. Consulte os avisos no relatório.' : 'UEFIExtract não executado; descompressão não verificada.');
  summaries.push('Análise estática: não garante boot, estabilidade ou recuperação integral.');
  result('Análise do firmware', report, summaries); notice('Análise concluída.', !!bad);
}, 'Analisando estrutura, microcódigos e descompressão…'));
$('compare').addEventListener('click', () => perform(async () => {
  const report = await api('/api/compare', {first: requiredFile('compare-first'), second: requiredFile('compare-second')});
  const summaries = [{text: report.identical ? 'Os arquivos são idênticos byte a byte.' : 'Os arquivos são diferentes.', className: report.identical ? 'status-good' : ''}];
  if (report.code_excluding_first_512KiB_nvram) summaries.push('Código fora da NVRAM: ' + report.code_excluding_first_512KiB_nvram.different_bytes.toLocaleString('pt-BR') + ' bytes diferentes.');
  summaries.push('Diferenças entre versões de firmware não provam corrupção; compare capturas da mesma base.');
  result('Comparação de arquivos', report, summaries); notice('Comparação concluída.');
}, 'Comparando bytes…'));
$('extract').addEventListener('click', () => perform(async () => {
  const meta = await api('/api/extract', {file: requiredFile('analysis-file')}); await refreshFiles();
  result('Região BIOS extraída', meta, ['A região foi copiada sem reparos. Analise o arquivo antes de usar.'], [meta]);
  notice('Extração concluída.');
}, 'Extraindo região BIOS…'));
$('build').addEventListener('click', () => perform(async () => {
  const response = await api('/api/build', {base: requiredFile('build-base'), second: requiredFile('build-second'), v3: requiredFile('build-v3'), v4: requiredFile('build-v4')});
  await refreshFiles(); result('Candidata experimental gerada', response, ['Microcódigos v3/49 e v4/040 aplicados ao perfil 002. NVRAM preservada.', 'Não houve gravação. Boot, estabilidade e desempenho não foram testados.'], [response.file]);
  notice('Candidata e manifesto gerados.');
}, 'Conferindo referências e gerando candidata…'));
$('write-file').addEventListener('change', () => {preparation = null; $('open-confirm').disabled = true; $('write-summary').textContent = 'A imagem mudou. Prepare novamente.';});
$('prepare').addEventListener('click', () => perform(async () => {
  selectedWrite = requiredFile('write-file'); preparation = null; $('open-confirm').disabled = true;
  const state = await hardware({action: 'prepare', file: selectedWrite}); preparation = state.preparation;
  const d = state.result;
  $('write-summary').textContent = `Perfil ${d.profile}. SHA-256 ${d.candidate_sha256}. NVRAM: ${d.nvram_will_change ? 'será alterada para os valores da imagem' : 'idêntica à leitura atual'}. Dois backups prévios foram preservados. Preparação válida por 10 minutos.`;
  $('open-confirm').disabled = false; notice('Preparação concluída. Revise antes de confirmar a gravação.');
}, 'Fazendo backups e verificando a candidata…'));
$('open-confirm').addEventListener('click', () => {
  $('confirm-details').textContent = $('write-summary').textContent;
  $('write-ack').checked = false; $('write-phrase').value = ''; $('write-dialog').showModal();
});
$('cancel-write').addEventListener('click', () => $('write-dialog').close());
$('confirm-write').addEventListener('click', () => {
  if (!$('write-ack').checked || $('write-phrase').value !== 'GRAVAR BIOS') return notice('Confira os dados, marque a confirmação e digite GRAVAR BIOS.', true);
  $('write-dialog').close();
  perform(async () => {
    const key = preparation; preparation = null; $('open-confirm').disabled = true;
    const state = await hardware({action: 'write', file: selectedWrite, preparation: key, confirmation: 'GRAVAR BIOS', acknowledged: true});
    result('Gravação e leitura posterior', state, [state.result.message, 'O teste de inicialização continua pendente.'], state.artifacts);
    notice('A leitura posterior corresponde à imagem gravada.');
  }, 'GRAVAÇÃO: aguarde. Não desligue, reinicie ou feche a ferramenta.');
});
$('save-settings').addEventListener('click', () => perform(async () => {
  const tools = await api('/api/settings', {fpt: $('fpt-path').value.trim()}); renderTools(tools); notice('Caminho aplicado para esta sessão.');
}));
function renderTools(tools) {
  $('engine').textContent = tools.backend === 'fpt' ? 'Intel FPT / Windows' : 'flashrom / CachyOS';
  $('engine-state').textContent = tools[tools.backend] ? 'Motor encontrado · autorize cada operação' : 'Configure o motor na aba Ferramentas';
  $('tools-status').textContent = JSON.stringify(tools, null, 2);
}
$('export-result').addEventListener('click', () => downloadBlob(new Blob([JSON.stringify(lastResult, null, 2)], {type: 'application/json'}), 'convenant-relatorio.json'));
$('close-app').addEventListener('click', () => perform(async () => {await api('/api/shutdown', {}); notice('Ferramenta encerrada. Você pode fechar esta aba.');}));
async function init() {
  try {
    const config = await api('/api/config'); token = config.token;
    const h = config.inventory;
    $('platform').textContent = h.os + ' / ' + h.architecture;
    $('version').textContent = 'v' + config.version + ' · Windows + CachyOS';
    $('board').textContent = h.board || 'Não identificada'; $('bios').textContent = 'BIOS ' + (h.bios || 'não identificada');
    $('cpu').textContent = Array.isArray(h.cpus) ? h.cpus.join(' / ') || 'Não identificado' : h.cpus;
    $('memory').textContent = h.memory_bytes ? (h.memory_bytes / 1024 ** 3).toFixed(1) + ' GiB de memória' : 'Memória não identificada';
    $('data-directory').textContent = config.data_directory;
    renderTools(config.tools); await refreshFiles();
  } catch (error) { notice('Não foi possível iniciar: ' + error.message, true); }
}
init();
