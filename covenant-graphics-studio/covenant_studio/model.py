"""Project links and in-memory tests. No ROM writer, EFI-variable access or flashing."""
from collections import defaultdict
from pathlib import Path
import base64
import copy
import csv
import hashlib
import io
import json
import math
import re
import struct
import uuid
import zipfile
import zlib

from .firmware import require, sha

VERSION = 1
MAX_PROJECT = 32 * 1024 * 1024
STATUS = {'linked':'Vínculo estrutural', 'review':'Revisar', 'unmatched':'Sem vínculo', 'manual':'Manual'}
VALUE_KINDS = ('oneof','checkbox','numeric')


def norm(value):
    text = ' '.join(value.casefold().split()).rstrip(' .:')
    return {'enabled':'enable','disabled':'disable'}.get(text,text)


def clean(value, limit=160):
    return ' '.join(str(value).split())[:limit]


def field_key(q):
    s = q.get('store') or {}
    return (q['module'],s.get('guid'),s.get('name'),norm(q['prompt']))


def slot(q):
    s = q['store']
    return '/'.join((s['guid'],s['name'],str(q['offset']),str(q['width'])))


def value_map(source, target):
    if source['kind'] not in VALUE_KINDS or target['kind'] not in VALUE_KINDS:
        return None, 'Tipos de controle incompatíveis.'
    if source['kind']=='numeric' or target['kind']=='numeric':
        if source['kind']!=target['kind']:
            return None, 'Campo numérico ligado a uma lista.'
        if (int(source['minimum']) < int(target['minimum'])
                or int(source['maximum']) > int(target['maximum'])
                or source['width']!=target['width']
                or source.get('signed')!=target.get('signed')):
            return None, 'Intervalo, sinal ou largura numérica diferente.'
        return {}, ''
    choices = defaultdict(set)
    for option in target['options']:
        choices[norm(option['label'])].add(option['value'])
    mapping = {}
    for option in source['options']:
        matches = choices[norm(option['label'])]
        if len(matches)!=1:
            return None, 'Há opções sem correspondência única.'
        v = next(iter(matches))
        if option['value'] in mapping and mapping[option['value']]!=v:
            return None, 'Um valor da origem tem interpretações diferentes.'
        mapping[option['value']] = v
    return (mapping,'') if mapping else (None,'Lista de opções ausente.')


def match_index(stock):
    questions=defaultdict(list);forms=defaultdict(list)
    for q in stock['questions']:
        if q.get('storage_valid') and q['kind'] in VALUE_KINDS:
            questions[field_key(q)].append(q)
    for f in stock['forms']:
        forms[(f['module'],norm(f['title']))].append(f)
    return {'questions':questions,'forms':forms}


def auto_match(question, stock, index=None):
    if index is None:
        index=match_index(stock)
    unmatched = {'target_kind':None,'target_id':None,'status':'unmatched','reason':'Sem correspondência única.','value_map':{}}
    if question['kind']=='ref':
        title = question.get('_target_title','')
        forms = index['forms'].get((question['module'],norm(title)),[])
        if title and len(forms)==1:
            return {'target_kind':'form','target_id':forms[0]['id'],'status':'review' if question['conditional'] else 'linked',
                    'reason':'Navegação por título e módulo; condição não executada.' if question['conditional'] else 'Formulário de destino identificado.', 'value_map':{}}
        return unmatched
    if question['kind'] not in VALUE_KINDS or not question.get('storage_valid'):
        return {**unmatched,'reason':'Ação/callback ou armazenamento sem suporte ao teste.'}
    candidates = index['questions'].get(field_key(question),[])
    same_form = [q for q in candidates if norm(q['form_title'])==norm(question['form_title'])]
    if same_form:
        candidates = same_form
    # Multiple IFR declarations at one storage slot can have different options/conditions.
    # Accept only when all remaining declarations agree, never select the first by guess.
    signatures = defaultdict(list)
    for q in candidates:
        sig = (slot(q),q['kind'],tuple((norm(o['label']),o['value']) for o in q['options']),
               q.get('minimum'),q.get('maximum'),q.get('step'),q.get('signed'),q['callback'],q['conditional'])
        signatures[sig].append(q)
    if len(signatures)!=1:
        return {**unmatched,'reason':'Mais de um campo candidato.' if candidates else unmatched['reason']}
    target = next(iter(signatures.values()))[0]
    mapping, error = value_map(question,target)
    if mapping is None:
        return {**unmatched,'reason':error}
    pending = question['callback'] or target['callback'] or question['conditional'] or target['conditional'] or target['read_only']
    return {'target_kind':'question','target_id':target['id'],'status':'review' if pending else 'linked',
            'reason':'Correspondência estrutural; callback/condição/leitura exige revisão.' if pending else 'Nome, variável, tipo e opções correspondem; offset traduzido.',
            'value_map':mapping}


