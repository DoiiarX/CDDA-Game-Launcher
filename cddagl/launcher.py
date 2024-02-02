# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT
# -*- coding: utf-8 -*-

import logging
import os
import sys
import traceback
from io import StringIO
from logging.handlers import RotatingFileHandler

import markdown2

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from babel.core import Locale
try:
    # new location for sip
    # https://www.riverbankcomputing.com/static/Docs/PyQt5/incompatibilities.html#pyqt-v5-11
    from PyQt5 import sip
except ImportError:
    import sip

### to avoid import errors when not setting PYTHONPATH
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.constants import get_cddagl_path, get_locale_path, get_resource_path
from cddagl.i18n import (
    load_gettext_locale, load_gettext_no_locale,
    proxy_gettext as _, get_available_locales
)
from cddagl.sql.functions import init_config, get_config_value, config_true
from cddagl.ui.views.dialogs import ExceptionWindow
from cddagl.ui.views.tabbed import TabbedWindow
from cddagl.win32 import get_ui_locale, SingleInstance, write_named_pipe

logger = logging.getLogger('cddagl')


def init_single_instance():
    if not config_true(get_config_value('allow_multiple_instances', 'False')):
        single_instance = SingleInstance()

        if single_instance.aleradyrunning():
            write_named_pipe('cddagl_instance', b'dupe')
            sys.exit(0)

        return single_instance

    return None


def get_preferred_locale(available_locales):
    preferred_locales = []

    selected_locale = get_config_value('locale', None)
    if selected_locale == 'None':
        selected_locale = None
    if selected_locale is not None:
        preferred_locales.append(selected_locale)

    system_locale = get_ui_locale()
    if system_locale is not None:
        preferred_locales.append(system_locale)

    app_locale = Locale.negotiate(preferred_locales, available_locales)
    if app_locale is None:
        app_locale = 'en'
    else:
        app_locale = str(app_locale)

    return app_locale


def init_logging():
    # get root logger
    logger = logging.getLogger('cddagl')
    logger.setLevel(logging.DEBUG)

    # setup directory for written-to-file logs
    local_app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
    if local_app_data is None or not os.path.isdir(local_app_data):
        local_app_data = ''

    logging_dir = os.path.join(local_app_data, 'CDDA Game Launcher')
    if not os.path.isdir(logging_dir):
        os.makedirs(logging_dir)

    logging_file = os.path.join(logging_dir, 'app.log')

    # setup logging formatter
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

    # setup file logger
    file_handler = RotatingFileHandler(
        logging_file, encoding='utf8',
        maxBytes=cons.MAX_LOG_SIZE, backupCount=cons.MAX_LOG_FILES
    )
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # setup consoler logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # initialize
    logger.info(_('CDDA Game Launcher started: {version}').format(version=version))


def handle_exception(extype, value, tb):
    logger = logging.getLogger('cddagl')

    tb_io = StringIO()
    traceback.print_tb(tb, file=tb_io)

    logger.critical(
        _('Global error:\n'
          'Launcher version: {version}\n'
          'Type: {extype}\n'
          'Value: {value}\n'
          'Traceback:\n{traceback}')
        .format(version=version, extype=str(extype), value=str(value),traceback=tb_io.getvalue())
    )
    ui_exception(extype, value, tb)


