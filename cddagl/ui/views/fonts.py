# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT
import logging
import os
import re
import json
import ctypes
import shutil

from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import (QWidget, QGridLayout, QTabWidget, QVBoxLayout, QPushButton, QLabel, QSpinBox, QRadioButton,
                             QGroupBox, QPlainTextEdit, QListView)
from cddagl.sql.functions import (
    get_config_value, set_config_value)
from cddagl.constants import get_data_path, get_cddagl_path

logger = logging.getLogger('cddagl')

ASCII_ART_0 = """   █████████             █████                       ████                                         █████     █████          
  ███░░░░░███           ░░███                       ░░███                                        ░░███     ░░███           
 ███     ░░░   ██████   ███████    ██████    ██████  ░███  █████ ████  █████  █████████████    ███████   ███████   ██████  
░███          ░░░░░███ ░░░███░    ░░░░░███  ███░░███ ░███ ░░███ ░███  ███░░  ░░███░░███░░███  ███░░███  ███░░███  ░░░░░███ 
░███           ███████   ░███      ███████ ░███ ░░░  ░███  ░███ ░███ ░░█████  ░███ ░███ ░███ ░███ ░███ ░███ ░███   ███████ 
░░███     ███ ███░░███   ░███ ███ ███░░███ ░███  ███ ░███  ░███ ░███  ░░░░███ ░███ ░███ ░███ ░███ ░███ ░███ ░███  ███░░███ 
 ░░█████████ ░░████████  ░░█████ ░░████████░░██████  █████ ░░███████  ██████  █████░███ █████░░████████░░████████░░████████
  ░░░░░░░░░   ░░░░░░░░    ░░░░░   ░░░░░░░░  ░░░░░░  ░░░░░   ░░░░░███ ░░░░░░  ░░░░░ ░░░ ░░░░░  ░░░░░░░░  ░░░░░░░░  ░░░░░░░░ 
                                                            ███ ░███                                                       
                                                           ░░██████                                                        
                                                            ░░░░░░                                                         
"""

ASCII_ART_1 = """
▓█████▄  ▒█████   ██▓     ██▓    ▄▄▄       ██▀███    ██████ 
▒██▀ ██▌▒██▒  ██▒▓██▒    ▓██▒   ▒████▄    ▓██ ▒ ██▒▒██    ▒ 
░██   █▌▒██░  ██▒▒██░    ▒██░   ▒██  ▀█▄  ▓██ ░▄█ ▒░ ▓██▄   
░▓█▄   ▌▒██   ██░▒██░    ▒██░   ░██▄▄▄▄██ ▒██▀▀█▄    ▒   ██▒
░▒████▓ ░ ████▓▒░░██████▒░██████▒▓█   ▓██▒░██▓ ▒██▒▒██████▒▒
 ▒▒▓  ▒ ░ ▒░▒░▒░ ░ ▒░▓  ░░ ▒░▓  ░▒▒   ▓▒█░░ ▒▓ ░▒▓░▒ ▒▓▒ ▒ ░
 ░ ▒  ▒   ░ ▒ ▒░ ░ ░ ▒  ░░ ░ ▒  ░ ▒   ▒▒ ░  ░▒ ░ ▒░░ ░▒  ░ ░
 ░ ░  ░ ░ ░ ░ ▒    ░ ░     ░ ░    ░   ▒     ░░   ░ ░  ░  ░  
   ░        ░ ░      ░  ░    ░  ░     ░  ░   ░           ░  
 ░                                                          
"""


