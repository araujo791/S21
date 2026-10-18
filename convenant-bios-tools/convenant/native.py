"""Native Qt Widgets application. No HTTP server or browser is started."""
import json
import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPainter, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QScrollArea, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__
from .core import build_candidate, compare_blobs, deep_check, descriptor, inspect_blob
from .hardware import inventory
from .workspace import Workspace, app_root

STYLE = '''
QWidget { background: #12171b; color: #e8eeee; font-size: 13px; }
QMainWindow, QScrollArea, QStackedWidget { background: #12171b; }
QListWidget { background: #181f24; border: 0; padding: 12px; outline: none; }
QListWidget::item { padding: 14px 10px; margin: 3px 0; border-radius: 5px; }
QListWidget::item:selected { background: #294637; color: #a4efc5; }
QFrame#card { background: #1b2329; border: 1px solid #34414a; border-radius: 8px; }
QFrame#card QLabel { background: transparent; }
QLabel#title { font-size: 27px; font-weight: 600; }
QLabel#eyebrow { color: #a4efc5; font-size: 11px; }
QLabel#muted { color: #a7b4bd; }
QPushButton { background: #2c3941; border: 1px solid #4a5b65; border-radius: 5px; padding: 10px 15px; }
QPushButton:hover { background: #3c4d57; }
QPushButton:disabled { color: #75828a; background: #232b30; border-color: #303a40; }
QPushButton[primary="true"] { background: #a4efc5; color: #12291c; border-color: #a4efc5; font-weight: 600; }
QPushButton[danger="true"] { background: #fba39c; color: #301614; border-color: #fba39c; font-weight: 600; }
QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QTreeWidget { background: #10161a; border: 1px solid #3d4c55; border-radius: 4px; padding: 7px; selection-background-color: #355f49; }
QComboBox { min-height: 22px; }
QComboBox QAbstractItemView { background: #1b2329; selection-background-color: #355f49; }
QHeaderView::section { background: #29353e; padding: 8px; border: 0; }
QTabWidget::pane { border: 1px solid #34414a; }
QTabBar::tab { background: #202b32; padding: 8px 15px; }
QTabBar::tab:selected { background: #355343; color: #b9f3d1; }
QProgressBar { border: 0; background: #263139; max-height: 5px; }
QProgressBar::chunk { background: #a4efc5; }
QSplitter::handle { background: #34414a; height: 4px; }
QMessageBox, QDialog { background: #1b2329; }
'''


class Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