def make_project(stock, donor, catalog, donor_sha):
    index=match_index(stock)
    project = {'format':'covenant-graphics-project','version':VERSION,'stock_sha256':stock['sha256'],
               'donor_catalog_sha256':donor_sha,'title':'Covenant','pages':[],'controls':[],
               'test_values':{},'asset_overrides':{},'firmware_compiler_implemented':False}
    def add_control(q, origin, page, row):
        target = None
        if origin=='stock':
            if q['kind']=='ref':
                forms = [f for f in stock['forms'] if f['form_id']==q.get('target_form_id') and f['formset']==q.get('target_formset')]
                if len(forms)==1:
                    target = {'target_kind':'form','target_id':forms[0]['id'],'status':'review' if q['conditional'] else 'linked','reason':'Referência original da 002.','value_map':{}}
            elif q['kind'] in VALUE_KINDS and q['storage_valid']:
                target = {'target_kind':'question','target_id':q['id'],
                          'status':'review' if q['callback'] or q['conditional'] or q['read_only'] else 'linked',
                          'reason':'Campo original da 002; condições/callbacks não são executados.',
                          'value_map':{o['value']:o['value'] for o in q['options']}}
        if target is None:
            target = auto_match(q,stock,index) if origin=='donor' else {'target_kind':None,'target_id':None,'status':'unmatched','reason':'Ação de firmware não executada.','value_map':{}}
        cid = origin[0]+'-'+sha(q['id'].encode())[:24]+'-'+sha(page.encode())[:8]
        project['controls'].append({'id':cid,'source_origin':origin,'source_id':q['id'],'page':page,
                                    'label':clean(q['prompt']) or 'Controle','rect':[.075,.22+row*.049,.85,.044],
                                    'asset':None,'hide_label':False,'shortcut':'','enabled':True,**target})
    # The first page uses actual 002 fields, with no donor variable assumptions.
    home = 'home'
    project['pages'].append({'id':home,'title':'Covenant · início','origin':'stock','form':None,'background':catalog['background']})
    pinned = [('CSM Support','Setup'),('Above 4G Decoding','Setup'),('Turbo Mode','IntelSetup'),
              ('Hyper-Threading [ALL]','IntelSetup'),('Numa','IntelSetup')]
    for prompt, variable in pinned:
        qs = [q for q in stock['questions'] if q['prompt']==prompt and q.get('store') and q['store']['name']==variable and q['storage_valid']]
        if len(qs)==1:
            add_control(qs[0],'stock',home,len([c for c in project['controls'] if c['page']==home]))
    for origin, data in (('stock',stock),('donor',donor)):
        lookup = {f['id']:f for f in data['forms']}
        for form in data['forms']:
            questions = [q for q in data['questions'] if q['form']==form['id']]
            for page_number in range(max(1,math.ceil(len(questions)/12))):
                page = f'{origin}:{form["id"]}:{page_number}'
                title = clean(form['title']) + (f' · {page_number+1}' if len(questions)>12 else '')
                project['pages'].append({'id':page,'title':title,'origin':origin,'form':form['id'],'background':catalog['background']})
                for row, original in enumerate(questions[page_number*12:(page_number+1)*12]):
                    q = dict(original)
                    if q['kind']=='ref':
                        targets = [f for f in data['forms'] if f['form_id']==q.get('target_form_id') and f['formset']==q.get('target_formset')]
                        if len(targets)==1:
                            q['_target_title'] = targets[0]['title']
                    add_control(q,origin,page,row)
    return project


