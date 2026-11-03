"""Read bounded PE resources and a subset of IFR for the mapping workbench.

Visibility expressions and callbacks are described, never executed.
"""
import struct
import uuid


def need(condition, message):
    if not condition:
        raise ValueError(message)


def resources(pe):
    need(len(pe) >= 64 and pe[:2] == b'MZ', 'PE sem cabeçalho DOS.')
    start = struct.unpack_from('<I', pe, 60)[0]
    need(start + 24 <= len(pe) and pe[start:start + 4] == b'PE\0\0', 'Cabeçalho PE inválido.')
    count, optsize = struct.unpack_from('<H', pe, start + 6)[0], struct.unpack_from('<H', pe, start + 20)[0]
    opt = start + 24
    need(count <= 96 and opt + optsize + count * 40 <= len(pe) and optsize >= 96, 'Seções PE fora dos limites.')
    magic = struct.unpack_from('<H', pe, opt)[0]
    need(magic in (0x10B, 0x20B), 'Tipo PE não suportado.')
    directory = opt + (112 if magic == 0x20B else 96)
    if directory + 24 > opt + optsize:
        return []
    if struct.unpack_from('<I', pe, directory - 4)[0] < 3:
        return []
    rva, size = struct.unpack_from('<II', pe, directory + 16)
    if not rva or not size:
        return []
    sections = [struct.unpack_from('<4I', pe, opt + optsize + i * 40 + 8) for i in range(count)]

    def offset(address, length):
        for _, va, rawsize, raw in sections:
            if va <= address and address + length <= va + rawsize:
                pos = raw + address - va
                need(pos + length <= len(pe), 'Recurso PE truncado.')
                return pos
        raise ValueError('RVA de recurso PE fora das seções.')

    base = offset(rva, size)
    result, seen = [], set()

    def walk(relative, depth=0):
        need(depth <= 4 and relative not in seen and relative + 16 <= size, 'Árvore de recursos PE inválida.')
        seen.add(relative)
        named, ids = struct.unpack_from('<HH', pe, base + relative + 12)
        need(named + ids <= 256 and relative + 16 + (named + ids) * 8 <= size, 'Diretório de recursos PE excedido.')
        for index in range(named + ids):
            _, pointer = struct.unpack_from('<II', pe, base + relative + 16 + index * 8)
            if pointer & 0x80000000:
                walk(pointer & 0x7FFFFFFF, depth + 1)
            else:
                need(pointer + 16 <= size, 'Entrada de recurso PE truncada.')
                address, length = struct.unpack_from('<II', pe, base + pointer)
                need(length <= 4 * 1024 * 1024 and len(result) < 128, 'Recurso PE excede o limite.')
                pos = offset(address, length)
                result.append(pe[pos:pos + length])
    walk(0)
    return result


def string_package(data):
    need(len(data) >= 47, 'Pacote de strings truncado.')
    header, start = struct.unpack_from('<II', data, 4)
    need(47 <= header <= start <= len(data), 'Cabeçalho de strings inválido.')
    language = data[46:header].split(b'\0', 1)[0].decode('ascii')
    if language not in ('en-US', 'en'):
        return {}
    pos, token, values = start, 1, {}

    def read_string():
        nonlocal pos
        begin = pos
        while pos + 2 <= len(data):
            if data[pos:pos + 2] == b'\0\0':
                value = data[begin:pos].decode('utf-16le')
                pos += 2
                return value
            pos += 2
        raise ValueError('String HII sem terminador.')

    while pos < len(data):
        op, pos = data[pos], pos + 1
        if op == 0:
            return values
        if op in (0x14, 0x15, 0x16, 0x17):
            if op in (0x15, 0x17):
                pos += 1
            count = 1
            if op in (0x16, 0x17):
                need(pos + 2 <= len(data), 'Contagem de strings truncada.')
                count = struct.unpack_from('<H', data, pos)[0]
                pos += 2
            need(token + count <= 65536, 'Tabela de strings excedida.')
            for _ in range(count):
                values[token] = read_string()
                token += 1
        elif op in (0x20, 0x21, 0x22):
            width = 1 if op == 0x22 else 2
            need(pos + width <= len(data), 'Operando de strings truncado.')
            number = int.from_bytes(data[pos:pos + width], 'little')
            pos += width
            if op == 0x20:
                need(number in values, 'Referência de string ausente.')
                values[token], token = values[number], token + 1
            else:
                token += number
        else:
            raise ValueError(f'Opcode de string inglesa não suportado: 0x{op:X}.')
        need(token <= 65536, 'Tabela de strings excedida.')
    raise ValueError('Pacote de strings sem terminador.')


