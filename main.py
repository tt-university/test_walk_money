import sys
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (QApplication, QFormLayout, QHeaderView,
                               QHBoxLayout, QLineEdit, QMainWindow,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QDialog, QMessageBox)
from PySide6.QtCharts import QChartView, QPieSeries, QChart

import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("walkmonye-firebase-adminsdk-8pm1s-efacc099d8.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://walkmonye-default-rtdb.europe-west1.firebasedatabase.app/'
})


def error_logging_in(text):
    error = QMessageBox()
    error.setWindowTitle("Что-то пошло не так")
    error.setText(text)
    error.setIcon(QMessageBox.Warning)
    error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

    error.exec_()


class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Регистрация / Авторизация')

        self.data_base = db.reference('users').get()
        self.user = ''

        self.user_name = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton('Войти', self)
        self.register_button = QPushButton('Регистрация', self)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow('Имя пользователя:', self.user_name)
        form_layout.addRow('Пароль:', self.password)
        layout.addLayout(form_layout)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

    def login(self):
        name_user = self.user_name.text()
        password = self.password.text()

        if not name_user and not password:
            error_logging_in("Нужно ввести данные!")
        elif not name_user:
            error_logging_in("Нужно ввести имя!")
        elif not password:
            error_logging_in("Отсутствует пароль!")
        elif name_user not in self.data_base.keys():
            error_logging_in("Такого пользователя не существует")
        elif password != self.data_base.get(name_user).get('password'):
            error_logging_in("Неправильный пароль")
        else:
            self.user = name_user
            self.accept()

    def register(self):
        name_user = self.user_name.text()
        password = self.password.text()

        if not name_user and not password:
            error_logging_in("Нужно ввести данные!")
        elif not name_user:
            error_logging_in("Нужно ввести имя!")
        elif not password:
            error_logging_in("Отсутствует пароль!")
        elif name_user in self.data_base.keys():
            error_logging_in("Пользователь с таким ником уже существует")
        else:
            print("Уже норм")
            self.user = name_user
            db.reference('users/'+name_user).set({
                'password': password,
                'data': None,
            })
            print(db.reference('users').get())
            self.accept()


class Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.items = 0

        self._user = ''
        self._data = {}

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Description", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        self.description = QLineEdit()
        self.description.setClearButtonEnabled(True)
        self.price = QLineEdit()
        self.price.setClearButtonEnabled(True)

        self.add = QPushButton("Add")
        self.clear = QPushButton("Clear")
        self.plot = QPushButton("Plot")

        self.add.setEnabled(False)

        form_layout = QFormLayout()
        form_layout.addRow("Description", self.description)
        form_layout.addRow("Price", self.price)
        self.right = QVBoxLayout()
        self.right.addLayout(form_layout)
        self.right.addWidget(self.add)
        self.right.addWidget(self.plot)
        self.right.addWidget(self.chart_view)
        self.right.addWidget(self.clear)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.table)
        self.layout.addLayout(self.right)

        self.add.clicked.connect(self.add_element)
        self.plot.clicked.connect(self.plot_data)
        self.clear.clicked.connect(self.clear_table)
        self.description.textChanged.connect(self.check_disable)
        self.price.textChanged.connect(self.check_disable)

        self.fill_table()

    @Slot()
    def add_element(self):
        des = self.description.text()
        price = float(self.price.text())

        db.reference(f'users/{self._user}/data/{des}').set(price)

        self.table.insertRow(self.items)
        description_item = QTableWidgetItem(des)
        price_item = QTableWidgetItem(f"{price:.2f}")
        price_item.setTextAlignment(Qt.AlignRight)

        self.table.setItem(self.items, 0, description_item)
        self.table.setItem(self.items, 1, price_item)

        self.description.clear()
        self.price.clear()

        self.items += 1

    @Slot()
    def check_disable(self, s):
        enabled = bool(self.description.text() and self.price.text())
        self.add.setEnabled(enabled)

    @Slot()
    def plot_data(self):
        series = QPieSeries()
        for i in range(self.table.rowCount()):
            text = self.table.item(i, 0).text()
            number = float(self.table.item(i, 1).text())
            series.append(text, number)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignLeft)
        self.chart_view.setChart(chart)

    def fill_table(self, data=None):
        data = self._data if not data else data
        for desc, price in data.items():
            description_item = QTableWidgetItem(desc)
            price_item = QTableWidgetItem(f"{price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight)
            self.table.insertRow(self.items)
            self.table.setItem(self.items, 0, description_item)
            self.table.setItem(self.items, 1, price_item)
            self.items += 1

    @Slot()
    def clear_table(self):
        self.table.setRowCount(0)
        self.items = 0

    def show_auth_dialog(self):
        dialog = AuthDialog(self)
        if dialog.exec_():
            self._user = dialog.user
            data = db.reference(f'users/{self._user}/data').get()
            self._data = data if data else {}
            self.fill_table()


class MainWindow(QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setWindowTitle("Tutorial")

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")

        # Exit QAction
        exit_action = self.file_menu.addAction("Exit", self.close)
        exit_action.setShortcut("Ctrl+Q")

        self.setCentralWidget(widget)
        widget.show_auth_dialog()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    window = MainWindow(widget)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