def start_ui(locale, single_instance):
    load_gettext_locale(get_locale_path(), locale)

    main_app = QApplication(sys.argv)
    
    main_app.setStyleSheet("""
        /* QWidget通用样式 */
        QToolTip {
            font-size: 20px;
            border-radius: 5px;
            padding: 5px;
            background-color: #ffffe0; /* 更柔和的黄色背景 */
            color: #000000;
            border: 1px solid #dcdcdc; /* 更细微的边框颜色 */
        }

        QWidget {
            background-color: #ffffff;
            color: #2c3e50;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            font-size: 14px;
        }

        QLineEdit, QTextEdit {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            min-height: 21px;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            vertical-align: middle; /* 将文字垂直居中 */
        }
        
        QPlainTextEdit {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            min-height: 21px;
            font-size: 20px;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
        }
        
        QProgressBar {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px;
            min-height: 14px;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            vertical-align: middle; /* 将文字垂直居中 */
            text-align: center; /* 将文字水平居中 */
        }

        QPushButton {
            background-color: #3498db;
            color: #ffffff;
            font-size: 15px;
            height: 20px;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            vertical-align: middle; /* 将文字垂直居中 */
            border-radius: 5px;
            padding: 10px 20px;
            margin: 0px 10px;
            outline: none;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #1f618d;
        }

        QLabel {
            font-size: 15px;
            margin-bottom: 5px;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            vertical-align: middle; /* 将文字垂直居中 */
        }

        QListView {
            background-color: #fff;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            min-height: 40px;
        }

        QListView::item {
            background-color: #ecf0f1;
            padding: 5px;
            color: #2c3e50;
        }

        QListView::item:selected {
            background-color: #3498db;
            color: #ffffff;
        }

        QListView::item:selected:!active {
            background-color: #ecf0f1;
            color: #2c3e50;
        }

        QListView::item:hover {
            background-color: #3498db;
            color: #ffffff;
        }
        
        /* 其他控件样式 */
        QVBoxLayout, QHBoxLayout {
        /* border: 1px solid #bdc3c7;*/
            margin-top: 1em;
        }
        
        QGroupBox {
            font-size: 24px; /* 设置更大的字体大小 */
            font-weight: bold; /* 设置字体加粗 */
            border: none;
            margin-top: 1em;
        }

        QGroupBox::title {
            font-size: 24px; /* 设置更大的字体大小 */
            font-weight: bold; /* 设置字体加粗 */
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }

        QRadioButton, QButtonGroup {
            font-size: 14px;
            color: #2c3e50;
        }

        QComboBox {
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 5px 10px;
            min-height: 21px;
            background-color: #ecf0f1;
            color: #2c3e50;
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            font-size: 14px;
        }

        QComboBox:hover {
            border-color: #3498db;
        }

        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left-width: 1px;
            border-left-color: #bdc3c7;
            border-left-style: solid;
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
        }

        QComboBox::down-arrow {
            width: 0px;
            height: 0px;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 12px solid #2c3e50; /* 使用深色作为箭头颜色 */
        }

        QComboBox QAbstractItemView {
            border: 1px solid #bdc3c7;
            selection-background-color: #3498db;
            selection-color: #ffffff;
            background-color: #ffffff;
            padding: 4px;
        }

        QComboBox::drop-down:hover {
            background-color: #e0e0e0;
        }
        
        QFileDialog, QMessageBox {
            /* 这些对话框通常已经有良好的默认样式，除非需要特别定制 */
        }

        QToolButton {
            background-color: #ecf0f1;
            border-radius: 3px;
        }

        QToolButton:hover, QToolButton:pressed {
            background-color: #bdc3c7;
        }

        QScrollBar:vertical {
            border: none;
            background-color: #ecf0f1;
            width: 10px;
            margin: 15px 0 15px 0;
        }

        QScrollBar::handle:vertical {
            background-color: #bdc3c7;
            min-height: 20px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background-color: #3498db;
            height: 15px;
            subcontrol-position: top;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            border: none;
            background-color: #ecf0f1;
            margin: 0 15px 0 15px;
        }

        QScrollBar::handle:horizontal {
            background-color: #bdc3c7;
            min-width: 20px; /* 设置最小宽度 */
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            background-color: #3498db;
            width: 15px; /* 设置宽度 */
            subcontrol-position: left; /* 对于水平滚动条，应该是left和right */
        }

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }

        
        /* QMainWindow样式 */
        QMainWindow {
            background-color: #f0f0f0;
        }

        /* QAction样式 */
        QAction {
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            color: #2c3e50;
        }

        /* QDialog样式 */
        QDialog {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
        }

        /* QTabWidget样式 */
        QTabWidget::pane {
            border-top: 2px solid #3498db;
        }

        QTabWidget::tab-bar {
            left: 5px;
        }

        QTabBar::tab {
            background: #ecf0f1;
            padding: 10px;
        }

        QTabBar::tab:selected {
            background: #3498db;
            color: #ffffff;
        }

        QTabBar::tab:!selected {
            color: #2c3e50;
        }

        /* QCheckBox基本样式 */
        QCheckBox {
            spacing: 5px; /* 文本与复选框之间的距离 */
        }

        /* QCheckBox指示器（复选框本身）的大小 */
        QCheckBox::indicator {
            width: 13px;
            height: 13px;
        }

        /* QCheckBox选中时的样式 */
        QCheckBox::indicator:checked {
            background-color: #3498db; /* 选中时的背景颜色 */
            border: 1px solid #2980b9; /* 选中时的边框颜色 */
        }

        /* QCheckBox未选中时的样式 */
        QCheckBox::indicator:unchecked {
            background-color: #ffffff; /* 未选中时的背景颜色 */
            border: 1px solid #bdc3c7; /* 未选中时的边框颜色 */
        }

        /* QMenu样式 */
        QMenu {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
        }

        QMenu::item {
            padding: 5px 30px 5px 30px;
        }

        QMenu::item:selected {
            background-color: #3498db;
            color: #ffffff;
        }

        """)
    
    main_app.setWindowIcon(QIcon(get_resource_path('launcher.ico')))

    main_app.single_instance = single_instance
    main_app.app_locale = locale

    main_win = TabbedWindow('CDDA Game Launcher')
    main_win.show()

    main_app.main_win = main_win

    sys.exit(main_app.exec_())


def ui_exception(extype, value, tb):
    main_app = QApplication.instance()

    if main_app is not None:
        main_app_still_up = True
        main_app.closeAllWindows()
    else:
        main_app_still_up = False
        main_app = QApplication(sys.argv)

    ex_win = ExceptionWindow(main_app, extype, value, tb)
    ex_win.show()
    main_app.ex_win = ex_win

    if not main_app_still_up:
        sys.exit(main_app.exec_())


def init_exception_catcher():
    sys.excepthook = handle_exception


def run_cddagl():
    load_gettext_no_locale()
    init_logging()
    init_exception_catcher()

    init_config(get_cddagl_path())

    start_ui(get_preferred_locale(get_available_locales(get_locale_path())),
             init_single_instance())


if __name__ == '__main__':
    run_cddagl()
