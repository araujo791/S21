"""Native Windows/Qt desktop editor for graphical BIOS mapping projects."""
from pathlib import Path
import base64
import copy
import json
import math
import uuid

from PySide6.QtCore import Qt, QObject, QRunnable, QThreadPool, Signal, QTimer, QRectF, QPointF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics, QPixmap, QImage, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QSplitter,
    QLabel,QPushButton,QLineEdit,QTreeWidget,QTreeWidgetItem,QTabWidget,QPlainTextEdit,
    QGraphicsView,QGraphicsScene,QGraphicsObject,QGraphicsItem,QFileDialog,QMessageBox,
    QComboBox,QCheckBox,QDoubleSpinBox,QFormLayout,QDialog,QDialogButtonBox,QListWidget,
    QListWidgetItem,QAbstractItemView,QInputDialog,QScrollArea)

from . import __version__
from .firmware import load_firmware, require, sha
from .model import (make_project,auto_match,match_index,validate_project,read_project,write_project,
                    export_package,summary,STATUS,VALUE_KINDS,slot,set_test_value,image_size,clean)

COLORS={'linked':'#62c9a5','review':'#edbd66','unmatched':'#8e99aa','manual':'#78b6ff'}
STYLE='''
QMainWindow,QDialog{background:#10151d;color:#e7edf4} QWidget{color:#e7edf4;font-size:13px}
QLineEdit,QComboBox,QDoubleSpinBox,QPlainTextEdit,QTreeWidget,QListWidget{background:#192330;border:1px solid #334256;border-radius:5px;padding:5px}
QPushButton{background:#24354a;border:1px solid #435770;border-radius:5px;padding:8px 12px}
QPushButton:hover{background:#344c67} QPushButton:disabled{color:#738093;background:#19212b}
QPushButton#primary{background:#246b58;border-color:#3eac87} QTreeWidget::item:selected,QListWidget::item:selected{background:#344c67}
QHeaderView::section{background:#243247;color:#e7edf4;padding:5px;border:0}
QTabBar::tab{background:#192330;padding:8px}QTabBar::tab:selected{background:#344c67}
QSplitter::handle{background:#28374b}QToolTip{color:#fff;background:#24354a;border:1px solid #435770}
'''


def label(text=''):
    item=QLabel(text);item.setTextFormat(Qt.TextFormat.PlainText);item.setWordWrap(True)
    return item


class JobSignals(QObject):
    done=Signal(object)
    error=Signal(str)


class Job(QRunnable):
    def __init__(self,fn):
        super().__init__();self.fn=fn;self.signals=JobSignals()
    def run(self):
        try:self.signals.done.emit(self.fn())
        except Exception as exc:self.signals.error.emit(str(exc))


class Canvas(QGraphicsView):
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.scene():self.fitInView(self.scene().sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)


class ControlItem(QGraphicsObject):
    def __init__(self,owner,control):
        super().__init__();self.owner=owner;self.control=control
        x,y,w,h=control['rect'];self.w=w*1024;self.h=h*576
        self.setPos(x*1024,y*576)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable|QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,owner.edit_mode.isChecked())
        self.setZValue(20);self.setCursor(Qt.CursorShape.OpenHandCursor if owner.edit_mode.isChecked() else Qt.CursorShape.PointingHandCursor)
    def boundingRect(self):return QRectF(0,0,self.w,self.h)
    def paint(self,painter,option,widget=None):
        c=self.control;rect=self.boundingRect();selected=self.owner.selected_id==c['id']
        painter.setOpacity(1 if c['enabled'] else .4)
        if c['asset']:
            painter.drawPixmap(rect,self.owner.asset_pixmap(c['asset']),QRectF(self.owner.asset_pixmap(c['asset']).rect()))
        else:
            painter.fillRect(rect,QColor(30,17,21,200))
        if self.owner.edit_mode.isChecked() or selected:
            painter.setPen(QPen(QColor('#ffffff' if selected else COLORS[c['status']]),2 if selected else 1))
            painter.drawRect(rect.adjusted(1,1,-1,-1))
        if not c['hide_label']:
            painter.setFont(QFont('Segoe UI',max(10,min(16,int(self.h*.48)))))
            painter.setPen(QColor('#fff7c9' if selected else '#f1e9e2'))
            value=self.owner.display_value(c)
            fm=QFontMetrics(painter.font())
            text=fm.elidedText(c['label'],Qt.TextElideMode.ElideRight,int(self.w*.65)-14)
            painter.drawText(QRectF(10,0,self.w*.65-14,self.h),Qt.AlignmentFlag.AlignVCenter,text)
            painter.setPen(QColor('#e4c376'))
            text=fm.elidedText(value,Qt.TextElideMode.ElideRight,int(self.w*.35)-16)
            painter.drawText(QRectF(self.w*.65,0,self.w*.35-10,self.h),Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter,text)
        painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor(COLORS[c['status']]))
        painter.drawEllipse(QRectF(2,self.h/2-2,4,4))
    def itemChange(self,change,value):
        if change==QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            return QPointF(max(0,min(1024-self.w,value.x())),max(0,min(576-self.h,value.y())))
        return super().itemChange(change,value)
    def mousePressEvent(self,event):
        self.owner.select_control(self.control['id']);super().mousePressEvent(event)
    def mouseDoubleClickEvent(self,event):
        cid=self.control['id'];event.accept();QTimer.singleShot(0,lambda:self.owner.activate_control(cid))
    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        if self.owner.edit_mode.isChecked():
            self.control['rect'][0]=round(self.pos().x()/1024,6)
            self.control['rect'][1]=round(self.pos().y()/576,6)
            self.owner.dirty=True;self.owner.select_control(self.control['id'])