def image_size(blob):
    require(len(blob)<=3*1024*1024, 'Imagem maior que 3 MiB.')
    if blob.startswith(b'\x89PNG\r\n\x1a\n'):
        require(len(blob)>=33 and blob[12:16]==b'IHDR', 'PNG inválido.')
        w,h = struct.unpack_from('>II',blob,16)
        pos = 8
        while pos+12<=len(blob):
            n = int.from_bytes(blob[pos:pos+4],'big');end=pos+n+12
            require(end<=len(blob), 'PNG truncado.')
            require(zlib.crc32(blob[pos+4:end-4])==int.from_bytes(blob[end-4:end],'big'),'CRC PNG inválido.')
            kind=blob[pos+4:pos+8];pos=end
            if kind==b'IEND':
                require(pos==len(blob), 'Dados após IEND.');break
        else:
            raise ValueError('PNG sem IEND.')
        require(0<w<=4096 and 0<h<=4096 and w*h<=8*1024*1024, 'Dimensões de imagem excessivas.')
        return w,h
    require(blob.startswith(b'\xff\xd8'), 'Use PNG ou JPEG.')
    pos=2
    for _ in range(4096):
        require(pos<len(blob) and blob[pos]==255, 'Marcador JPEG inválido.')
        while pos<len(blob) and blob[pos]==255:
            pos+=1
        require(pos<len(blob), 'JPEG truncado.')
        marker=blob[pos];pos+=1
        require(marker not in (0,0xD8,0xD9,0xDA), 'JPEG sem dimensões válidas.')
        if marker==1 or 0xD0<=marker<=0xD7:
            continue
        require(pos+2<=len(blob), 'JPEG truncado.')
        size=int.from_bytes(blob[pos:pos+2],'big')
        require(size>=2 and pos+size<=len(blob), 'Segmento JPEG truncado.')
        if marker in (0xC0,0xC1,0xC2):
            require(size>=8, 'SOF JPEG inválido.')
            h,w=struct.unpack_from('>HH',blob,pos+3)
            require(0<w<=4096 and 0<h<=4096 and w*h<=8*1024*1024, 'Dimensões de imagem excessivas.')
            return w,h
        pos+=size
    raise ValueError('JPEG excede o limite de segmentos.')