class Task(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation, self.signals = operation, Signals()

    def run(self):
        try:
            self.signals.done.emit(self.operation())
        except Exception as exc:
            self.signals.failed.emit(str(exc))


def label(text, kind=None):
    result = QLabel(text)
    result.setTextFormat(Qt.PlainText)
    result.setWordWrap(True)
    if kind:
        result.setObjectName(kind)
    return result


def icon():
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setBrush(Qt.GlobalColor.darkGreen)
    painter.setPen(Qt.GlobalColor.transparent)
    painter.drawRoundedRect(0, 0, 64, 64, 12, 12)
    painter.setPen(Qt.GlobalColor.white)
    painter.setFont(QFont('Segoe UI', 33, QFont.Bold))
    painter.drawText(pix.rect(), Qt.AlignCenter, 'C')
    painter.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self, data=None, root=None, identify=True):
        super().__init__()
        self.workspace = Workspace(data or app_root() / 'dados-convenant', root=root, initialize_inventory=False)
        self.setWindowTitle('Convenant BIOS Tools ' + __version__)
        self.setWindowIcon(icon())
        self.resize(1180, 840)
        self.setMinimumSize(860, 620)
        self.selectors, self.actions, self.tasks = [], [], []
        self.busy, self.preparation, self.prepared_file = False, None, None
        self.last_report = None
        self.pool = QThreadPool(self)
        central = QWidget(); self.setCentralWidget(central)
        row = QHBoxLayout(central); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(0)
        sidebar = QWidget(); sidebar.setFixedWidth(220)
        left = QVBoxLayout(sidebar); left.setContentsMargins(16, 25, 16, 18)
        brand = label('CONVENANT\nBIOS TOOLS', 'eyebrow'); brand.setFont(QFont('Segoe UI', 16, QFont.Bold)); left.addWidget(brand)
        self.navigation = QListWidget(); self.navigation.setObjectName('navigation')
        self.navigation.addItems(['Visão geral', 'Backups', 'Analisar e comparar', 'Microcódigos', 'Gravar BIOS', 'Ferramentas e arquivos'])
        left.addWidget(self.navigation)
        left.addWidget(label('v' + __version__ + '\nAplicativo nativo · dados locais', 'muted'))
        row.addWidget(sidebar)
        main = QWidget(); layout = QVBoxLayout(main); layout.setContentsMargins(25, 20, 25, 18)
        self.progress = QProgressBar(); self.progress.setRange(0, 0); self.progress.hide(); layout.addWidget(self.progress)
        self.status = label('Nenhum acesso ao chip é feito ao abrir o aplicativo.', 'muted'); layout.addWidget(self.status)
        splitter = QSplitter(Qt.Vertical)
        self.pages = QStackedWidget(); splitter.addWidget(self.pages)
        self._overview(); self._backups(); self._analysis(); self._microcodes(); self._write(); self._settings()
        self.results = QTabWidget(); self.results.setMinimumHeight(155)
        self.summary = QTextEdit(); self.summary.setReadOnly(True)
        self.details = QPlainTextEdit(); self.details.setReadOnly(True); self.details.setFont(QFont('Consolas', 10))
        self.results.addTab(self.summary, 'Resultado'); self.results.addTab(self.details, 'Relatório e log')
        splitter.addWidget(self.results); splitter.setSizes([540, 180]); layout.addWidget(splitter)
        bottom = QHBoxLayout()
        self.export_button = self.button('Salvar relatório JSON', self.export_report)
        bottom.addWidget(self.export_button); bottom.addStretch(); bottom.addWidget(label('Convenant BIOS Tools · janela nativa', 'muted'))
        layout.addLayout(bottom); row.addWidget(main, 1)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.refresh_files()
        self.poll_timer = QTimer(self); self.poll_timer.setInterval(350); self.poll_timer.timeout.connect(self.poll_hardware)
        self.active_job = None
        if identify:
            QTimer.singleShot(0, lambda: self.run_task('Identificando a plataforma…', inventory, self.show_inventory))
        else:
            self.show_inventory({})

    def button(self, text, operation, primary=False, danger=False, name=None):
        b = QPushButton(text); b.setProperty('primary', primary); b.setProperty('danger', danger)
        if name: b.setObjectName(name)
        b.clicked.connect(lambda _checked=False: operation())
        self.actions.append(b)
        return b

    def page(self, eyebrow, title, description):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget(); layout = QVBoxLayout(body); layout.setContentsMargins(5, 10, 12, 15); layout.setSpacing(18)
        layout.addWidget(label(eyebrow, 'eyebrow')); layout.addWidget(label(title, 'title')); layout.addWidget(label(description, 'muted'))
        scroll.setWidget(body); self.pages.addWidget(scroll)
        return layout

    def card(self, parent, title):
        frame = QFrame(); frame.setObjectName('card'); box = QVBoxLayout(frame); box.setContentsMargins(20, 18, 20, 18); box.setSpacing(14)
        heading = label(title); heading.setFont(QFont('Segoe UI', 14, QFont.Bold)); box.addWidget(heading); parent.addWidget(frame)
        return box

    def selector(self, parent, title, name):
        parent.addWidget(label(title, 'muted'))
        combo = QComboBox(); combo.setObjectName(name); combo.setMinimumWidth(180); parent.addWidget(combo)
        self.selectors.append(combo)
        return combo

    def _overview(self):
        page = self.page('SEU FIRMWARE, SOB CONTROLE', 'Uma bancada para a sua BIOS.',
                         'Aplicativo desktop. Escolha os arquivos nas janelas do sistema e preserve o original antes de alterar.')
        box = self.card(page, 'Plataforma identificada')
        self.inventory_label = label('Identificando…'); box.addWidget(self.inventory_label)
        box = self.card(page, 'Comece com uma cópia confiável')
        box.addWidget(label('Faça duas leituras, compare os arquivos e confira a estrutura. Um arquivo com menos mensagens pode conter mais dados corrompidos.'))
        box.addWidget(self.button('Abrir backups', lambda: self.navigation.setCurrentRow(1), primary=True))
        box = self.card(page, 'Regiões diferentes, permissões diferentes')
        box.addWidget(label('Na E5-D8 Max, o chip tem 16 MiB. A BIOS ocupa 8 MiB. Descriptor e SPS ficam na outra metade. O aplicativo informa áreas bloqueadas; não simula um backup completo preenchendo bytes.'))
        page.addStretch()

    def _backups(self):
        page = self.page('LEITURA DO CHIP', 'Preserve antes de alterar.', 'Operações de leitura. O sistema solicita autorização de administrador ao acessar o controlador.')
        box = self.card(page, 'Chip e permissões')
        box.addWidget(self.button('Consultar chip e acesso', lambda: self.hardware_job({'action': 'probe'})))
        box = self.card(page, 'Criar backup')
        self.region = QComboBox()
        for title, value in [('BIOS / UEFI — 8 MiB', 'bios'), ('SPI completa — 16 MiB', 'full'), ('Descriptor Intel — 4 KiB', 'descriptor'), ('ME / SPS isolado', 'sps')]:
            self.region.addItem(title, value)
        box.addWidget(self.region)
        box.addWidget(self.button('Fazer e comparar duas leituras', lambda: self.hardware_job({'action': 'backup', 'region': self.region.currentData()}), primary=True))
        box.addWidget(label('Error 26 significa acesso negado pelo descriptor. As leituras do CH341 podem ser abertas na aba Analisar; esta versão usa o controlador interno via FPT ou flashrom.', 'muted'))
        page.addStretch()

    def _analysis(self):
        page = self.page('VERIFICAÇÃO DOS ARQUIVOS', 'Analisar e comparar.', 'Descriptors de 4 KiB, BIOS de 8 MiB ou SPI de 16 MiB. Os arquivos ficam na pasta portátil.')
        page.addWidget(self.button('Adicionar arquivos…', self.choose_files, primary=True, name='import_button'))
        box = self.card(page, 'Análise do firmware')
        self.analysis_file = self.selector(box, 'Arquivo', 'analysis_file')
        row = QHBoxLayout()
        self.analyze_button = self.button('Verificar integridade', self.analyze_selected, primary=True, name='analyze_button')
        row.addWidget(self.analyze_button); row.addWidget(self.button('Extrair região BIOS', self.extract_selected)); box.addLayout(row)
        box = self.card(page, 'Comparação de capturas')
        self.compare_first = self.selector(box, 'Referência', 'compare_first')
        self.compare_second = self.selector(box, 'Segunda captura', 'compare_second')
        self.compare_button = self.button('Comparar bytes e hashes', self.compare_selected, name='compare_button'); box.addWidget(self.compare_button)
        page.addStretch()

    def _microcodes(self):
        page = self.page('ATUALIZAÇÃO OFFLINE', 'Microcódigos com base conhecida.', 'Candidata experimental da base 002. Não altera memória, potência, turbo ou SPS.')
        box = self.card(page, 'Entradas verificadas')
        self.build_base = self.selector(box, 'Primeira leitura BIOS de 8 MiB', 'build_base')
        self.build_second = self.selector(box, 'Segunda leitura idêntica', 'build_second')
        self.build_v3 = self.selector(box, 'Intel 06-3f-02 — v3 / revisão 49', 'build_v3')
        self.build_v4 = self.selector(box, 'Intel 06-4f-01 — v4 / revisão 040', 'build_v4')
        self.build_button = self.button('Gerar candidata e manifesto', self.build_selected, primary=True, name='build_button'); box.addWidget(self.build_button)
        box.addWidget(label('Adicione os arquivos na aba Analisar. Somente o perfil 002 revisado e as referências Intel com hash fixado são aceitos. A candidata não tem validação física de boot ou desempenho.', 'muted'))
        page.addStretch()

    def _write(self):
        page = self.page('OPERAÇÃO DE GRAVAÇÃO', 'Grave depois de conferir.', 'Somente a região BIOS de 8 MiB e a família de código 002 revisada. Descriptor e SPS não são gravados.')
        box = self.card(page, '1. Preparar e preservar o estado atual')
        self.write_file = self.selector(box, 'Imagem candidata', 'write_file')
        self.write_file.currentIndexChanged.connect(self.invalidate_preparation)
        box.addWidget(self.button('Preparar gravação', self.prepare_selected, primary=True))
        box.addWidget(label('Faz dois backups atuais, exige igualdade e análise UEFI detalhada. A 006 e bases desconhecidas são bloqueadas por compatibilidade não demonstrada.', 'muted'))
        box = self.card(page, '2. Revisar e confirmar')
        self.write_summary = label('Prepare uma imagem para conferir os dados e os backups.'); box.addWidget(self.write_summary)
        self.write_confirm = self.button('Revisar gravação…', self.confirm_write, danger=True, name='write_confirm'); self.write_confirm.setEnabled(False); box.addWidget(self.write_confirm)
        box.addWidget(label('A análise estática não garante compatibilidade física ou boot. Tenha recuperação confiável. Uma leitura posterior precisa coincidir byte a byte com a candidata.', 'muted'))
        page.addStretch()

    def _settings(self):
        page = self.page('PASTA PORTÁTIL', 'Ferramentas e arquivos.', 'FPT e flashrom são motores externos. O executável não desativa proteções do sistema.')
        box = self.card(page, 'Motor de acesso')
        self.tools_label = label(''); box.addWidget(self.tools_label)
        box.addWidget(self.button('Selecionar fptw64.exe…', self.choose_fpt))
        box.addWidget(label('Windows: copie sua pasta completa do FPT para tools/FPT. CachyOS: instale flashrom e polkit. O Python e a interface acompanham os pacotes executáveis.', 'muted'))
        box = self.card(page, 'Arquivos desta bancada')
        self.files_tree = QTreeWidget(); self.files_tree.setHeaderLabels(['Arquivo', 'Tamanho', 'SHA-256']); self.files_tree.setMinimumHeight(160)
        self.files_tree.setColumnWidth(0, 270); self.files_tree.setColumnWidth(1, 100); box.addWidget(self.files_tree)
        row = QHBoxLayout(); row.addWidget(self.button('Salvar BIN selecionado…', self.save_selected_file)); row.addWidget(self.button('Abrir pasta de dados', lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.workspace.data)))))
        box.addLayout(row); box.addWidget(label(str(self.workspace.data), 'muted')); page.addStretch()

    def set_busy(self, value, message=''):
        self.busy = value
        self.progress.setVisible(value)
        for b in self.actions:
            b.setEnabled(not value)
        self.write_confirm.setEnabled(not value and bool(self.preparation))
        if message:
            self.status.setText(message)

    def show_inventory(self, result):
        self.workspace.hardware = result
        cpus = result.get('cpus', [])
        if isinstance(cpus, str): cpus = [cpus]
        text = 'Placa: ' + (result.get('board') or 'não identificada') + '\nBIOS: ' + (result.get('bios') or 'não identificada')
        text += '\nCPU(s): ' + (' / '.join(cpus) or 'não identificado')
        if result.get('memory_bytes'): text += '\nMemória: %.1f GiB' % (result['memory_bytes'] / 1024 ** 3)
        self.inventory_label.setText(text)
        tools = self.workspace.tools()
        self.tools_label.setText('Motor: %s\nExecutável: %s\nUEFIExtract: %s' % (tools['backend'], tools.get(tools['backend']) or 'não encontrado', tools['uefiextract'] or 'não encontrado'))

    def run_task(self, message, operation, after=None):
        if self.busy:
            return
        self.set_busy(True, message)
        task = Task(operation); self.tasks.append(task)
        def done(value):
            self.tasks.remove(task)
            self.set_busy(False, 'Operação concluída.')
            try:
                if after: after(value)
            except Exception as exc:
                self.failure(str(exc))
        def failed(message):
            self.tasks.remove(task); self.set_busy(False); self.failure(message)
        task.signals.done.connect(done); task.signals.failed.connect(failed); self.pool.start(task)

    def failure(self, message):
        self.status.setText('Operação interrompida: ' + message)
        self.show_result({'error': message}, message)

    def refresh_files(self):
        self.files = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((self.workspace.data / 'files').glob('*.meta.json'))]
        for combo in self.selectors:
            old = combo.currentData(); combo.blockSignals(True); combo.clear(); combo.addItem('Selecione um arquivo…', None)
            for item in self.files:
                combo.addItem('%s · %.2f MiB · %s' % (item['name'], item['size'] / 1024 ** 2, item['sha256'][:8]), item['id'])
            index = combo.findData(old)
            combo.setCurrentIndex(max(index, 0)); combo.blockSignals(False)
        self.files_tree.clear()
        for item in self.files:
            row = QTreeWidgetItem([item['name'], '%s bytes' % item['size'], item['sha256']]); row.setData(0, Qt.UserRole, item['id']); self.files_tree.addTopLevelItem(row)

    def require(self, combo):
        if not combo.currentData():
            raise ValueError('Selecione um arquivo para esta operação.')
        return combo.currentData()

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Adicionar firmware ou referência Intel', '', 'Firmware (*.bin *.rom *.fd *.cap);;Todos os arquivos (*)')
        if paths: self.import_paths(paths)

    def import_paths(self, paths):
        def load():
            items = []
            for name in paths:
                path = Path(name)
                if not 0 < path.stat().st_size <= 16 * 1024 ** 2:
                    raise ValueError('Use arquivos não vazios de até 16 MiB.')
                items.append(self.workspace.save_blob(path.read_bytes(), path.name))
            return items
        def done(items):
            self.refresh_files(); self.show_result({'files':items}, '%d arquivo(s) adicionado(s). Selecione para analisar.' % len(items))
        self.run_task('Adicionando arquivos…', load, done)

    def analyze_file(self, ident):
        path = self.workspace.file(ident); report = inspect_blob(path.read_bytes()); tool = self.workspace.tools()['uefiextract']
        report['deep'] = deep_check(path, tool) if tool and path.stat().st_size != 4096 else {'available':False,'passed':False}
        if report['deep']['available'] and not report['deep']['passed']: report['status'] = 'deep_analysis_errors'
        path.with_suffix('.analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        return report

    def analyze_selected(self):
        try: ident = self.require(self.analysis_file)
        except ValueError as exc: return self.failure(str(exc))
        def show(report):
            bad = bool(report['issues'] or (report['deep']['available'] and not report['deep']['passed']))
            text = ('Foram encontrados erros; não use para gravação.' if bad else 'As verificações executadas não encontraram erros estruturais.')
            text += '\nSHA-256: ' + report['sha256']
            if report.get('bios_id'): text += '\nBIOS: ' + report['bios_id'] + '\nPerfil: ' + report['profile']
            for code in report.get('microcodes',[]):
                text += '\nCPUID %s — revisão %s — %s' % (code['cpuid'],code['revision'],'checksum válido' if code['checksum_valid'] else 'CHECKSUM INVÁLIDO')
            if report.get('sps_bup'): text += '\nBUP SPS: ' + report['sps_bup']['status'] + '. Demais módulos não verificados.'
            text += '\nAnálise estática: não garante boot, estabilidade ou recuperação integral.'
            self.show_result(report, text)
        self.run_task('Verificando estrutura e descompressão…', lambda: self.analyze_file(ident), show)

    def compare_selected(self):
        try: first, second = self.require(self.compare_first), self.require(self.compare_second)
        except ValueError as exc: return self.failure(str(exc))
        def compare(): return compare_blobs(self.workspace.file(first).read_bytes(), self.workspace.file(second).read_bytes())
        def show(report):
            text = 'Arquivos idênticos byte a byte.' if report['identical'] else 'Os arquivos são diferentes.'
            if report.get('code_excluding_first_512KiB_nvram'):
                text += '\nCódigo fora da NVRAM: %s bytes diferentes.' % report['code_excluding_first_512KiB_nvram']['different_bytes']
            text += '\nDiferenças entre versões distintas não provam corrupção.'
            self.show_result(report,text)
        self.run_task('Comparando arquivos…', compare, show)

    def extract_selected(self):
        try: ident = self.require(self.analysis_file)
        except ValueError as exc: return self.failure(str(exc))
        def extract():
            data = self.workspace.file(ident).read_bytes()
            if len(data) != 16 * 1024 ** 2: raise ValueError('Selecione uma SPI de 16 MiB.')
            region = next(r for r in descriptor(data)['regions'] if r['name']=='bios')
            if not region['present'] or region['end'] > len(data) or region['end']-region['start'] != 8*1024**2:
                raise ValueError('Região BIOS de 8 MiB não encontrada.')
            return self.workspace.save_blob(data[region['start']:region['end']], 'BIOS-extraida-8MiB.bin')
        self.run_task('Extraindo região…', extract, lambda r: (self.refresh_files(), self.show_result(r,'Região copiada sem reparos; analise antes de usar.')))

    def build_selected(self):
        try: ids = [self.require(c) for c in (self.build_base,self.build_second,self.build_v3,self.build_v4)]
        except ValueError as exc: return self.failure(str(exc))
        def build():
            image, manifest = build_candidate(*(self.workspace.file(i).read_bytes() for i in ids))
            item = self.workspace.save_blob(image,'E5-D8-MAX-002-V3-V4-EXPERIMENTAL-8MiB.bin')
            self.workspace.file(item['id']).with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
            return {'file':item,'manifest':manifest}
        self.run_task('Gerando candidata experimental…', build,
                      lambda r: (self.refresh_files(), self.show_result(r,'Candidata gerada, com NVRAM preservada. Nenhuma gravação ou teste físico foi realizado.')))

    def hardware_job(self, payload):
        if self.busy: return
        try:
            self.active_job = self.workspace.start_job(payload)['id']
            self.set_busy(True,'Autorize a operação no sistema. Não feche durante gravação.'); self.poll_timer.start()
        except Exception as exc: self.failure(str(exc))

    def poll_hardware(self):
        state = self.workspace.jobs[self.active_job]
        if state['status'] == 'running': return
        self.poll_timer.stop(); self.refresh_files()
        if state.get('ok') and state['action']=='prepare':
            self.preparation = state['preparation']; self.prepared_file = self.write_file.currentData()
            r=state['result']; self.write_summary.setText('Perfil: %s\nSHA-256: %s\nNVRAM será alterada: %s\nDois backups prévios preservados; validade de 10 minutos.' % (r['profile'],r['candidate_sha256'],'sim' if r['nvram_will_change'] else 'não'))
        self.set_busy(False,'Operação concluída.' if state.get('ok') else 'Operação interrompida.')
        text = state.get('error') or 'Confira os resultados e preserve os arquivos.'
        if state.get('ok'):
            result=state['result']
            if state['action']=='probe':
                for name,access in result.get('permissions',{}).items():
                    text+='\n%s — leitura: %s; gravação: %s' % (name,'sim' if access['read'] else 'não','sim' if access['write'] else 'não')
            elif state['action']=='backup':
                text+='\nDuas leituras: '+('idênticas.' if result['identical'] else 'DIFERENTES — não usar para gravação.')
                if any(r.get('analysis',{}).get('issues') or (r.get('analysis',{}).get('deep',{}).get('available') and not r['analysis']['deep']['passed']) for r in result['reports']):
                    text+='\nForam encontrados erros de integridade no conteúdo.'
                text+='\nIgualdade não comprova integridade completa ou boot.'
            elif state['action']=='write':text=result['message']
        self.show_result(state,text)

    def invalidate_preparation(self):
        self.preparation = None
        self.write_confirm.setEnabled(False)

    def prepare_selected(self):
        try: ident = self.require(self.write_file)
        except ValueError as exc: return self.failure(str(exc))
        self.invalidate_preparation(); self.hardware_job({'action':'prepare','file':ident})

    def confirm_write(self):
        if not self.preparation: return
        dialog = QDialog(self); dialog.setWindowTitle('Confirmar gravação da BIOS'); dialog.resize(570,330)
        box=QVBoxLayout(dialog); box.addWidget(label(self.write_summary.text()))
        ack=QCheckBox('Conferi a imagem e os backups e disponho de recuperação confiável.'); box.addWidget(ack)
        box.addWidget(label('Digite GRAVAR BIOS para alterar o chip:'))
        phrase=QLineEdit(); box.addWidget(phrase)
        buttons=QDialogButtonBox(QDialogButtonBox.Cancel|QDialogButtonBox.Ok); buttons.button(QDialogButtonBox.Ok).setText('Gravar região BIOS'); box.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)
        def accept():
            if ack.isChecked() and phrase.text()=='GRAVAR BIOS': dialog.accept()
        buttons.accepted.connect(accept)
        if dialog.exec()!=QDialog.Accepted: return
        key=self.preparation;ident=self.prepared_file;self.invalidate_preparation()
        self.hardware_job({'action':'write','file':ident,'preparation':key,'confirmation':'GRAVAR BIOS','acknowledged':True})

    def choose_fpt(self):
        path,_=QFileDialog.getOpenFileName(self,'Selecionar Intel FPT','','Intel FPT (fptw64.exe)')
        if path:
            if Path(path).name.lower()!='fptw64.exe': return self.failure('Selecione fptw64.exe.')
            self.workspace.fpt=path;self.show_inventory(self.workspace.hardware)

    def show_result(self, report, text):
        self.last_report=report;self.summary.setPlainText(text);self.details.setPlainText(json.dumps(report,indent=2,ensure_ascii=False));self.results.setCurrentIndex(0)

    def export_report(self):
        if self.last_report is None: return
        path,_=QFileDialog.getSaveFileName(self,'Salvar relatório','convenant-relatorio.json','JSON (*.json)')
        if path:
            try: Path(path).write_text(json.dumps(self.last_report,indent=2,ensure_ascii=False),encoding='utf-8')
            except OSError as exc: self.failure(str(exc))

    def save_selected_file(self):
        row=self.files_tree.currentItem()
        if not row: return self.failure('Selecione um arquivo na lista.')
        path,_=QFileDialog.getSaveFileName(self,'Salvar BIN',row.text(0),'BIN (*.bin)')
        if path:
            try:
                source=self.workspace.file(row.data(0,Qt.UserRole))
                if Path(path).resolve()!=source.resolve(): shutil.copyfile(source,path)
            except OSError as exc: self.failure(str(exc))

    def closeEvent(self,event):
        if self.busy or self.workspace.lock.locked():
            QMessageBox.information(self,'Operação em andamento','Aguarde a operação terminar. Não interrompa uma gravação.');event.ignore()
        else: event.accept()


def start(args):
    application=QApplication.instance() or QApplication(sys.argv[:1])
    application.setApplicationName('Convenant BIOS Tools');application.setStyle('Fusion');application.setStyleSheet(STYLE)
    window=MainWindow(args.data);window.show()
    if getattr(args,'smoke_output',None):
        def save_result(analysis=None):
            data={'native_window':True,'version':__version__,'pages':window.pages.count(),'network_server_started':False,'hardware_accessed':False}
            if analysis is not None:data['analysis']=analysis
            Path(args.smoke_output).write_text(json.dumps(data),encoding='utf-8');window.close()
        def finish():
            if window.busy: return QTimer.singleShot(100,finish)
            if getattr(args,'smoke_input',None):
                source=Path(args.smoke_input)
                if source.stat().st_size>16*1024**2:raise ValueError('Arquivo de teste maior que 16 MiB.')
                meta=window.workspace.save_blob(source.read_bytes(),source.name)
                window.run_task('Verificação local do pacote…',lambda:window.analyze_file(meta['id']),save_result)
            else:save_result()
        QTimer.singleShot(300,finish)
    return application.exec()