class AssetDialog(QDialog):
    def __init__(self,owner):
        super().__init__(owner);self.owner=owner;self.asset_id=None
        self.setWindowTitle('Recursos gráficos Covenant');self.resize(900,620)
        layout=QVBoxLayout(self)
        layout.addWidget(label('Selecione uma imagem original. As substituições mantêm as dimensões e ficam no projeto.'))
        self.search=QLineEdit();self.search.setPlaceholderText('Filtrar por nome ou dimensão');layout.addWidget(self.search)
        self.items=QListWidget();self.items.setViewMode(QListWidget.ViewMode.IconMode);self.items.setIconSize(QSize(135,85));self.items.setGridSize(QSize(190,126));self.items.setResizeMode(QListWidget.ResizeMode.Adjust)
        for asset in owner.catalog['images']:
            item=QListWidgetItem(QIcon(owner.asset_pixmap(asset['id'])),f"{asset['width']} × {asset['height']}\n{asset['id']}")
            item.setData(Qt.ItemDataRole.UserRole,asset['id']);self.items.addItem(item)
        layout.addWidget(self.items)
        self.search.textChanged.connect(lambda text:[self.items.item(i).setHidden(text.casefold() not in self.items.item(i).text().casefold()) for i in range(self.items.count())])
        buttons=QHBoxLayout();replace=QPushButton('Substituir imagem…');buttons.addWidget(replace)
        use=QPushButton('Usar no controle');buttons.addWidget(use)
        bg=QPushButton('Usar como fundo');buttons.addWidget(bg)
        close=QPushButton('Fechar');buttons.addWidget(close);layout.addLayout(buttons)
        close.clicked.connect(self.reject);replace.clicked.connect(self.replace)
        use.clicked.connect(lambda:self.choose(False));bg.clicked.connect(lambda:self.choose(True))
    def selected_asset(self):
        item=self.items.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None
    def replace(self):
        aid=self.selected_asset()
        if not aid:return
        path,_=QFileDialog.getOpenFileName(self,'Imagem editada','','PNG ou JPEG (*.png *.jpg *.jpeg)')
        if not path:return
        try:
            with Path(path).open('rb') as f:blob=f.read(3*1024*1024+1)
            self.owner.import_asset(aid,blob)
            self.items.currentItem().setIcon(QIcon(self.owner.asset_pixmap(aid)))
        except Exception as exc:self.owner.error(str(exc))
    def choose(self,background):
        aid=self.selected_asset()
        if not aid:return
        if background:
            self.owner.page()['background']=aid
        else:
            c=self.owner.control()
            if not c:self.owner.error('Selecione primeiro um controle na tela.');return
            c['asset']=aid
        self.owner.dirty=True;self.owner.redraw();self.accept()