def validate_project(project, stock, donor, catalog, donor_sha):
    require(isinstance(project,dict) and project.get('format')=='covenant-graphics-project'
            and type(project.get('version')) is int and project['version']==VERSION,'Projeto inválido.')
    require(project.get('stock_sha256')==stock['sha256'] and project.get('donor_catalog_sha256')==donor_sha,
            'Este projeto pertence a outra BIOS ou catálogo gráfico.')
    require(project.get('firmware_compiler_implemented') is False,'O projeto não pode declarar um compilador de firmware.')
    require(isinstance(project.get('title'),str) and 1<=len(project['title'])<=160,'Título inválido.')
    pages,controls=project.get('pages'),project.get('controls')
    require(isinstance(pages,list) and 1<=len(pages)<=2048 and isinstance(controls,list) and len(controls)<=20000,'Projeto grande demais.')
    assets={i['id']:i for i in catalog['images']}
    page_ids=set();shortcuts=set();control_ids=set()
    questions={q['id']:q for q in stock['questions']};forms={f['id'] for f in stock['forms']}
    sources={'stock':questions,'donor':{q['id']:q for q in donor['questions']}}
    for p in pages:
        require(isinstance(p,dict) and isinstance(p.get('id'),str) and len(p['id'])<=1024 and p['id'] not in page_ids,'Página inválida ou repetida.')
        require(isinstance(p.get('title'),str) and 1<=len(p['title'])<=200 and p.get('origin') in ('stock','donor'),'Título/origem da página inválidos.')
        require(p.get('background') in assets,'Fundo não pertence ao catálogo.')
        form_ids={f['id'] for f in (stock if p['origin']=='stock' else donor)['forms']}
        require(p.get('form') is None or p['form'] in form_ids,'Formulário da página desconhecido.')
        page_ids.add(p['id'])
    for c in controls:
        require(isinstance(c,dict) and isinstance(c.get('id'),str) and 1<=len(c['id'])<=1024 and c['id'] not in control_ids,'Controle inválido ou repetido.')
        require(c.get('page') in page_ids and c.get('status') in STATUS,'Página/estado do vínculo inválido.')
        require(isinstance(c.get('label'),str) and 1<=len(c['label'])<=160 and all(ord(x)>=32 for x in c['label']),'Texto do controle inválido.')
        rect=c.get('rect')
        require(isinstance(rect,list) and len(rect)==4 and all(type(x) in (int,float) and math.isfinite(x) for x in rect),'Posição inválida.')
        x,y,w,h=rect
        require(0<=x<1 and 0<=y<1 and .005<=w<=1 and .005<=h<=1 and x+w<=1.000001 and y+h<=1.000001,'Controle fora da tela.')
        require(c.get('asset') is None or c['asset'] in assets,'Imagem desconhecida.')
        require(type(c.get('hide_label')) is bool and type(c.get('enabled')) is bool,'Flags inválidos.')
        hot=c.get('shortcut')
        require(isinstance(hot,str) and (hot=='' or re.fullmatch(r'F(?:[1-9]|1[0-2])|[A-Z0-9]',hot)),'Atalho inválido.')
        if hot and c['enabled']:
            require((c['page'],hot) not in shortcuts,'Atalho repetido na mesma página.');shortcuts.add((c['page'],hot))
        origin=c.get('source_origin');sid=c.get('source_id')
        require(origin in sources and (sid in sources[origin] or (origin=='stock' and sid is None and c['id'].startswith('custom-'))),'Origem do controle desconhecida.')
        tk,ti=c.get('target_kind'),c.get('target_id')
        require((tk is None and ti is None) or (tk=='question' and ti in questions) or (tk=='form' and ti in forms),'Destino não pertence à BIOS carregada.')
        vm=c.get('value_map')
        require(isinstance(vm,dict) and len(vm)<=512 and all(isinstance(k,str) and isinstance(v,str) for k,v in vm.items()),'Mapa de valores inválido.')
        if tk=='question':
            target=questions[ti]
            require(target['kind'] in VALUE_KINDS and target['storage_valid'],'Destino sem armazenamento suportado.')
            source=sources[origin].get(sid)
            if source and source['kind'] in ('oneof','checkbox'):
                require(target['kind'] in ('oneof','checkbox'),'Lista ligada a campo numérico.')
                require({o['value'] for o in source['options']}==set(vm)
                        and set(vm.values())<={o['value'] for o in target['options']},'Opções de origem/destino incompatíveis.')
            elif source:
                require(source['kind']=='numeric' and target['kind']=='numeric','Tipo de controle não pode ser ligado a um valor.')
                numeric_map,error=value_map(source,target)
                require(numeric_map is not None and not vm,error or 'Mapa numérico inválido.')
        control_ids.add(c['id'])
    overrides=project.get('asset_overrides')
    require(isinstance(overrides,dict) and len(overrides)<=242,'Imagens substitutas inválidas.')
    total=0
    for aid,encoded in overrides.items():
        require(aid in assets and isinstance(encoded,str) and len(encoded)<=4*1024*1024,'Imagem substituta desconhecida ou grande demais.')
        try:
            blob=base64.b64decode(encoded,validate=True)
        except Exception as exc:
            raise ValueError('Base64 de imagem inválido.') from exc
        total+=len(blob)
        require(image_size(blob)==(assets[aid]['width'],assets[aid]['height']),'Mantenha as dimensões originais da imagem.')
    require(total<=12*1024*1024,'Conjunto de imagens substitutas excede 12 MiB.')
    values=project.get('test_values')
    require(isinstance(values,dict) and len(values)<=10000,'Valores de teste inválidos.')
    targets={slot(q):q for q in stock['questions'] if q.get('storage_valid') and q['kind'] in VALUE_KINDS}
    for k,v in values.items():
        require(k in targets,'Valor de teste não pertence à BIOS.')
        check_value(targets[k],v)
    return project