class FontsTab(QTabWidget):
    def __init__(self):
        super(FontsTab, self).__init__()

        self.initialize_variables()
        # 创建主布局
        main_layout = QGridLayout()
        params = get_config_value('command.params', '').strip()
        logger.debug(params)
        # 创建QListView来实现字体选择
        self.font_list_view = QListView()
        self.font_list_view.setEditTriggers(QListView.NoEditTriggers)
        self.font_families = self.load_fonts()

        # 创建字体设置的GroupBox并添加按钮
        font_settings_groupbox = QGroupBox("字体设置")
        font_buttons_layout = QVBoxLayout()
        set_ui_font_button = QPushButton("设为UI字体")
        set_map_font_button = QPushButton("设为地图字体")
        set_large_map_font_button = QPushButton("设为大地图字体")
        set_all_button = QPushButton("设为全部")
        reset_all_font_button = QPushButton("重置全部字体")

        font_buttons_layout.addWidget(self.font_list_view)
        font_buttons_layout.addWidget(set_ui_font_button)
        font_buttons_layout.addWidget(set_map_font_button)
        font_buttons_layout.addWidget(set_large_map_font_button)
        font_buttons_layout.addWidget(set_all_button)
        font_buttons_layout.addWidget(reset_all_font_button)
        font_settings_groupbox.setLayout(font_buttons_layout)

        # 创建四个标签
        ui_font_label = QLabel("UI字体大小:")
        map_font_label = QLabel("地图字体大小:")
        large_map_font_label = QLabel("大地图字体大小:")
        font_mixture_label = QLabel("字体混合:")

        # 创建三个调节字体大小的SpinBox
        self.ui_font_size_spinbox = QSpinBox()
        self.map_font_size_spinbox = QSpinBox()
        self.large_map_font_size_spinbox = QSpinBox()

        # 初始化字体大小为14
        self.ui_font_size_spinbox.setValue(14)
        self.map_font_size_spinbox.setValue(14)
        self.large_map_font_size_spinbox.setValue(14)

        # 创建RadioButton
        self.font_mixture_radio = QRadioButton("启用")

        # 创建保存按钮
        save_button = QPushButton("保存")

        # 创建预览的GroupBox，并将QPlainTextEdit添加到其中
        preview_groupbox = QGroupBox("预览")
        preview_layout = QVBoxLayout()
        test_text_edit = QPlainTextEdit()
        test_text = """这就是一些常见的测试文本。
AB汉字1234测试cd。
Hello, World!
World, Hello!
1234567890
0987654321
!@#$%^&*()_+
+_)(*&^%$#@!
Это пример текста на кириллице.
"""
        ascii_art_edit = QPlainTextEdit()
        ascii_art = ASCII_ART_0
        ascii_art += ASCII_ART_1

        test_text_edit.setPlainText(test_text)
        test_text_edit.setReadOnly(True)
        test_text_edit.setStyleSheet("background-color: black; color: white;")
        self.test_text_edit = test_text_edit

        ascii_art_edit.setPlainText(ascii_art)
        ascii_art_edit.setReadOnly(True)
        ascii_art_edit.setStyleSheet("font-size: 5px;background-color: black; color: white;")
        self.ascii_art_edit = ascii_art_edit

        preview_layout.addWidget(test_text_edit)
        preview_layout.addWidget(ascii_art_edit)
        preview_groupbox.setLayout(preview_layout)

        # 创建目前字体和备用字体的GroupBox，并添加QPlainTextEdit
        current_font_groupbox = QGroupBox("目前字体和备用字体")
        current_font_layout = QVBoxLayout()
        current_font_text_edit = QPlainTextEdit()

        current_font_text_edit.setReadOnly(True)
        current_font_layout.addWidget(current_font_text_edit)
        current_font_groupbox.setLayout(current_font_layout)
        self.current_font_text_edit = current_font_text_edit

        # 使用QGridLayout将标签和SpinBox布局在一行
        label_spinbox_layout = QGridLayout()
        label_spinbox_layout.addWidget(ui_font_label, 0, 0)
        label_spinbox_layout.addWidget(self.ui_font_size_spinbox, 0, 1)
        label_spinbox_layout.addWidget(map_font_label, 1, 0)
        label_spinbox_layout.addWidget(self.map_font_size_spinbox, 1, 1)
        label_spinbox_layout.addWidget(large_map_font_label, 2, 0)
        label_spinbox_layout.addWidget(self.large_map_font_size_spinbox, 2, 1)
        label_spinbox_layout.addWidget(font_mixture_label, 3, 0)
        label_spinbox_layout.addWidget(self.font_mixture_radio, 3, 1)

        # 创建其他设置的GroupBox并添加标签和SpinBox的布局
        other_settings_groupbox = QGroupBox("其他设置（未实装）")
        other_settings_groupbox.setLayout(label_spinbox_layout)

        # 将字体设置的GroupBox添加到主布局
        main_layout.addWidget(font_settings_groupbox, 0, 0)  # 字体设置
        main_layout.addWidget(preview_groupbox, 0, 1)  # 预览
        main_layout.addWidget(other_settings_groupbox, 1, 1)  # 其他设置
        main_layout.addWidget(current_font_groupbox, 1, 0)  # 目前字体和备用字体

        self.setLayout(main_layout)

        # 绑定事件（预留函数）
        set_ui_font_button.clicked.connect(self.set_ui_font)
        set_map_font_button.clicked.connect(self.set_map_font)
        set_large_map_font_button.clicked.connect(self.set_large_map_font)
        set_all_button.clicked.connect(self.set_all_font)
        reset_all_font_button.clicked.connect(self.reset_all_font)
        save_button.clicked.connect(self.save_settings)
        self.font_list_view.selectionModel().currentChanged.connect(self.font_selected)

        self.load_font_settings()

    def initialize_variables(self):
        # 初始化字体大小和是否启用的变量
        self.ui_font_size = None
        self.map_font_size = None
        self.large_map_font_size = None
        self.font_mixture_enabled = False
        self.selected_font = None
        self.game_dir = None

    def load_font_settings(self):
        """
        从指定的JSON文件中加载字体设置。

        读取字体配置文件，该文件包含UI字体、地图字体和大地图字体的路径设置。配置文件位于"D:\Doiiars\Game\cataclysmdda\config\fonts.json"。
        加载配置后，更新界面上显示的当前字体信息。

        返回:
            None
        """

        # 如果仍然没有游戏路径
        if not self.game_dir:
            return

        # 配置文件路径
        font_settings_path = os.path.normpath(os.path.join(self.game_dir, "config\\fonts.json"))

        # 确保文件路径存在
        if not os.path.exists(font_settings_path):
            logger.error("字体配置文件不存在：" + font_settings_path)
            return  # 如果文件不存在，直接返回

        # 读取字体配置文件
        with open(font_settings_path, 'r', encoding='utf-8') as file:
            self.fontsjson = json.load(file)

        # 更新current_font_text_edit的文本
        self.update_current_font_text_edit()

    def update_current_font_text_edit(self):
        typeface = self.fontsjson.get("typeface", [])
        map_typeface = self.fontsjson.get("map_typeface", [])
        overmap_typeface = self.fontsjson.get("overmap_typeface", [])

        current_font_text = f"""UI： {typeface[0]} => {typeface[1] if len(typeface) > 1 else ''}
地图： {map_typeface[0]} => {map_typeface[1] if len(map_typeface) > 1 else ''}
大地图： {overmap_typeface[0]} => {overmap_typeface[1] if len(overmap_typeface) > 1 else ''}
"""
        self.current_font_text_edit.setPlainText(current_font_text)

    def load_fonts(self):
        """
        加载字体到列表
        """
        # 自定义字体目录
        font_filenames_custom = []
        if self.game_dir:
            CUSTOM_FONT_DIRECTORY = os.path.normpath(os.path.join(self.game_dir, "data", "font"))
            font_filenames_custom = load_font_filenames(CUSTOM_FONT_DIRECTORY)
            logger.debug(f'CUSTOM_FONT_DIRECTORY: {CUSTOM_FONT_DIRECTORY}')
        else:
            logger.debug("游戏目录未设置")

        # 获取系统字体目录
        system_fonts_directory = get_windows_fonts_directory()
        font_filenames_system = load_font_filenames(system_fonts_directory)

        fontnamemaps = []
        display_names = []  # 创建一个新列表来存储用于显示的字体名称
        for filename in font_filenames_custom + font_filenames_system:
            font_id = QFontDatabase.addApplicationFont(filename)
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_name = font_families[0]
            else:
                logger.error(f"无法获取字体名称： {font_families}")
                continue

            # 检查文件名是否来自 font_filenames_custom 列表
            display_name = font_name  # 储存原始的字体名称用于显示
            if filename in font_filenames_custom:
                display_name = "(游戏) " + font_name  # 给来自自定义字体列表的字体名称加上前缀
            if filename in font_filenames_system:
                display_name = "(系统) " + font_name  # 给来自系统字体列表的字体名称加上前缀
            if font_name:
                fontnamemaps.append([filename, font_name])
                display_names.append(display_name)  # 只将原始字体名称添加到显示列表中

        font_model = QStringListModel(display_names)
        self.font_list_view.setModel(font_model)
        self.font_list_view.selectionModel().currentChanged.connect(self.font_selected)

        return fontnamemaps

    def update_font_settings(self, font_key, filepath):
        """
        更新字体设置。

        根据提供的键和文件路径更新配置和字体文件。这个通用函数处理目标文件路径计算、更新配置、写入JSON、复制字体文件以及更新UI。

        参数:
            font_key (str | list): 需要更新的字体设置的键名，可以是单个键或键列表。
            filepath (str): 选定字体文件的路径。

        返回:   
            None
        """
        target_subdirectory = 'data/fonts'
        font_name = os.path.basename(filepath)
        # target_filepath = os.path.normpath(os.path.join(self.game_dir, target_subdirectory, font_name))
        target_filepath = font_name

        # 更新 fontsjson 字体部分
        if isinstance(font_key, list):
            for key in font_key:
                if isinstance(self.fontsjson[key], list):
                    # 在列表第一个位置插入新的文件路径，并保持最多两个元素
                    self.fontsjson[key].insert(0, target_filepath)
                    self.fontsjson[key] = self.fontsjson[key][:2]
                else:
                    self.fontsjson[key] = [target_filepath]  # 如果原来不是列表，直接更新为一个新列表
        else:
            if isinstance(self.fontsjson[font_key], list):
                # 在列表第一个位置插入新的文件路径，并保持最多两个元素
                self.fontsjson[font_key].insert(0, target_filepath)
                self.fontsjson[font_key] = self.fontsjson[font_key][:2]
            else:
                self.fontsjson[font_key] = [target_filepath]  # 如果原来不是列表，直接更新为一个新列表

        print(self.fontsjson)

        # # 更新命令行参数
        # params = get_config_value('command.params', '').strip()
        # userdatadir = os.path.join(self.game_dir, 'userdata')
        # params = update_userdir_param(params, userdatadir)
        # set_config_value('command.params', params)
        # self.get_main_window().central_widget.settings_tab.launcher_settings_group_box.command_line_parameters_edit.setText(params)

        # 写入JSON并复制字体文件
        __write_fonts_json_to_path(self.game_dir, self.fontsjson)
        copy_font_to_directory_by_name(self.game_dir, filepath)

        # 更新UI
        self.update_current_font_text_edit()

    def set_ui_font(self):
        """
        设为UI字体事件处理。

        当UI字体选项被触发时，调用此函数。此函数通过调用更新字体设置函数来设置UI字体。

        返回:
            None
        """
        logger.debug("触发设为UI字体事件")
        if self.selected_font is not None:
            self.update_font_settings("typeface", self.selected_fontmaps[0])

    def set_map_font(self):
        """
        设为地图字体事件处理。

        当地图字体选项被触发时，调用此函数。此函数通过调用更新字体设置函数来设置地图字体。

        返回:
            None
        """
        logger.debug("触发设为地图字体事件")
        if self.selected_font is not None:
            self.update_font_settings("map_typeface", self.selected_fontmaps[0])

    def set_large_map_font(self):
        """
        设为大地图字体事件处理。

        当大地图字体选项被触发时，调用此函数。此函数通过调用更新字体设置函数来设置大地图字体。

        返回:
            None
        """
        logger.debug("触发设为大地图字体事件")
        if self.selected_font is not None:
            self.update_font_settings("overmap_typeface", self.selected_fontmaps[0])

    def set_all_font(self):
        """
        设为全部字体事件处理。

        当全部字体选项被触发时，调用此函数。此函数通过调用更新字体设置函数来同时设置UI字体、地图字体及大地图字体。

        返回:
            None
        """
        logger.debug("触发设为全部字体事件")
        if self.selected_font is not None:
            self.update_font_settings(["typeface", "map_typeface", "overmap_typeface"], self.selected_fontmaps[0])

    def reset_all_font(self):
        """
        重置全部字体事件处理。

        当需要重置所有字体设置时，调用此函数。此函数通过重新加载字体设置来实现重置。

        返回:
            None
        """
        logger.debug("触发重置全部字体事件")
        self.load_font_settings()

    def save_settings(self):
        logger.debug("触发保存设置事件")
        # 将字体大小和是否启用的变量存储在这里
        self.ui_font_size = self.ui_font_size_spinbox.value()
        self.map_font_size = self.map_font_size_spinbox.value()
        self.large_map_font_size = self.large_map_font_size_spinbox.value()
        self.font_mixture_enabled = self.font_mixture_radio.isChecked()

    def font_selected(self, index):
        logger.debug("触发字体选择变化事件")
        # 处理字体选择变化事件
        self.selected_fontmaps = self.font_families[index.row()]
        self.selected_font = self.selected_fontmaps[1]
        logger.debug(f"选择了字体：{self.selected_font}")

        # 设置test_text_edit的字体
        font_style = f'font-family: "{self.selected_font}"; font-size: 32px; background-color: black; color: white; '
        ascii_font_style = f'font-family: "{self.selected_font}"; font-size: 6px; background-color: black; color: white; '
        logger.debug(f"font_style: {font_style}")

        self.test_text_edit.setStyleSheet(font_style)
        self.ascii_art_edit.setStyleSheet(ascii_font_style)

        # todo

    def game_dir_changed(self, new_dir):
        logger.debug("触发游戏目录改变事件")
        # todo
        # 设置游戏目录为新的目录
        self.game_dir = new_dir
        # 清空现有的模组列表

        # 构建游戏的模组目录和用户模组目录的路径
        fonts_dir = os.path.join(new_dir, 'data', 'font')
        user_fonts_dir = os.path.join(new_dir, 'font')

        self.font_families = self.load_fonts()
        self.load_font_settings()  # 重新加载字体配置

    def load_repository(self):
        """加载字体库。"""
        self.repo_fonts = []  # 使用 repo_fonts 替换 repo_mods 以反映内容的改变

        yaml_file = get_data_path('fonts.yaml')  # 修改文件名为 fonts.yaml

        if os.path.isfile(yaml_file):  # 检查文件是否存在
            with open(yaml_file, 'r', encoding='utf8') as f:  # 打开YAML文件
                try:
                    values = yaml.safe_load(f)  # 解析YAML文件
                    print(values)
                except yaml.YAMLError:  # 处理YAML解析错误
                    pass

    def install_new(self):
        """
        安装选中的字体。

        此方法从用户界面选择的字体库中获取选中的字体信息，并进行下载与安装。
        如果字体已存在，会首先确认是否继续安装。
        下载过程中，状态栏会显示下载进度和相关信息。

        Raises:
            HTTPError: 如果下载过程中遇到网络错误。
        """
        if not self.installing_new_font:
            selection_model = self.repository_lv.selectionModel()
            if selection_model is None or not selection_model.hasSelection():
                return

            selected = selection_model.currentIndex()
            selected_info = self.repo_fonts[selected.row()]

            font_idents = selected_info['ident']
            if isinstance(font_idents, list):
                font_idents = set(font_idents)
            else:
                font_idents = set((font_idents,))

            self.check_and_confirm_font_installation(font_idents, selected_info)

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            self.install_type = selected_info['type']

            if selected_info['type'] == 'direct_download':
                if self.http_reply is not None and self.http_reply.isRunning():
                    self.http_reply_aborted = True
                    self.http_reply.abort()

                self.installing_new_font = True
                self.download_aborted = False

                download_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)
                self.download_dir = download_dir

                download_url = selected_info['url']

                url = QUrl(download_url)
                file_info = QFileInfo(url.path())
                file_name = file_info.fileName()
                self.downloaded_file = os.path.join(self.download_dir, file_name)
                self.download_first_ready = True
                self.downloading_file = None

                status_bar.clearMessage()
                status_bar.busy += 1

                downloading_label = QLabel()
                downloading_label.setText(_('Downloading: {0}').format(selected_info['url']))
                status_bar.addWidget(downloading_label, 100)
                self.downloading_label = downloading_label

                downloading_speed_label = QLabel()
                status_bar.addWidget(downloading_speed_label)
                self.downloading_speed_label = downloading_speed_label

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

                self.downloading_new_font = True

                request = QNetworkRequest(QUrl(url))
                request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(self.download_http_finished)
                self.download_http_reply.readyRead.connect(self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(self.download_dl_progress)

                self.cancel_installation()

    def cancel_installation(self):
        self.install_new_button.setText(_('Cancel font installation'))
        self.installed_lv.setEnabled(False)
        self.repository_lv.setEnabled(False)

        self.get_main_tab().disable_tab()
        self.get_soundpacks_tab().disable_tab()
        self.get_settings_tab().disable_tab()
        self.get_backups_tab().disable_tab()

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


def load_font_filenames(directory):
    try:
        # 获取目录中所有文件的文件名
        filenames = os.listdir(directory)

        # 只选择特定类型的字体文件（比如.ttf或.otf），并且兼顾大小写
        font_filenames = [os.path.join(directory, filename) for filename in filenames if
                          filename.lower().endswith(('.ttf', '.otf', '.ttc'))]

        return font_filenames
    except Exception as e:
        logger.error(f"加载字体文件失败: {e}")
        return []


# 加载字体
def load_font(font_path):
    try:
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            return QFont(font_families[0])
    except Exception as e:
        logger.error(f"加载字体失败 '{font_path}': {e}")
    return None


def __write_fonts_json_to_path(dirpath, data, subpath='config'):
    try:
        # 检查路径是否存在，如果不存在则创建它
        if not os.path.exists(subpath):
            os.makedirs(subpath)

        # 构建JSON文件的完整路径
        json_path = os.path.join(dirpath, subpath, 'fonts.json')

        # 手动构造带有换行的JSON字符串
        formatted_json = json.dumps(data, indent=4)
        formatted_json = formatted_json.replace('],', '],\n').replace('[', '[\n    ').replace(']', '\n  ]')

        # 写入JSON数据到文件
        with open(json_path, 'w') as json_file:
            json_file.write(formatted_json)

        print(f"JSON数据已成功写入到路径: {json_path}")
    except Exception as e:
        print(f"写入JSON数据时出错: {str(e)}")


def copy_font_to_directory_by_name(taget_path, font_path, target_subdirectory='data/font'):
    # 目标目录
    target_directory = os.path.join(taget_path, target_subdirectory)

    # 从font_path中提取文件名
    font_name = os.path.basename(font_path)

    # 使用文件名构建目标字体路径
    target_font_path = os.path.join(target_directory, font_name)

    # 检查目标目录是否已存在字体文件
    if os.path.exists(target_font_path):
        print(f"字体 '{font_name}' 已存在于目标目录中.")
        return

    # 确保目标目录存在
    os.makedirs(target_directory, exist_ok=True)

    try:
        # 复制字体文件到目标目录
        shutil.copy(font_path, target_font_path)
        print(f"字体 '{font_name}' 已成功复制到目标目录.")
    except Exception as e:
        print(f"复制字体 '{font_name}' 到目标目录时发生错误: {str(e)}")


def get_windows_fonts_directory():
    # 获取系统文件夹路径
    windir = os.environ.get('WINDIR', 'C:\\Windows')

    fonts_directory = os.path.join(windir, 'Fonts')

    return fonts_directory

# def update_userdir_param(params, userdir_path):
#     """
#     替换或添加`--userdir`参数到给定的命令行参数字符串中。

#     如果`params`字符串中已存在`--userdir`参数，则替换其路径；
#     否则，向`params`添加`--userdir`参数和指定的路径。

#     参数:
#     - params: 原始的命令行参数字符串。
#     - userdir_path: 要设置的`--userdir`参数的路径。

#     返回:
#     - 更新后的命令行参数字符串。
#     """
#     # 将路径中的反斜杠转义，以避免正则表达式解析错误
#     safe_userdir_path = userdir_path.replace('\\', '\\\\')

#     # 构建正则表达式以匹配--userdir参数
#     userdir_pattern = re.compile(r'--userdir\s+"[^"]*"')

#     # 检查params中是否已存在--userdir参数
#     match = userdir_pattern.search(params)
#     if match:
#         # 如果已存在，替换其路径
#         params = userdir_pattern.sub(f'--userdir "{safe_userdir_path}"', params)
#     else:
#         # 如果不存在，添加参数
#         if params:
#             params += ' '
#         params += f'--userdir "{safe_userdir_path}"'
#     return params