class BindDialog(QDialog):
    def __init__(self,owner,source,target):
        super().__init__(owner);self.setWindowTitle('Conferir opções do vínculo');self.boxes=[]
        layout=QVBoxLayout(self);layout.addWidget(label('Tradução das opções da origem para o campo da sua 002. Isso não valida um callback de firmware.'))
        form=QFormLayout();layout.addLayout(form)
        for option in source['options']:
            box=QComboBox()
            for t in target['options']:box.addItem(t['label'],t['value'])
            for i in range(box.count()):
                if clean(box.itemText(i)).casefold().rstrip('d')==clean(option['label']).casefold().rstrip('d'):box.setCurrentIndex(i);break
            form.addRow(option['label'],box);self.boxes.append((option['value'],box))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
    def mapping(self):return {value:box.currentData() for value,box in self.boxes}


class MainWindow(QMainWindow):
    def __init__(self,root=None):
        super().__init__();self.root=Path(root) if root else Path(__file__).resolve().parents[1]
        self.setWindowTitle('Covenant Graphics Studio · projeto gráfico da BIOS');self.resize(1540,920);self.setStyleSheet(STYLE)
        self.donor_blob=(self.root/'assets/doadora-hii.json').read_bytes();self.donor=json.loads(self.donor_blob);self.donor_sha=sha(self.donor_blob)
        self.catalog=json.loads((self.root/'assets/catalogo.json').read_text());self.asset_info={i['id']:i for i in self.catalog['images']}
        for aid,item in self.asset_info.items():
            require(Path(aid).name==aid and sha((self.root/'assets/imagens'/aid).read_bytes())==item['sha256'],'Recurso gráfico ausente ou modificado no pacote.')
        self.stock=None;self.project=None;self.current_page=None;self.selected_id=None;self.dirty=False;self.busy=False
        self.qmap={};self.pmap={};self.cmap={};self.controls_by_page={};self.pixmaps={};self.page_items={};self.stock_items={};self.hotkeys=[];self._updating=False;self._job=None
        self.build_ui()
        QShortcut(QKeySequence.StandardKey.Open,self,activated=self.open_bios)
        QShortcut(QKeySequence.StandardKey.Save,self,activated=self.save_project)
        self.update_enabled();self.redraw()
    def build_ui(self):
        central=QWidget();layout=QVBoxLayout(central);self.setCentralWidget(central)
        title=QHBoxLayout();heading=label('COVENANT  /  GRAPHICS STUDIO');heading.setWordWrap(False);title.addWidget(heading);title.addStretch();native=label('Janela nativa · sem navegador');native.setWordWrap(False);title.addWidget(native)
        layout.addLayout(title)
        layout.addWidget(label('Projeto e teste de vínculos gráficos. Esta versão exporta projetos; não compila uma ROM modificada.'))
        bar=QHBoxLayout();layout.addLayout(bar)
        self.open_button=QPushButton('1  Abrir BIOS 002…');self.open_button.setObjectName('primary');bar.addWidget(self.open_button)
        self.project_open=QPushButton('Abrir projeto…');bar.addWidget(self.project_open)
        self.project_save=QPushButton('Salvar projeto…');bar.addWidget(self.project_save)
        self.export_button=QPushButton('Exportar vínculos…');bar.addWidget(self.export_button)
        self.verify_button=QPushButton('Verificar projeto');bar.addWidget(self.verify_button)
        self.asset_button=QPushButton('Imagens…');bar.addWidget(self.asset_button)
        self.edit_mode=QCheckBox('Mover controles');bar.addWidget(self.edit_mode);bar.addStretch()
        self.open_button.clicked.connect(self.open_bios);self.project_open.clicked.connect(self.open_project)
        self.project_save.clicked.connect(self.save_project);self.export_button.clicked.connect(self.export_links)
        self.verify_button.clicked.connect(self.verify);self.asset_button.clicked.connect(lambda:AssetDialog(self).exec());self.edit_mode.toggled.connect(self.redraw)
        self.info=label('Abra sua BIOS 002 de 8 MiB ou o backup completo de 16 MiB.');layout.addWidget(self.info)
        split=QSplitter();layout.addWidget(split,1)
        left=QWidget();ll=QVBoxLayout(left);ll.setContentsMargins(0,0,0,0)
        self.filter=QLineEdit();self.filter.setPlaceholderText('Buscar páginas e opções');ll.addWidget(self.filter)
        self.tabs=QTabWidget();ll.addWidget(self.tabs)
        self.page_tree=QTreeWidget();self.page_tree.setHeaderLabels(['Páginas gráficas']);self.tabs.addTab(self.page_tree,'Páginas')
        self.stock_tree=QTreeWidget();self.stock_tree.setHeaderLabels(['Opções reais da 002']);self.tabs.addTab(self.stock_tree,'BIOS 002')
        self.filter.textChanged.connect(self.filter_trees);self.page_tree.itemSelectionChanged.connect(self.page_selected)
        self.stock_tree.itemDoubleClicked.connect(lambda item,col:self.add_stock_control())
        self.add_button=QPushButton('Adicionar opção selecionada à tela');self.add_button.clicked.connect(self.add_stock_control);ll.addWidget(self.add_button)
        split.addWidget(left)
        middle=QWidget();ml=QVBoxLayout(middle);ml.setContentsMargins(0,0,0,0)
        self.page_title=label('Prévia gráfica');ml.addWidget(self.page_title)
        self.scene=QGraphicsScene();self.scene.setSceneRect(0,0,1024,576)
        self.canvas=Canvas(self.scene);self.canvas.setBackgroundBrush(QColor('#10151d'));self.canvas.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform);self.canvas.setMinimumSize(500,350);ml.addWidget(self.canvas,1)
        ml.addWidget(label('Duplo clique em um controle para testar. Valores são locais ao projeto; não são valores lidos da placa.'))
        self.totals=label('');ml.addWidget(self.totals);split.addWidget(middle)
        right=QWidget();rl=QVBoxLayout(right);rl.setContentsMargins(0,0,0,0)
        rl.addWidget(label('Controle selecionado'))
        self.control_label=QLineEdit();rl.addWidget(self.control_label)
        self.control_label.editingFinished.connect(self.rename_control)
        self.details=QPlainTextEdit();self.details.setReadOnly(True);self.details.setMinimumHeight(220);rl.addWidget(self.details,1)
        self.test_button=QPushButton('Testar valor / abrir destino');self.test_button.clicked.connect(lambda:self.activate_control(self.selected_id));rl.addWidget(self.test_button)
        self.bind_button=QPushButton('Vincular à opção selecionada da 002');self.bind_button.clicked.connect(self.bind_selected);rl.addWidget(self.bind_button)
        self.auto_button=QPushButton('Recalcular sugestão deste controle');self.auto_button.clicked.connect(self.rematch_selected);rl.addWidget(self.auto_button)
        form=QFormLayout();rl.addLayout(form);self.geometry=[]
        for name in ('X (%)','Y (%)','Largura (%)','Altura (%)'):
            box=QDoubleSpinBox();box.setRange(0,100);box.setDecimals(2);box.setSingleStep(.5);box.valueChanged.connect(self.change_geometry);form.addRow(name,box);self.geometry.append(box)
        self.shortcut=QLineEdit();self.shortcut.setPlaceholderText('F1–F12 ou letra');form.addRow('Atalho',self.shortcut);self.shortcut.editingFinished.connect(self.change_shortcut)
        self.hide_label=QCheckBox('Ocultar texto sobre a imagem');rl.addWidget(self.hide_label);self.hide_label.toggled.connect(self.change_flags)
        self.control_enabled=QCheckBox('Controle ativo');rl.addWidget(self.control_enabled);self.control_enabled.toggled.connect(self.change_flags)
        remove=QPushButton('Remover imagem deste controle');remove.clicked.connect(self.remove_asset);rl.addWidget(remove)
        self.remove_asset_button=remove;split.addWidget(right)
        split.setSizes([270,930,330])
        self.statusBar().showMessage('Projeto offline • nenhum acesso ao chip ou às variáveis EFI • sem compilador de ROM')
    def error(self,message):QMessageBox.warning(self,'Covenant Graphics Studio',str(message))
    def update_enabled(self):
        ready=self.project is not None and not self.busy
        for button in (self.project_open,self.project_save,self.export_button,self.verify_button,self.asset_button,self.add_button):button.setEnabled(ready)
        self.open_button.setEnabled(not self.busy)
        for button in (self.test_button,self.bind_button,self.auto_button,self.remove_asset_button):button.setEnabled(ready and self.selected_id in self.cmap)
        self.auto_button.setEnabled(bool(ready and self.control() and self.control()['source_origin']=='donor'))
    def open_bios(self):
        if self.busy:return
        if self.dirty and QMessageBox.question(self,'Projeto não salvo','Abrir outra BIOS e descartar alterações não salvas?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        path,_=QFileDialog.getOpenFileName(self,'Abrir BIOS Machinist 002','','BIOS (*.bin *.rom);;Todos os arquivos (*)')
        if path:self.load_bios(path)
    def load_bios(self,path):
        if self.busy:return
        self.busy=True;self.update_enabled();self.info.setText('Lendo estrutura UEFI e formulários; criando vínculos…')
        def work():
            stock=load_firmware(path);project=make_project(stock,self.donor,self.catalog,self.donor_sha)
            validate_project(project,stock,self.donor,self.catalog,self.donor_sha)
            return stock,project
        job=Job(work);self._job=job
        job.signals.done.connect(self.loaded);job.signals.error.connect(self.load_failed)
        QThreadPool.globalInstance().start(job)
    def loaded(self,result):
        self.busy=False;self.stock,self.project=result;self.dirty=False;self.qmap={q['id']:q for q in self.stock['questions']}
        self.index_project();self.populate_trees();self.current_page='home';self.selected_id=self.controls_by_page.get('home',[{}])[0].get('id');self.pixmaps.clear()
        self.info.setText(f"{self.stock['bios_id']}  •  {self.stock['size']//1048576} MiB  •  {len(self.stock['forms'])} formulários / {len(self.qmap)} campos  •  formulário original: {'sim' if self.stock['original_ui_modules'] else 'alterado'}")
        self._job=None;self.update_enabled();self.redraw()
    def load_failed(self,message):
        self.busy=False;self._job=None;self.update_enabled();self.info.setText('A BIOS não foi carregada. O projeto anterior foi preservado.');self.error(message)
    def index_project(self):
        self.pmap={p['id']:p for p in self.project['pages']};self.cmap={c['id']:c for c in self.project['controls']};self.controls_by_page={}
        for c in self.project['controls']:self.controls_by_page.setdefault(c['page'],[]).append(c)
    def populate_trees(self):
        self.page_tree.blockSignals(True);self.page_tree.clear();self.stock_tree.clear();self.page_items={};self.stock_items={}
        parents={}
        for origin,title in (('stock','Menus da sua 002'),('donor','Sugestões a partir da doadora')):
            parents[origin]=QTreeWidgetItem(self.page_tree,[title])
        for p in self.project['pages']:
            item=QTreeWidgetItem(parents[p['origin']],[p['title']]);item.setData(0,Qt.ItemDataRole.UserRole,p['id']);self.page_items[p['id']]=item
        parents['stock'].setExpanded(True);parents['donor'].setExpanded(False)
        forms={}
        for f in self.stock['forms']:
            item=QTreeWidgetItem(self.stock_tree,[f['title']]);item.setData(0,Qt.ItemDataRole.UserRole,('form',f['id']));forms[f['id']]=item
        for q in self.stock['questions']:
            item=QTreeWidgetItem(forms[q['form']],[clean(q['prompt']) or q['kind']]);item.setData(0,Qt.ItemDataRole.UserRole,('question',q['id']));self.stock_items[q['id']]=item
        self.page_tree.blockSignals(False);self.filter_trees(self.filter.text())
    def filter_trees(self,text):
        term=text.casefold()
        def walk(item):
            visible=term in item.text(0).casefold()
            for i in range(item.childCount()):visible=walk(item.child(i)) or visible
            item.setHidden(not visible);return visible
        for tree in (self.page_tree,self.stock_tree):
            for i in range(tree.topLevelItemCount()):walk(tree.topLevelItem(i))
    def page_selected(self):
        selected=self.page_tree.selectedItems()
        if not selected:return
        pid=selected[0].data(0,Qt.ItemDataRole.UserRole)
        if pid in self.pmap:self.current_page=pid;self.selected_id=None;self.redraw()
    def page(self):return self.pmap[self.current_page]
    def control(self):return self.cmap.get(self.selected_id)
    def asset_pixmap(self,aid):
        if aid not in self.pixmaps:
            override=self.project['asset_overrides'].get(aid) if self.project else None
            if override:
                q=QImage.fromData(base64.b64decode(override));require(not q.isNull(),'Imagem inválida.')
                self.pixmaps[aid]=QPixmap.fromImage(q)
            else:self.pixmaps[aid]=QPixmap(str(self.root/'assets/imagens'/aid))
        return self.pixmaps[aid]
    def redraw(self,*args):
        self.scene.clear()
        bg=self.page()['background'] if self.project else self.catalog['background']
        pix=self.asset_pixmap(bg);item=self.scene.addPixmap(pix);item.setScale(1024/pix.width())
        brand=self.scene.addPixmap(self.asset_pixmap(self.catalog['brand']));brand.setPos(420,17);brand.setScale(1.7);brand.setZValue(10)
        x99=self.scene.addSimpleText('X99',QFont('Segoe UI',28,QFont.Weight.Bold));x99.setBrush(QColor('#e7e9ef'));x99.setPos(28,8)
        title=self.page()['title'] if self.project else 'Abra sua BIOS 002 para iniciar'
        t=self.scene.addSimpleText(title,QFont('Segoe UI',16));t.setBrush(QColor('#e7b65b'));t.setPos(68,82)
        if self.project:
            for c in self.controls_by_page.get(self.current_page,[]):self.scene.addItem(ControlItem(self,c))
            counts=summary(self.project)
            self.totals.setText(f"{counts['linked']} vínculos estruturais  ·  {counts['review']} para revisar  ·  {counts['unmatched']} sem vínculo  ·  {counts['manual']} manuais")
        self.page_title.setText(('Menus da 002 · ' if self.project and self.page()['origin']=='stock' else 'Sugestões da doadora · ' if self.project else '')+title)
        self.canvas.fitInView(self.scene.sceneRect(),Qt.AspectRatioMode.KeepAspectRatio)
        self.rebuild_shortcuts();self.select_control(self.selected_id)
    def display_value(self,c):
        if c['target_kind']=='form':return '›'
        q=self.qmap.get(c['target_id'])
        if not q:return '—'
        v=self.project['test_values'].get(slot(q))
        if v is None:return '—'
        return next((o['label'] for o in q['options'] if o['value']==v),v)
    def select_control(self,cid):
        self.selected_id=cid if cid in self.cmap else None;c=self.control();self._updating=True
        self.control_label.setText(c['label'] if c else '')
        if c:
            q=self.qmap.get(c['target_id']);lines=[STATUS[c['status']],c['reason'],'','Destino: '+(q['prompt'] if q else c['target_id'] or 'nenhum')]
            if q:
                lines += ['Variável: '+q['store']['name'],'GUID: '+q['store']['guid'],f"Offset: 0x{q['offset']:X} / largura {q['width']} byte(s)",
                          'Callback: '+str(q['callback'])+' · Condição: '+str(q['conditional']),'',q['help']]
                item=self.stock_items.get(q['id'])
                if item:self.stock_tree.setCurrentItem(item)
            lines+=['','Vínculo do projeto; o adaptador AMI de runtime não está implementado.']
            self.details.setPlainText('\n'.join(lines))
            for box,value in zip(self.geometry,c['rect']):box.setValue(value*100)
            self.shortcut.setText(c['shortcut']);self.hide_label.setChecked(c['hide_label']);self.control_enabled.setChecked(c['enabled'])
        else:self.details.clear();self.shortcut.clear()
        self._updating=False;self.scene.update();self.update_enabled()
    def rename_control(self):
        c=self.control()
        if not c or self._updating:return
        text=clean(self.control_label.text())
        if text:c['label']=text;self.dirty=True;self.scene.update()
    def change_flags(self):
        c=self.control()
        if self._updating or not c:return
        c['hide_label']=self.hide_label.isChecked();c['enabled']=self.control_enabled.isChecked();self.dirty=True;self.redraw()
    def change_geometry(self):
        c=self.control()
        if self._updating or not c:return
        x,y,w,h=[b.value()/100 for b in self.geometry]
        w=max(.005,min(1-x,w));h=max(.005,min(1-y,h));x=min(x,1-w);y=min(y,1-h)
        c['rect']=[x,y,w,h];self.dirty=True;self.redraw()
    def change_shortcut(self):
        c=self.control()
        if not c or self._updating:return
        previous=c['shortcut'];c['shortcut']=self.shortcut.text().strip().upper()
        try:validate_project(self.project,self.stock,self.donor,self.catalog,self.donor_sha)
        except ValueError as exc:c['shortcut']=previous;self.error(str(exc));self.shortcut.setText(previous);return
        self.dirty=True;self.rebuild_shortcuts()
    def rebuild_shortcuts(self):
        for s in self.hotkeys:s.setEnabled(False);s.deleteLater()
        self.hotkeys=[]
        if not self.project:return
        for c in self.controls_by_page.get(self.current_page,[]):
            if c['shortcut'] and c['enabled']:
                cid=c['id'];s=QShortcut(QKeySequence(c['shortcut']),self);s.activated.connect(lambda cid=cid:self.activate_control(cid));self.hotkeys.append(s)
    def activate_control(self,cid):
        c=self.cmap.get(cid)
        if not c or not c['enabled']:return
        if c['target_kind']=='form':
            page=next((p for p in self.project['pages'] if p['origin']=='stock' and p['form']==c['target_id']),None)
            if page:self.current_page=page['id'];self.selected_id=None;self.page_tree.setCurrentItem(self.page_items[page['id']]);self.redraw()
            return
        q=self.qmap.get(c['target_id'])
        if not q:self.error('Controle sem vínculo. Selecione uma opção da 002 e associe-a.');return
        if q['read_only']:self.error('Campo marcado somente para leitura no IFR.');return
        if q['kind'] in ('oneof','checkbox'):
            choices=[o['label']+'  ['+o['value']+']' for o in q['options']]
            text,ok=QInputDialog.getItem(self,'Valor de teste · não grava a BIOS',q['prompt'],choices,0,False)
            if not ok:return
            value=q['options'][choices.index(text)]['value']
        else:
            value,ok=QInputDialog.getText(self,'Valor numérico de teste',q['prompt']+f" ({q['minimum']}…{q['maximum']})",text=self.project['test_values'].get(slot(q),q['minimum']))
            if not ok:return
        try:set_test_value(self.project,q,value)
        except ValueError as exc:self.error(str(exc));return
        self.dirty=True;self.redraw()
    def selected_stock_question(self):
        items=self.stock_tree.selectedItems()
        if not items:return None
        d=items[0].data(0,Qt.ItemDataRole.UserRole)
        return self.qmap.get(d[1]) if d and d[0]=='question' else None
    def bind_selected(self):
        c=self.control();target=self.selected_stock_question()
        if not c or not target:return
        if target['kind'] not in VALUE_KINDS or not target['storage_valid']:self.error('Selecione um campo de valor com armazenamento válido.');return
        source=(self.qmap if c['source_origin']=='stock' else {q['id']:q for q in self.donor['questions']}).get(c['source_id'])
        mapping={}
        if source:
            if source['kind'] in ('oneof','checkbox') and target['kind'] in ('oneof','checkbox'):
                dialog=BindDialog(self,source,target)
                if dialog.exec()!=QDialog.DialogCode.Accepted:return
                mapping=dialog.mapping()
            elif source['kind']=='numeric' and target['kind']=='numeric':
                from .model import value_map
                mapping,error=value_map(source,target)
                if mapping is None:self.error(error);return
            else:self.error('Os tipos dos controles não correspondem.');return
        previous=copy.deepcopy(c)
        c.update(target_kind='question',target_id=target['id'],value_map=mapping,status='manual',reason='Vínculo escolhido no projeto; runtime/callback não validado.')
        try:validate_project(self.project,self.stock,self.donor,self.catalog,self.donor_sha)
        except ValueError as exc:c.clear();c.update(previous);self.error(str(exc));return
        self.dirty=True;self.redraw()
    def rematch_selected(self):
        c=self.control()
        if not c or c['source_origin']!='donor':return
        q=dict(next(q for q in self.donor['questions'] if q['id']==c['source_id']))
        if q['kind']=='ref':
            forms=[f for f in self.donor['forms'] if f['form_id']==q.get('target_form_id') and f['formset']==q.get('target_formset')]
            if len(forms)==1:q['_target_title']=forms[0]['title']
        c.update(auto_match(q,self.stock));self.dirty=True;self.redraw()
    def add_stock_control(self):
        if not self.project:return
        q=self.selected_stock_question()
        if not q or q['kind'] not in VALUE_KINDS or not q['storage_valid']:self.error('Selecione um campo de valor válido na aba BIOS 002.');return
        c={'id':'custom-'+uuid.uuid4().hex,'source_origin':'stock','source_id':None,'page':self.current_page,
           'label':clean(q['prompt']),'rect':[.075,.82,.85,.044],'asset':None,'hide_label':False,'shortcut':'','enabled':True,
           'target_kind':'question','target_id':q['id'],'status':'manual','reason':'Controle criado diretamente do campo da 002; runtime não implementado.','value_map':{}}
        self.project['controls'].append(c);self.index_project();self.selected_id=c['id'];self.dirty=True;self.redraw()
    def import_asset(self,aid,blob):
        info=self.asset_info[aid]
        require(image_size(blob)==(info['width'],info['height']),f"Mantenha {info['width']} × {info['height']} pixels.")
        require(not QImage.fromData(blob).isNull(),'A imagem não foi decodificada pelo Qt.')
        previous=self.project['asset_overrides'].get(aid)
        self.project['asset_overrides'][aid]=base64.b64encode(blob).decode()
        try:validate_project(self.project,self.stock,self.donor,self.catalog,self.donor_sha)
        except Exception:
            if previous is None:self.project['asset_overrides'].pop(aid)
            else:self.project['asset_overrides'][aid]=previous
            raise
        self.pixmaps.pop(aid,None);self.dirty=True;self.redraw()
    def remove_asset(self):
        c=self.control()
        if c:c['asset']=None;self.dirty=True;self.redraw()
    def verify(self):
        if not self.project:return
        try:validate_project(self.project,self.stock,self.donor,self.catalog,self.donor_sha)
        except Exception as exc:self.error(str(exc));return
        QMessageBox.information(self,'Projeto verificado','Identidades, destinos, opções, imagens, posições e atalhos conferidos.\n\nIsso valida o projeto, não boot, callbacks ou uma ROM gráfica.')
    def save_to(self,path):
        write_project(path,self.project,self.stock,self.donor,self.catalog,self.donor_sha);self.dirty=False
    def save_project(self):
        if not self.project:return
        path,_=QFileDialog.getSaveFileName(self,'Salvar projeto','','Projeto Covenant (*.json)')
        if path:
            if Path(path).suffix.lower()!='.json':path+='.json'
            try:self.save_to(path)
            except Exception as exc:self.error(str(exc))
    def load_project_from(self,path):
        p=read_project(path,self.stock,self.donor,self.catalog,self.donor_sha)
        self.project=p;self.index_project();self.populate_trees();self.pixmaps.clear();self.current_page=p['pages'][0]['id'];self.selected_id=None;self.dirty=False;self.redraw()
    def open_project(self):
        if not self.stock:return
        if self.dirty and QMessageBox.question(self,'Projeto não salvo','Descartar as alterações atuais?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        path,_=QFileDialog.getOpenFileName(self,'Abrir projeto da BIOS carregada','','Projeto Covenant (*.json)')
        if path:
            try:self.load_project_from(path)
            except Exception as exc:self.error(str(exc))
    def export_links(self):
        if not self.project:return
        path,_=QFileDialog.getSaveFileName(self,'Exportar pacote de projeto','','Pacote de vínculos (*.zip)')
        if path:
            if Path(path).suffix.lower()!='.zip':path+='.zip'
            try:
                export_package(path,self.project,self.stock,self.donor,self.catalog,self.donor_sha)
                self.statusBar().showMessage('Pacote de projeto exportado. Não contém ROM para gravação.')
            except Exception as exc:self.error(str(exc))
    def closeEvent(self,event):
        if self.busy:
            self.error('Aguarde a análise terminar.');event.ignore();return
        if self.dirty and QMessageBox.question(self,'Projeto não salvo','Sair e descartar alterações não salvas?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:
            event.ignore();return
        event.accept()


def start(args):
    app=QApplication.instance() or QApplication([])
    window=MainWindow();window.show()
    if getattr(args,'smoke_bios',None):
        window.load_bios(args.smoke_bios)
        def finish():
            if window.busy:return
            if not window.stock:app.exit(2);return
            if args.smoke_screenshot:window.grab().save(args.smoke_screenshot)
            if args.smoke_report:
                Path(args.smoke_report).write_text(json.dumps({'native_window':True,'bios_id':window.stock['bios_id'],
                    'forms':len(window.stock['forms']),'questions':len(window.qmap),'links':summary(window.project),
                    'browser_used':False,'firmware_compiler_implemented':False},indent=2)+'\n')
            window.dirty=False;app.quit()
        timer=QTimer();timer.timeout.connect(finish);timer.start(100)
    return app.exec()