def parse(blob, module_guid, *, max_questions=5000):
    need(type(max_questions) is int and 1 <= max_questions <= 16384, 'Limite de questões HII inválido.')
    need(len(blob) >= 24, 'Lista HII truncada.')
    total = struct.unpack_from('<I', blob, 16)[0]
    need(24 <= total <= min(len(blob), 4 * 1024 * 1024), 'Tamanho HII inválido.')
    package_guid = str(uuid.UUID(bytes_le=blob[:16])).upper()
    packages, strings, pos, ended = [], {}, 20, False
    while pos + 4 <= total:
        word = struct.unpack_from('<I', blob, pos)[0]
        size, kind = word & 0xFFFFFF, word >> 24
        need(size >= 4 and pos + size <= total and len(packages) < 4096, 'Pacote HII fora dos limites.')
        payload = blob[pos:pos + size]
        packages.append((kind, payload))
        if kind == 4:
            strings.update(string_package(payload))
        if kind == 0xDF:
            need(size == 4 and pos + size == total, 'Fim de lista HII inválido.')
            ended = True
        pos += size
    need(pos == total and ended and any(k == 2 for k, _ in packages), 'Recurso sem lista HII de formulários completa.')
    forms, questions, stores = [], [], {}
    source = module_guid + '/' + package_guid
    for kind, data in packages:
        if kind != 2:
            continue
        stack, pos = [], 4
        while pos < len(data):
            need(pos + 2 <= len(data), 'Opcode IFR truncado.')
            op, flags = data[pos], data[pos + 1]
            length = flags & 0x7F
            need(length >= 2 and pos + length <= len(data), 'Opcode IFR fora dos limites.')
            item, node = data[pos:pos + length], {'op': op}
            formset = next((s['formset'] for s in reversed(stack) if 'formset' in s), None)
            form = next((s['form'] for s in reversed(stack) if 'form' in s), None)
            if op == 0x0E:
                need(length >= 23, 'Formset IFR truncado.')
                node['formset'] = str(uuid.UUID(bytes_le=item[2:18])).upper()
            elif op == 1:
                need(formset and length >= 6, 'Form IFR inválido.')
                number, title = struct.unpack_from('<HH', item, 2)
                node['form'] = f'{source}/{formset}/f{number:04X}'
                forms.append({'id': node['form'], 'form_id': number, 'formset': formset,
                              'title': strings.get(title, f'Form 0x{number:X}'), 'module': module_guid})
                need(len(forms) <= 512, 'Quantidade de formulários HII excedida.')
            elif op == 0x24:
                need(formset and length >= 23, 'Varstore IFR truncado.')
                sid, size = struct.unpack_from('<HH', item, 18)
                name = item[22:].split(b'\0', 1)[0].decode('ascii')
                stores[(formset, sid)] = {'guid': str(uuid.UUID(bytes_le=item[2:18])).upper(), 'name': name, 'size': size}
            elif op in (5, 6, 7, 0x0F, 0x0C):
                need(formset and form and length >= 13, 'Questão IFR truncada ou fora de formulário.')
                prompt, help_id, qid, sid, offset = struct.unpack_from('<5H', item, 2)
                q = {'id': f'{source}/{formset}/q{qid:04X}@{pos:X}', 'question_id': qid, 'form': form,
                     'formset': formset, 'module': module_guid, 'opcode': op,
                     'kind': {5:'oneof', 6:'checkbox', 7:'numeric', 15:'ref', 12:'action'}[op],
                     'prompt': strings.get(prompt, f'Question 0x{qid:X}'), 'help': strings.get(help_id, ''),
                     'store_id': sid, 'offset': offset, 'flags': item[12], 'width': 0, 'options': [],
                     'callback': bool(item[12] & 4), 'read_only': bool(item[12] & 1),
                     'conditional': any(s['op'] in (0x0A, 0x19, 0x1E) for s in stack)}
                if op in (5, 7):
                    need(length >= 14, 'Flags numéricas truncadas.')
                    width = 1 << (item[13] & 3)
                    need(length >= 14 + 3 * width, 'Limites numéricos truncados.')
                    q['width'] = width
                    q['signed'] = op == 7 and (item[13] & 0x30) == 0
                    for index, key in enumerate(('minimum', 'maximum', 'step')):
                        q[key] = str(int.from_bytes(item[14 + index * width:14 + (index + 1) * width], 'little', signed=q['signed'] and index < 2))
                elif op == 6:
                    need(length >= 14, 'Checkbox IFR truncado.')
                    q['width'], q['options'] = 1, [{'label':'Disabled', 'value':'0'}, {'label':'Enabled', 'value':'1'}]
                elif op == 15:
                    need(length >= 15, 'Referência IFR truncada.')
                    q['target_form_id'] = struct.unpack_from('<H', item, 13)[0]
                    q['target_formset'] = str(uuid.UUID(bytes_le=item[17:33])).upper() if length >= 33 else formset
                questions.append(q)
                need(len(questions) <= max_questions, 'Quantidade de questões HII excedida.')
                node['question'] = q
            elif op == 9:
                question = next((s['question'] for s in reversed(stack) if 'question' in s), None)
                need(length >= 6, 'Opção IFR truncada.')
                width = {0:1, 1:2, 2:4, 3:8, 4:1}.get(item[5])
                if question and width:
                    need(length >= 6 + width, 'Valor de opção IFR truncado.')
                    token = struct.unpack_from('<H', item, 2)[0]
                    question['options'].append({'label': strings.get(token, f'Option {token}'),
                                                'value': str(int.from_bytes(item[6:6 + width], 'little'))})
                    need(len(question['options']) <= 512, 'Quantidade de opções HII excedida.')
            if op == 0x29:
                need(bool(stack), 'Escopo IFR negativo.')
                stack.pop()
            elif flags & 0x80:
                stack.append(node)
            pos += length
        need(not stack, 'Escopos IFR incompletos.')
    lookup = {f['id']: f for f in forms}
    for q in questions:
        q['store'] = stores.get((q['formset'], q['store_id']))
        q['form_title'] = lookup[q['form']]['title']
        q['storage_valid'] = bool(q['store'] and q['width'] and q['offset'] + q['width'] <= q['store']['size'])
        q['simulation_supported'] = (q['storage_valid'] and q['kind'] in ('oneof', 'checkbox', 'numeric')
                                     and (q['kind'] != 'oneof' or bool(q['options']))) or q['kind'] in ('ref', 'action')
    return {'forms': forms, 'questions': questions, 'english_strings': len(strings), 'package_guid': package_guid}
