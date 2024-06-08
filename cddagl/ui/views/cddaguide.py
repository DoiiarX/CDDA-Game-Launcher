# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import logging
import sys

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout

logger = logging.getLogger('cddagl')


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, browser, parent=None):
        super(CustomWebEnginePage, self).__init__(parent)
        self.browser = browser

    def createRequest(self, _type, request):
        # 修改请求头
        request.setHeader("Referer", "cddagl")
        return super().createRequest(_type, request)


class CDDAGuideTab(QTabWidget):
    def __init__(self):
        super(CDDAGuideTab, self).__init__()

        # 创建浏览器视图
        self.browser = QWebEngineView(self)
        self.browser.setPage(CustomWebEnginePage(self.browser))

        try:
            # 设置初始页面
            self.browser.setUrl(QUrl("https://cdda.doiiars.com/?lang=zh_CN"))

            # 设置用户代理
            user_agent = "cddagl"  # 你可以设置自己的用户代理字符串
            self.browser.page().profile().setHttpUserAgent(user_agent)

            settings = self.browser.settings()
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
            settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

            # 创建布局并将浏览器视图添加到布局中
            layout = QVBoxLayout()
            layout.addWidget(self.browser)

            self.setLayout(layout)
        except Exception as e:
            logger.error(f'An error occurred: {str(e)}')

    def keyPressEvent(self, event):
        # 获取按键和修饰符
        key = event.key()
        modifiers = event.modifiers()

        # 将修饰符和按键转换为可读的字符串
        modifier_keys = []
        if modifiers & Qt.ShiftModifier:
            modifier_keys.append("Shift")
        if modifiers & Qt.ControlModifier:
            modifier_keys.append("Ctrl")
        if modifiers & Qt.AltModifier:
            modifier_keys.append("Alt")
        if modifiers & Qt.MetaModifier:
            modifier_keys.append("Meta")

        try:
            key_hex = hex(key)  # 将按键的键代码转换为十六进制字符串
            logger.debug(f"Pressed key: {'+'.join(modifier_keys)}+{key_hex}")
        except Exception as e:
            logger.debug(f"An error occurred while processing key press: {str(e)}")

        # 检查是否是后退或前进快捷键
        if modifiers == Qt.AltModifier and key == Qt.Key_Left:
            self.go_back()
        elif modifiers == Qt.AltModifier and key == Qt.Key_Right:
            self.go_forward()
        elif key == Qt.Key_Left:
            self.go_back()
        elif key == Qt.Key_Right:
            self.go_forward()
        else:
            super().keyPressEvent(event)

    def go_back(self):
        if self.browser.page().action(QWebEnginePage.Back).isEnabled():
            self.browser.back()

    def go_forward(self):
        if self.browser.page().action(QWebEnginePage.Forward).isEnabled():
            self.browser.forward()

    def set_text(self):
        pass

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = QMainWindow()
    tab = CDDAGuideTab()
    mainWin.setCentralWidget(tab)
    mainWin.show()
    sys.exit(app.exec_())
