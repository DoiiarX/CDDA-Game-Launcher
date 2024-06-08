# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import requests
import html
import json
import yaml
import logging
import os
import random
import shutil
import tempfile
import zipfile
from collections import deque
from datetime import datetime
from os import scandir
from urllib.parse import urljoin, urlencode

import rarfile
from PyQt5.QtCore import Qt, QTimer, QUrl, QFileInfo, QStringListModel
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QTextBrowser,
    QTabWidget, QMessageBox, QHBoxLayout, QListView, QAbstractItemView, QTextEdit, QPlainTextEdit
)
from PyQt5.QtGui import QTextCursor
from py7zlib import Archive7z, NoPasswordGivenError, FormatError
from werkzeug.http import parse_options_header
from werkzeug.utils import secure_filename

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.constants import get_data_path, get_cddagl_path
from cddagl.functions import sizeof_fmt, delete_path
from cddagl.i18n import proxy_gettext as _
from cddagl.ui.views.dialogs import BrowserDownloadDialog

logger = logging.getLogger('cddagl')

rarfile.UNRAR_TOOL = get_cddagl_path('UnRAR.exe')


class ModsTab(QWidget):
    def __init__(self):
        super(ModsTab, self).__init__()

        self.tab_disabled = False
        self.qnam = QNetworkAccessManager()

        self.http_reply = None
        self.current_repo_info = None

        self.mods = []
        self.mods_model = None

        self.installing_new_mod = False
        self.downloading_new_mod = False
        self.extracting_new_mod = False

        self.install_type = None
        self.extracting_file = None
        self.extracting_zipfile = None

        self.close_after_install = False

        self.game_dir = None
        self.mods_dir = None
        self.user_mods_dir = None

        layout = QVBoxLayout()

        top_part = QWidget()
        tp_layout = QHBoxLayout() # 水平组布局控件
        tp_layout.setContentsMargins(0, 0, 0, 0)
        self.tp_layout = tp_layout

        installed_gb = QGroupBox()
        tp_layout.addWidget(installed_gb)
        self.installed_gb = installed_gb

        installed_gb_layout = QVBoxLayout()
        installed_gb.setLayout(installed_gb_layout)
        self.installed_gb_layout = installed_gb_layout

        installed_lv = QListView()
        installed_lv.clicked.connect(self.installed_clicked)
        installed_lv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        installed_gb_layout.addWidget(installed_lv)
        self.installed_lv = installed_lv

        installed_buttons = QWidget()
        ib_layout = QHBoxLayout() # 水平按钮布局控件
        installed_buttons.setLayout(ib_layout)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self.ib_layout = ib_layout
        self.installed_buttons = installed_buttons
        installed_gb_layout.addWidget(installed_buttons)

        disable_existing_button = QPushButton()
        disable_existing_button.setStyleSheet('''QPushButton {
            background-color: #f39c12; /* 橙色 */
            color: white;
            }
            QPushButton:hover {
        background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #e67e22;
            }
        ''')
        disable_existing_button.clicked.connect(self.disable_existing)
        disable_existing_button.setEnabled(False)
        ib_layout.addWidget(disable_existing_button)
        self.disable_existing_button = disable_existing_button

        delete_existing_button = QPushButton()
        delete_existing_button.setStyleSheet('''QPushButton {
            background-color: #c0392b; /* 暗红色 */
            color: white;
        }
        QPushButton:hover {
            background-color: #e74c3c;
        }
        QPushButton:pressed {
            background-color: #a93226;
        }
        ''')
        delete_existing_button.clicked.connect(self.delete_existing)
        delete_existing_button.setEnabled(False)
        ib_layout.addWidget(delete_existing_button)
        self.delete_existing_button = delete_existing_button

        repository_gb = QGroupBox()
        tp_layout.addWidget(repository_gb)
        self.repository_gb = repository_gb

        repository_gb_layout = QVBoxLayout()
        repository_gb.setLayout(repository_gb_layout)
        self.repository_gb_layout = repository_gb_layout

        repository_lv = QListView()
        repository_lv.clicked.connect(self.repository_clicked)
        repository_lv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        repository_gb_layout.addWidget(repository_lv)
        self.repository_lv = repository_lv

        suggest_new_label = QLabel()
        suggest_new_label.setOpenExternalLinks(True)
        repository_gb_layout.addWidget(suggest_new_label)
        self.suggest_new_label = suggest_new_label

        install_new_button = QPushButton()
        install_new_button.clicked.connect(self.install_new)
        install_new_button.setEnabled(False)
        repository_gb_layout.addWidget(install_new_button)
        self.install_new_button = install_new_button

        top_part.setLayout(tp_layout)
        layout.addWidget(top_part)
        self.top_part = top_part

        details_gb = QGroupBox()
        layout.addWidget(details_gb)
        self.details_gb = details_gb

        details_gb_layout = QGridLayout()

        # 名称 + 作者
        name_label = QLabel()
        details_gb_layout.addWidget(name_label, 0, 0, Qt.AlignRight)
        self.name_label = name_label

        name_le = QLineEdit()
        name_le.setReadOnly(True)
        details_gb_layout.addWidget(name_le, 0, 1)
        self.name_le = name_le

        author_label = QLabel()
        details_gb_layout.addWidget(author_label, 0, 2, Qt.AlignRight)
        self.author_label = author_label

        author_le = QLineEdit()
        author_le.setReadOnly(True)
        details_gb_layout.addWidget(author_le, 0, 3)
        self.author_le = author_le
        
        # 鉴别 + 类别
        ident_label = QLabel()
        details_gb_layout.addWidget(ident_label, 1, 0, Qt.AlignRight)
        self.ident_label = ident_label

        ident_le = QLineEdit()
        ident_le.setReadOnly(True)
        details_gb_layout.addWidget(ident_le, 1, 1)
        self.ident_le = ident_le

        category_label = QLabel()
        details_gb_layout.addWidget(category_label, 1, 2, Qt.AlignRight)
        self.category_label = category_label

        category_le = QLineEdit()
        category_le.setReadOnly(True)
        details_gb_layout.addWidget(category_le, 1, 3)
        self.category_le = category_le
        
        # 描述
        description_label = QLabel()
        details_gb_layout.addWidget(description_label, 2, 0, 1, 1, Qt.AlignRight)
        self.description_label = description_label

        description_le = QPlainTextEdit()
        description_le.setReadOnly(True)
        details_gb_layout.addWidget(description_le, 2, 1, 2, 3)
        self.description_le = description_le

        # 链接 + 尺寸
        path_label = QLabel()
        details_gb_layout.addWidget(path_label, 4, 0, Qt.AlignRight)
        self.path_label = path_label

        path_le = QLineEdit()
        path_le.setReadOnly(True)
        details_gb_layout.addWidget(path_le, 4, 1)
        self.path_le = path_le

        size_label = QLabel()
        details_gb_layout.addWidget(size_label, 4, 2, Qt.AlignRight)
        self.size_label = size_label

        size_le = QLineEdit()
        size_le.setReadOnly(True)
        details_gb_layout.addWidget(size_le, 4, 3)
        self.size_le = size_le

        # 主页 + 版本
        homepage_label = QLabel()
        details_gb_layout.addWidget(homepage_label, 5, 0, Qt.AlignRight)
        self.homepage_label = homepage_label

        homepage_tb = QTextBrowser()
        homepage_tb.setReadOnly(True)
        homepage_tb.setOpenExternalLinks(True)
        homepage_tb.setMaximumHeight(23)
        homepage_tb.setLineWrapMode(QTextEdit.NoWrap)
        homepage_tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        details_gb_layout.addWidget(homepage_tb, 5, 1)
        self.homepage_tb = homepage_tb

        version_label = QLabel()
        details_gb_layout.addWidget(version_label, 5, 2, Qt.AlignRight)
        self.version_label = version_label

        version_le = QLineEdit()
        version_le.setReadOnly(True)
        details_gb_layout.addWidget(version_le, 5, 3)
        self.version_le = version_le

        details_gb.setLayout(details_gb_layout)
        self.details_gb_layout = details_gb_layout

        self.setLayout(layout)

        self.load_repository()
        self.set_text()

    def set_text(self):
        self.installed_gb.setTitle(_('Installed'))
        self.disable_existing_button.setText(_('Disable'))
        self.delete_existing_button.setText(_('Delete'))
        suggest_url = 'https://notion.doiiars.com/article/CDDA-Game-Launcher#2817a04097ea42c1a462d1133d0520ec'