def check_value(q,value):
    require(isinstance(value,str) and re.fullmatch(r'-?\d{1,24}',value),'Valor inválido.')
    n=int(value)
    if q['kind'] in ('oneof','checkbox'):
        require(value in {o['value'] for o in q['options']},'Opção não pertence ao campo da 002.')
    else:
        require(int(q['minimum'])<=n<=int(q['maximum']),'Valor fora do intervalo.')
        step=int(q.get('step','0'))
        require(not step or (n-int(q['minimum']))%step==0,'Valor fora do incremento permitido.')
    require(q.get('storage_valid'),'Campo fora da variável.')
    return value


def set_test_value(project,q,value):
    require(not q.get('read_only'),'Campo marcado somente para leitura.')
    project['test_values'][slot(q)]=check_value(q,str(value))


def summary(project):
    result={status:0 for status in STATUS}
    for c in project['controls']:
        result[c['status']]+=1
    return result


def write_project(path,project,stock,donor,catalog,donor_sha):
    require(str(Path(path).resolve())!=stock.get('_input_path'),'O projeto não pode sobrescrever a BIOS aberta.')
    require(Path(path).suffix.lower()=='.json','Salve o projeto com extensão .json.')
    validate_project(project,stock,donor,catalog,donor_sha)
    blob=(json.dumps(project,ensure_ascii=False,indent=2)+'\n').encode()
    require(len(blob)<=MAX_PROJECT,'Projeto excede 32 MiB.')
    Path(path).write_bytes(blob)


def read_project(path,stock,donor,catalog,donor_sha):
    with Path(path).open('rb') as f:
        blob=f.read(MAX_PROJECT+1)
    require(len(blob)<=MAX_PROJECT,'Projeto excede 32 MiB.')
    return validate_project(json.loads(blob),stock,donor,catalog,donor_sha)


def export_package(path,project,stock,donor,catalog,donor_sha):
    require(str(Path(path).resolve())!=stock.get('_input_path'),'O pacote não pode sobrescrever a BIOS aberta.')
    require(Path(path).suffix.lower()=='.zip','Exporte o pacote com extensão .zip.')
    validate_project(project,stock,donor,catalog,donor_sha)
    qmap={q['id']:q for q in stock['questions']}
    buffer=io.StringIO(newline='');writer=csv.writer(buffer,lineterminator='\n')
    writer.writerow(['controle','pagina','nome','estado','destino','variavel','offset','largura','motivo'])
    for c in project['controls']:
        q=qmap.get(c['target_id'],{})
        fields=[c['id'],c['page'],c['label'],STATUS[c['status']],c['target_id'] or '',
                (q.get('store') or {}).get('name',''),hex(q['offset']) if 'offset' in q else '',q.get('width',''),c['reason']]
        # Spreadsheet viewers must not execute formulas from user/firmware labels.
        writer.writerow([("'"+str(x)) if str(x).startswith(('=','+','-','@','\t','\r')) else x for x in fields])
    manifest={'app':'Covenant Graphics Studio','version':'0.1.0','stock_sha256':stock['sha256'],
              'bios_id':stock['bios_id'],'links':summary(project),'firmware_compiler_implemented':False,
              'runtime_adapter_implemented':False,'flashable_rom_included':False,'firmware_modified':False,
              'callbacks_executed':False,'hardware_tested':False}
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('projeto.json',json.dumps(project,indent=2,ensure_ascii=False)+'\n')
        z.writestr('manifesto.json',json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        z.writestr('vinculos.csv',buffer.getvalue())
        z.writestr('LEIA-ME.txt','Projeto gráfico e vínculos estruturais. Não é uma BIOS para gravar.\n'
                   'Valores de teste não foram aplicados à ROM ou à placa.\n'
                   'O compilador AMI/adaptador de runtime ainda não está implementado.\n')
        for aid,blob in project['asset_overrides'].items():
            z.writestr('imagens-editadas/'+aid,base64.b64decode(blob))
    return manifest