#         suggest_url = cons.NEW_ISSUE_URL + '?' + urlencode({
#             'title': _('Add this new mod to the repository'),
#             'body': _('''## 请求加入模组：模组名[模组支持的游戏版本]

# ```
# - type: direct_download  # 可选项: direct_download, github_release, github_repo, gitlab_repo, custom
#   ident: unique_mod_identifier  # 您的mod的唯一标识符
#   name: Mod Name  # 您的mod的名称
#   authors:  # 作者信息，可以是单个作者或作者列表
#     - Author1
#     - Author2
#   maintainers:  # 可选项：如果有维护者，包括维护者信息
#     - Maintainer1
#     - Maintainer2
#   description: A brief description of your mod.  # 简要描述您的mod
#   category: content  # 您的mod所属的类别，如items, creatures, vehicles, buildings, misc_additions, rebalance, monster_exclude, total_conversion, content等
#   dependencies:  # 可选项：如果您的mod依赖于其他mod，列出这些依赖项
#     - mod_dependency1
#     - mod_dependency2
#   size: 12345  # 您的mod的文件大小，以字节为单位
#   url: https://github.com/your_username/your_mod_repo/archive/master.zip  # 您的mod的下载链接
#   homepage: https://link_to_your_mod_homepage.com  # 您的mod的主页链接
# ```''').format(version=version)
#         })
        self.suggest_new_label.setText(_('<a href="{url}">贡献模组/提交模组</a>').format(url=suggest_url))
        self.repository_gb.setTitle(_('Repository'))
        self.install_new_button.setText(_('Install this mod'))
        self.details_gb.setTitle(_('Details'))
        self.name_label.setText(_('Name:'))
        self.ident_label.setText(_('Ident:'))
        self.author_label.setText(_('Author:'))
        self.description_label.setText(_('Description:'))
        self.category_label.setText(_('Category:'))

        selection_model = self.repository_lv.selectionModel()
        if selection_model is not None and selection_model.hasSelection():
            self.path_label.setText(_('Url:'))
        else:
            self.path_label.setText(_('Path:'))

        self.size_label.setText(_('Size:'))
        self.homepage_label.setText(_('Home page:'))
        self.version_label.setText(_('Version:'))

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab

    def get_soundpacks_tab(self):
        return self.get_main_tab().get_soundpacks_tab()

    def get_settings_tab(self):
        return self.get_main_tab().get_settings_tab()

    def get_backups_tab(self):
        return self.get_main_tab().get_backups_tab()

    def disable_tab(self):
        self.tab_disabled = True

        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)

        self.install_new_button.setEnabled(False)

        installed_selection = self.installed_lv.selectionModel()
        if installed_selection is not None:
            installed_selection.clearSelection()

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

    def enable_tab(self):
        self.tab_disabled = False

        installed_selection = self.installed_lv.selectionModel()
        if installed_selection is None:
            installed_selected = False
        else:
            installed_selected = installed_selection.hasSelection()

        self.disable_existing_button.setEnabled(installed_selected)
        self.delete_existing_button.setEnabled(installed_selected)

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is None:
            repository_selected = False
        else:
            repository_selected = repository_selection.hasSelection()

        self.install_new_button.setEnabled(repository_selected)
    
    def get_mods_yaml_file(self):
        """尝试从远程获取 mods.yaml 文件，失败则使用本地文件"""
        try:
            response = requests.get(cons.GITHUB_REST_API_URL + cons.REMOTE_MODS_URL)
            response.raise_for_status()
            with open(get_data_path('mods.yaml'), 'wb') as f:
                f.write(response.content)
            return get_data_path('mods.yaml')
        except requests.RequestException:
            logger.warning("无法从远程获取 mods.yaml 文件，使用本地文件")
            return get_data_path('mods.yaml')

    def load_repository(self):
        """加载存储库。"""
        self.repo_mods = []

        self.install_new_button.setEnabled(False)  # 禁用“安装新模组”按钮

        self.repo_mods_model = QStringListModel()
        self.repository_lv.setModel(self.repo_mods_model)
        # 连接列表视图选择变更事件到repository_selection方法
        self.repository_lv.selectionModel().currentChanged.connect(
            self.repository_selection)

        yaml_file = self.get_mods_yaml_file()  # 获取mods.yaml文件的路径

        if os.path.isfile(yaml_file):  # 检查文件是否存在
            with open(yaml_file, 'r', encoding='utf8') as f:  # 打开YAML文件
                try:
                    values = yaml.safe_load(f)  # 解析YAML文件
                    if isinstance(values, list):  # 检查values是否为列表
                        # 按模组名称排序
                        values.sort(key=lambda x: x['name'])
                        self.repo_mods = values

                        # 在列表模型中插入行
                        self.repo_mods_model.insertRows(
                            self.repo_mods_model.rowCount(),
                            len(self.repo_mods))
                        for index, mod_info in enumerate(self.repo_mods):
                            # 设置列表模型数据
                            self.repo_mods_model.setData(
                                self.repo_mods_model.index(index),
                                mod_info['name'])
                except yaml.YAMLError:  # 处理YAML解析错误
                    pass


    def install_new(self):
        if not self.installing_new_mod:
            selection_model = self.repository_lv.selectionModel()
            if selection_model is None or not selection_model.hasSelection():
                return

            selected = selection_model.currentIndex()
            selected_info = self.repo_mods[selected.row()]

            mod_idents = selected_info['ident']
            if isinstance(mod_idents, list):
                mod_idents = set(mod_idents)
            else:
                mod_idents = set((mod_idents, ))

            # Is it already installed?
            self.check_and_confirm_mod_installation(mod_idents, selected_info)

            
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()
                
            self.install_type = selected_info['type']

            if selected_info['type'] == 'direct_download':
                if self.http_reply is not None and self.http_reply.isRunning():
                    self.http_reply_aborted = True
                    self.http_reply.abort()

                self.installing_new_mod = True
                self.download_aborted = False

                download_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)
                self.download_dir = download_dir

                download_url = selected_info['url']

                url = QUrl(download_url)
                file_info = QFileInfo(url.path())
                file_name = file_info.fileName()
                self.downloaded_file = os.path.join(self.download_dir,
                    file_name)
                self.download_first_ready = True
                self.downloading_file = None

                
                status_bar.clearMessage()

                status_bar.busy += 1

                downloading_label = QLabel()
                downloading_label.setText(_('Downloading: {0}').format(
                    selected_info['url']))
                status_bar.addWidget(downloading_label, 100)
                self.downloading_label = downloading_label

                dowloading_speed_label = QLabel()
                status_bar.addWidget(dowloading_speed_label)
                self.dowloading_speed_label = dowloading_speed_label

                downloading_size_label = QLabel()
                status_bar.addWidget(downloading_size_label)
                self.downloading_size_label = downloading_size_label

                progress_bar = QProgressBar()
                status_bar.addWidget(progress_bar)
                self.downloading_progress_bar = progress_bar
                progress_bar.setMinimum(0)

                self.download_last_read = datetime.utcnow()
                self.download_last_bytes_read = 0
                self.download_speed_count = 0

                self.downloading_new_mod = True

                request = QNetworkRequest(QUrl(url))
                request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(
                    self.download_http_finished)
                self.download_http_reply.readyRead.connect(
                    self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(
                    self.download_dl_progress)
                
                self.cancel_installation()

            elif selected_info['type'] == 'browser_download':
                bd_dialog = BrowserDownloadDialog('mod',
                    selected_info['url'], selected_info.get('expected_filename',
                        None))
                bd_dialog.exec()

                if bd_dialog.downloaded_path is not None:


                    if not os.path.isfile(bd_dialog.downloaded_path):
                        status_bar.showMessage(_('Could not find downloaded '
                            'file archive'))
                    else:
                        self.installing_new_mod = True
                        self.downloaded_file = bd_dialog.downloaded_path

                        self.cancel_installation()
                        
                        # Test downloaded file
                        status_bar.showMessage(_('Testing downloaded file '
                            'archive'))

                        if self.downloaded_file.lower().endswith('.7z'):
                            try:
                                with open(self.downloaded_file, 'rb') as f:
                                    archive = Archive7z(f)
                            except FormatError:
                                status_bar.clearMessage()
                                status_bar.showMessage(_('Selected file is a '
                                    'bad archive file'))

                                self.finish_install_new_mod()
                                return
                            except NoPasswordGivenError:
                                status_bar.clearMessage()
                                status_bar.showMessage(_('Selected file is a '
                                    'password protected archive file'))

                                self.finish_install_new_mod()
                                return
                        else:
                            if self.downloaded_file.lower().endswith('.zip'):
                                archive_class = zipfile.ZipFile
                                archive_exception = zipfile.BadZipFile
                                test_method = 'testzip'
                            elif self.downloaded_file.lower().endswith('.rar'):
                                archive_class = rarfile.RarFile
                                archive_exception = rarfile.Error
                                test_method = 'testrar'

                            try:
                                with archive_class(self.downloaded_file) as z:
                                    test = getattr(z, test_method)
                                    if test() is not None:
                                        status_bar.clearMessage()
                                        status_bar.showMessage(
                                            _('Downloaded archive is invalid'))

                                        self.finish_install_new_mod()
                                        return
                            except archive_exception:
                                status_bar.clearMessage()
                                status_bar.showMessage(_('Selected file is a '
                                    'bad archive file'))

                                self.finish_install_new_mod()
                                return

                        status_bar.clearMessage()
                        self.extract_new_mod()
        else:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            # Cancel installation
            if self.downloading_new_mod:
                self.download_aborted = True
                self.download_http_reply.abort()
            elif self.extracting_new_mod:
                self.extracting_timer.stop()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_new_mod = False

                if self.extracting_zipfile is not None:
                    self.extracting_zipfile.close()

                if self.install_type == 'direct_download':
                    download_dir = os.path.dirname(self.downloaded_file)
                    delete_path(download_dir)

                if os.path.isdir(self.extract_dir):
                    delete_path(self.extract_dir)

            status_bar.showMessage(_('Mod installation cancelled'))

            self.finish_install_new_mod()
    
    
    def cancel_installation(self):
        self.install_new_button.setText(_('Cancel mod installation'))
        self.installed_lv.setEnabled(False)
        self.repository_lv.setEnabled(False)

        self.get_main_tab().disable_tab()
        self.get_soundpacks_tab().disable_tab()
        self.get_settings_tab().disable_tab()
        self.get_backups_tab().disable_tab()
     
    def check_and_confirm_mod_installation(self, mod_idents, selected_info):
        for mod in self.mods:
            if mod['ident'] in mod_idents:
                confirm_msgbox = QMessageBox()
                confirm_msgbox.setWindowTitle(_('Mod already present'))
                confirm_msgbox.setText(_('It seems this mod is '
                    'already installed. The launcher will not overwrite '
                    'the mod if it has the same directory name. You '
                    'might want to delete the mod first if you want '
                    'to update it. Also, there can only be a single '
                    'mod with the same ident value available in the '
                    'game.'))
                confirm_msgbox.setInformativeText(_('Are you sure you want '
                    'to install the {name} mod?').format(
                        name=selected_info['name']))
                confirm_msgbox.addButton(_('Install the mod'),
                    QMessageBox.YesRole)
                confirm_msgbox.addButton(_('Do not install again'),
                    QMessageBox.NoRole)
                confirm_msgbox.setIcon(QMessageBox.Warning)

                if confirm_msgbox.exec() == 1:
                    return
                break
            
    def download_http_finished(self):
        if self.downloading_file is not None:
            self.downloading_file.close()

        self.clear_download_ui()
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()
        if self.download_aborted:
            delete_path(self.download_dir)

            self.downloading_new_mod = False
        else:
            redirect = self.download_http_reply.attribute(
                QNetworkRequest.RedirectionTargetAttribute)
            if redirect is not None:
                self.handle_redirection(redirect)
                dowloading_speed_label = QLabel()
                status_bar.addWidget(dowloading_speed_label)
                self.dowloading_speed_label = dowloading_speed_label

                downloading_size_label = QLabel()
                status_bar.addWidget(downloading_size_label)
                self.downloading_size_label = downloading_size_label

                progress_bar = QProgressBar()
                status_bar.addWidget(progress_bar)
                self.downloading_progress_bar = progress_bar
                progress_bar.setMinimum(0)

                self.download_last_read = datetime.utcnow()
                self.download_last_bytes_read = 0
                self.download_speed_count = 0

                progress_bar.setValue(0)

                self.download_first_ready = True
                self.downloading_file = None

                request = QNetworkRequest(QUrl(redirected_url))
                request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(
                    self.download_http_finished)
                self.download_http_reply.readyRead.connect(
                    self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(
                    self.download_dl_progress)
            else:
                if not os.path.exists(self.downloaded_file):
                    status_bar.clearMessage()
                    status_bar.showMessage(
                        _('Could not find downloaded archive ({file})'
                        ).format(file=self.downloaded_file))

                    self.finish_install_new_mod()
                    return

                # Test downloaded file
                status_bar.showMessage(_('Testing downloaded file archive'))

                if self.downloaded_file.lower().endswith('.7z'):
                    try:
                        with open(self.downloaded_file, 'rb') as f:
                            archive = Archive7z(f)
                    except FormatError:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'bad archive file'))

                        self.finish_install_new_mod()
                        return
                    except NoPasswordGivenError:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'password protected archive file'))

                        self.finish_install_new_mod()
                        return
                else:
                    if self.downloaded_file.lower().endswith('.zip'):
                        archive_class = zipfile.ZipFile
                        archive_exception = zipfile.BadZipFile
                        test_method = 'testzip'
                    elif self.downloaded_file.lower().endswith('.rar'):
                        archive_class = rarfile.RarFile
                        archive_exception = rarfile.Error
                        test_method = 'testrar'
                    else:
                        extension = os.path.splitext(self.downloaded_file)[1]
                        status_bar.clearMessage()
                        status_bar.showMessage(
                            _('Unknown downloaded archive format ({extension})'
                            ).format(extension=extension))

                        self.finish_install_new_mod()
                        return

                    try:
                        with archive_class(self.downloaded_file) as z:
                            test = getattr(z, test_method)
                            if test() is not None:
                                status_bar.clearMessage()
                                status_bar.showMessage(
                                    _('Downloaded archive is invalid'))

                                self.finish_install_new_mod()
                                return
                    except archive_exception:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'bad archive file'))

                        self.finish_install_new_mod()
                        return

                status_bar.clearMessage()
                self.downloading_new_mod = False
                self.extract_new_mod()
    def handle_redirection(self, redirect):
        delete_path(self.download_dir)
        os.makedirs(self.download_dir)

        status_bar.busy += 1

        redirected_url = urljoin(
            self.download_http_reply.request().url().toString(),
            redirect.toString())

        downloading_label = QLabel()
        downloading_label.setText(_('Downloading: {0}').format(
            redirected_url))
        status_bar.addWidget(downloading_label, 100)
        self.downloading_label = downloading_label

    def clear_download_ui(self):
        if self.downloading_file is not None:
            self.downloading_file.close()

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.downloading_label)
        status_bar.removeWidget(self.dowloading_speed_label)
        status_bar.removeWidget(self.downloading_size_label)
        status_bar.removeWidget(self.downloading_progress_bar)
        status_bar.busy -= 1

    def finish_install_new_mod(self):
        self.installing_new_mod = False

        self.installed_lv.setEnabled(True)
        self.repository_lv.setEnabled(True)

        self.install_new_button.setText(_('Install this mod'))

        self.get_main_tab().enable_tab()
        self.get_soundpacks_tab().enable_tab()
        self.get_settings_tab().enable_tab()
        self.get_backups_tab().enable_tab()

        if self.close_after_install:
            self.get_main_window().close()

    def download_http_ready_read(self):
        if self.download_first_ready:
            self.download_first_ready = False

            cd_header = self.download_http_reply.header(QNetworkRequest.ContentDispositionHeader)
            
            if cd_header is not None:
                ctype, options = parse_options_header(cd_header)
                if 'filename' in options:
                    sfilename = secure_filename(options['filename'])
                    self.downloaded_file = os.path.join(self.download_dir, sfilename)

            self.downloading_file = open(self.downloaded_file, 'wb')

        while True:
            data = self.download_http_reply.read(cons.READ_BUFFER_SIZE)
            if not data:
                break
            self.downloading_file.write(data)

    def download_dl_progress(self, bytes_read, total_bytes):
        self.downloading_progress_bar.setMaximum(total_bytes)
        self.downloading_progress_bar.setValue(bytes_read)

        self.download_speed_count += 1

        self.downloading_size_label.setText(
            '{bytes_read}/{total_bytes}'
            .format(bytes_read=sizeof_fmt(bytes_read), total_bytes=sizeof_fmt(total_bytes))
        )

        if self.download_speed_count % 5 == 0:
            delta_bytes = bytes_read - self.download_last_bytes_read
            delta_time = datetime.utcnow() - self.download_last_read

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.dowloading_speed_label.setText(_('{bytes_sec}/s').format(
                bytes_sec=sizeof_fmt(bytes_secs)))

            self.download_last_bytes_read = bytes_read
            self.download_last_read = datetime.utcnow()

    def extract_new_mod(self):
        logger.debug(f'extract_new_mod:{self.game_dir}')
        self.extracting_new_mod = True

        if self.downloaded_file.lower().endswith('.7z'):
            self.extracting_zipfile = open(self.downloaded_file, 'rb')
            self.extracting_archive = Archive7z(self.extracting_zipfile)

            self.extracting_infolist = self.extracting_archive.getmembers()
        else:
            if self.downloaded_file.lower().endswith('.zip'):
                archive_class = zipfile.ZipFile
            elif self.downloaded_file.lower().endswith('.rar'):
                archive_class = rarfile.RarFile

            z = archive_class(self.downloaded_file)
            self.extracting_zipfile = z

            self.extracting_infolist = z.infolist()

        modname = os.path.basename(self.downloaded_file)
        modname, temp = os.path.splitext(modname)

        self.extract_dir = os.path.join(self.game_dir, modname)
        while os.path.exists(self.extract_dir):
            self.extract_dir = os.path.join(self.game_dir,
                'newmod-{0}'.format('%08x' % random.randrange(16**8)))
        os.makedirs(self.extract_dir)

        self.extracting_index = 0

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.busy += 1

        extracting_label = QLabel()
        status_bar.addWidget(extracting_label, 100)
        self.extracting_label = extracting_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.extracting_progress_bar = progress_bar

        timer = QTimer(self)
        self.extracting_timer = timer

        progress_bar.setRange(0, len(self.extracting_infolist))

        def timeout():
            self.extracting_progress_bar.setValue(self.extracting_index)

            if self.extracting_index == len(self.extracting_infolist):
                self.extracting_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_new_mod = False

                self.extracting_zipfile.close()
                self.extracting_zipfile = None

                if self.downloaded_file.lower().endswith('.7z'):
                    self.extracting_archive = None

                if self.install_type == 'direct_download':
                    download_dir = os.path.dirname(self.downloaded_file)
                    delete_path(download_dir)

                self.move_new_mod()

            else:
                extracting_element = self.extracting_infolist[
                    self.extracting_index]

                self.extracting_label.setText(_('Extracting {0}').format(
                    extracting_element.filename))

                if self.downloaded_file.lower().endswith('.7z'):
                    destination = os.path.join(self.extract_dir,
                        *extracting_element.filename.split('/'))
                    dest_dir = os.path.dirname(destination)
                    if not os.path.isdir(dest_dir):
                        os.makedirs(dest_dir)
                    with open(destination, 'wb') as f:
                        f.write(extracting_element.read())
                else:
                    self.extracting_zipfile.extract(extracting_element,
                        self.extract_dir)

                self.extracting_index += 1

        timer.timeout.connect(timeout)
        timer.start(0)

    def move_new_mod(self):
        self.moving_new_mod = True

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()
        status_bar.showMessage(_('Finding the mod(s)'))

        mod_dirs = self.find_mods_in_directory(self.extract_dir)

        if not mod_dirs:
            status_bar.showMessage(_('Mod installation cancelled - No mod found in the downloaded archive'))
            self.clean_up_after_install()
            return

        if self.move_mods_to_mods_dir(mod_dirs):
            status_bar.showMessage(_('Mod installation completed'))
        else:
            status_bar.showMessage(_('Mod installation cancelled - Conflict with existing mod directories'))

        self.clean_up_after_install()

    def find_mods_in_directory(self, directory):
        mod_dirs = set()
        next_scans = deque([directory])

        while next_scans:
            with os.scandir(next_scans.popleft()) as current_scan:
                for entry in current_scan:
                    if entry.is_dir():
                        next_scans.append(entry.path)
                    elif entry.is_file() and os.path.basename(entry.path).lower() == 'modinfo.json':
                        mod_dirs.add(os.path.dirname(entry.path))

        return mod_dirs

    def move_mods_to_mods_dir(self, mod_dirs):
        all_moved = True
        for mod_dir in mod_dirs:
            mod_dir_name = os.path.basename(mod_dir)
            target_dir = os.path.join(self.mods_dir, mod_dir_name)
            if os.path.exists(target_dir):
                all_moved = False
                break
            shutil.move(mod_dir, self.mods_dir)
        return all_moved

    def clean_up_after_install(self):
        delete_path(self.extract_dir)
        self.moving_new_mod = False
        self.game_dir_changed(self.game_dir)
        self.finish_install_new_mod()

    def disable_existing(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        selected_info = self.mods[selected.row()]

        if selected_info['enabled']:
            config_file = os.path.join(selected_info['path'], 'modinfo.json')
            new_config_file = os.path.join(selected_info['path'],
                'modinfo.json.disabled')
            try:
                shutil.move(config_file, new_config_file)
                selected_info['enabled'] = False
                self.mods_model.setData(selected, selected_info.get('name',
                    selected_info.get('ident', _('*Error*'))) +
                    _(' (Disabled)'))
                self.disable_existing_button.setText(_('Enable'))
            except OSError as e:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(str(e))
        else:
            config_file = os.path.join(selected_info['path'],
                'modinfo.json.disabled')
            new_config_file = os.path.join(selected_info['path'],
                'modinfo.json')
            try:
                shutil.move(config_file, new_config_file)
                selected_info['enabled'] = True
                self.mods_model.setData(selected, selected_info.get('name',
                    selected_info.get('ident', _('*Error*'))))
                self.disable_existing_button.setText(_('Disable'))
            except OSError as e:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(str(e))

    def delete_existing(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        selected_info = self.mods[selected.row()]

        confirm_msgbox = QMessageBox()
        confirm_msgbox.setWindowTitle(_('Delete mod'))
        confirm_msgbox.setText(_('This will delete the mod directory. It '
            'cannot be undone.'))
        confirm_msgbox.setInformativeText(_('Are you sure you want to '
            'delete the {view} mod?').format(view=selected_info['name']))
        confirm_msgbox.addButton(_('Delete the mod'),
            QMessageBox.YesRole)
        confirm_msgbox.addButton(_('I want to keep the mod'),
            QMessageBox.NoRole)
        confirm_msgbox.setIcon(QMessageBox.Warning)

        if confirm_msgbox.exec() == 0:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            if not delete_path(selected_info['path']):
                status_bar.showMessage(_('Mod deletion cancelled'))
            else:
                self.mods_model.removeRows(selected.row(), 1)
                self.mods.remove(selected_info)

                status_bar.showMessage(_('Mod deleted'))

    def installed_selection(self, selected, previous):
        self.installed_clicked()

    def installed_clicked(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is not None and selection_model.hasSelection():
            selected = selection_model.currentIndex()
            selected_info = self.mods[selected.row()]

            self.name_le.setText(selected_info.get('name', ''))
            self.ident_le.setText(selected_info.get('ident', ''))
            self.author_le.setText(selected_info.get('author', ''))
            if not selected_info.get('author', ''):
                authors = selected_info.get('authors', [])
                try:
                    iterable = iter(authors)
                except TypeError:
                    pass
                else:
                    authors = ', '.join(authors)
                    self.author_le.setText(authors)
            self.description_le.setPlainText(selected_info.get('description', ''))
            self.description_le.moveCursor(QTextCursor.Start)
            self.description_le.setToolTip(selected_info.get('description', ''))
            self.category_le.setText(selected_info.get('category', ''))
            self.path_label.setText(_('Path:'))
            self.path_le.setText(selected_info['path'])
            self.size_le.setText(sizeof_fmt(selected_info['size']))
            self.homepage_tb.setText('')
            if selected_info.get('version', None) is not None:
                self.version_le.setText(selected_info['version'])
            else:
                self.version_le.setText(_('Unknown'))

            if selected_info['enabled']:
                self.disable_existing_button.setText(_('Disable'))
            else:
                self.disable_existing_button.setText(_('Enable'))

        if not self.tab_disabled:
            self.disable_existing_button.setEnabled(True)
            self.delete_existing_button.setEnabled(True)
        self.install_new_button.setEnabled(False)

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

    def repository_selection(self, selected, previous):
        self.repository_clicked()

    def repository_clicked(self):
        selection_model = self.repository_lv.selectionModel()
        if not (selection_model and selection_model.hasSelection()):
            return

        selected_info = self.repo_mods[selection_model.currentIndex().row()]
        self.update_ui_with_selected_info(selected_info)
        
        self.update_install_buttons_state()
        self.clear_installed_selection()

    def update_ui_with_selected_info(self, selected_info):
        self.name_le.setText(selected_info.get('name', ''))
        self.ident_le.setText(self.format_idents(selected_info.get('ident', '')))
        self.author_le.setText(self.format_authors(selected_info))
        self.description_le.setPlainText(selected_info.get('description', ''))
        self.description_le.moveCursor(QTextCursor.Start)
        self.description_le.setToolTip(selected_info.get('description', ''))
        self.category_le.setText(selected_info.get('category', ''))
        self.version_le.setText(selected_info.get('version', _('Unknown')))

        self.update_path_and_homepage(selected_info)
        self.update_size_le(selected_info)

    def format_idents(self, idents):
        if isinstance(idents, list):
            return ', '.join(str(ident) for ident in idents)
        return str(idents) if idents else ''

    def format_authors(self, selected_info):
        authors = selected_info.get('authors', selected_info.get('author', ''))
        if isinstance(authors, list):
            return ', '.join(str(author) for author in authors)
        return str(authors) if authors else ''


    def update_path_and_homepage(self, selected_info):
        self.path_label.setText(_('Url:'))
        self.path_le.setText(selected_info['url'])
        homepage_url = html.escape(selected_info['homepage'])
        self.homepage_tb.setText(f'<a href="{homepage_url}">{homepage_url}</a>')

    def update_size_le(self, selected_info):
        if 'size' in selected_info:
            self.size_le.setText(sizeof_fmt(selected_info['size']))
        elif selected_info['type'] == 'direct_download':
            self.handle_direct_download(selected_info)
        else:
            self.size_le.setText(_('Unknown'))

    def handle_direct_download(self, selected_info):
        self.size_le.setText(_('Getting remote size'))
        if not self.is_size_query_needed(selected_info):
            return

        self.abort_existing_http_reply()
        self.http_reply_aborted = False
        self.current_repo_info = selected_info

        request = QNetworkRequest(QUrl(selected_info['url']))
        request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

        self.http_reply = self.qnam.head(request)
        self.http_reply.finished.connect(self.size_query_finished)

    def is_size_query_needed(self, selected_info):
        return not (self.current_repo_info == selected_info and 
                    self.http_reply and self.http_reply.isRunning())

    def abort_existing_http_reply(self):
        if self.http_reply and self.http_reply.isRunning():
            self.http_reply_aborted = True
            self.http_reply.abort()

    def update_install_buttons_state(self):
        if self.mods_dir and os.path.isdir(self.mods_dir) and not self.tab_disabled:
            self.install_new_button.setEnabled(True)
        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)

    def clear_installed_selection(self):
        installed_selection = self.installed_lv.selectionModel()
        if installed_selection:
            installed_selection.clearSelection()

    def size_query_finished(self):
        if (not self.http_reply_aborted
            and self.http_reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute) == 200
            and self.http_reply.hasRawHeader(b'Content-Length')):

            content_length = int(self.http_reply.rawHeader(b'Content-Length'))
            self.current_repo_info['size'] = content_length

            selection_model = self.repository_lv.selectionModel()
            if selection_model is not None and selection_model.hasSelection():
                selected = selection_model.currentIndex()
                selected_info = self.repo_mods[selected.row()]

                if selected_info is self.current_repo_info:
                    self.size_le.setText(sizeof_fmt(content_length))
        else:
            selection_model = self.repository_lv.selectionModel()
            if selection_model is not None and selection_model.hasSelection():
                selected = selection_model.currentIndex()
                selected_info = self.repo_mods[selected.row()]

                if selected_info is self.current_repo_info:
                    self.size_le.setText(_('Unknown'))

    def config_info(self, config_file):
        val = {}
        keys = ('ident', 'name', 'author', 'authors', 'description', 'category',
            'version')
        try:
            with open(config_file, 'r', encoding='utf8') as f:
                try:
                    values = json.load(f)
                    if isinstance(values, dict):
                        if values.get('type', '') == 'MOD_INFO':
                            for key in keys:
                                val[key] = values.get(key, None)
                    elif isinstance(values, list):
                        for item in values:
                            if (isinstance(item, dict)
                                and item.get('type', '') == 'MOD_INFO'):
                                    for key in keys:
                                        val[key] = item.get(key, None)
                                    break
                except ValueError:
                    pass
        except FileNotFoundError:
            return val
        return val

    def scan_size(self, mod_info):
        next_scans = deque()
        current_scan = scandir(mod_info['path'])

        total_size = 0

        while True:
            try:
                entry = next(current_scan)
                if entry.is_dir():
                    next_scans.append(entry.path)
                elif entry.is_file():
                    total_size += entry.stat().st_size
            except StopIteration:
                if len(next_scans) > 0:
                    current_scan = scandir(next_scans.popleft())
                else:
                    break

        return total_size

    def add_mod(self, mod_info):
        index = self.mods_model.rowCount()
        self.mods_model.insertRows(self.mods_model.rowCount(), 1)
        disabled_text = ''
        if not mod_info['enabled']:
            disabled_text = _(' (Disabled)')
        self.mods_model.setData(self.mods_model.index(index),
            mod_info.get('name', mod_info.get('ident', _('*Error*'))) +
            disabled_text)

    def clear_details(self):
        self.name_le.setText('')
        self.ident_le.setText('')
        self.author_le.setText('')
        self.description_le.setPlainText('')
        self.category_le.setText('')
        self.path_le.setText('')
        self.size_le.setText('')
        self.homepage_tb.setText('')
        self.version_le.setText('')

    def clear_mods(self):
        self.game_dir = None
        self.mods = []

        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)
        self.install_new_button.setEnabled(False)

        if self.mods_model is not None:
            self.mods_model.setStringList([])
        self.mods_model = None

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

        self.clear_details()

    def game_dir_changed(self, new_dir):
        self.game_dir = new_dir
        # 清空现有的模组列表
        self.mods = []
        # 更新用户界面元素
        self.update_ui_elements()

        # 构建游戏的模组目录和用户模组目录的路径
        mods_dir = os.path.join(new_dir, 'data', 'mods')
        user_mods_dir = os.path.join(new_dir, 'mods')

        if os.path.isdir(mods_dir):
            self.mods_dir = mods_dir
            self.scan_directory_for_mods(mods_dir)

        if os.path.isdir(user_mods_dir):
            self.user_mods_dir = user_mods_dir
            self.scan_directory_for_mods(user_mods_dir)

        # Sort installed mods
        self.mods.sort(key=lambda x: x['name'])
        self.update_mod_list()

    def update_ui_elements(self):
        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)
        self.install_new_button.setEnabled(False)
        self.clear_details()
        self.mods_model = QStringListModel()
        self.installed_lv.setModel(self.mods_model)
        self.installed_lv.selectionModel().currentChanged.connect(self.installed_selection)
        repository_selection = self.repository_lv.selectionModel()
        if repository_selection:
            repository_selection.clearSelection()

    def scan_directory_for_mods(self, directory):
        with os.scandir(directory) as dir_scan:
            for entry in dir_scan:
                if entry.is_dir():
                    self.process_mod_directory(entry.path)

    def process_mod_directory(self, mod_path):
        config_file = os.path.join(mod_path, 'modinfo.json')
        disabled_config_file = os.path.join(mod_path, 'modinfo.json.disabled')

        if os.path.isfile(config_file):
            self.process_mod_config_file(config_file, mod_path, enabled=True)
        elif os.path.isfile(disabled_config_file):
            self.process_mod_config_file(disabled_config_file, mod_path, enabled=False)

    def process_mod_config_file(self, config_file, mod_path, enabled):
        info = self.config_info(config_file)
        if ('ident' in info) or ('id' in info):
            mod_info = {
                'path': mod_path,
                'enabled': enabled
            }
            mod_info.update(info)
            mod_info['size'] = self.scan_size(mod_info)
            self.mods.append(mod_info)

    def update_mod_list(self):
        for mod_info in self.mods:
            self.add_mod(mod_info)
