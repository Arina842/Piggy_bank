import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QWidget
from PyQt5.QtGui import QBrush, QColor
import pandas as pd
from datetime import datetime
from PyQt5 import QtCore
import os

class PiggyBank(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("piggy_bank.ui", self)
        self.setWindowTitle("Виртуальная Копилка")
        self.balance = 0
        self.history_file = 'piggy_bank_history.xlsx'
        self.goal = 0
        self.load_history()
        self.update_balance_label()
        self.update_goal_label()

        self.deposit_button.clicked.connect(self.deposit)
        self.withdraw_button.clicked.connect(self.withdraw)
        self.view_history_button.clicked.connect(self.view_history)
        self.set_goal_button.clicked.connect(self.set_goal)
        self.clear_history_button.clicked.connect(self.clear_history)

        # Настройка layout
        self.setup_layout()

    def setup_layout(self):
         # Создаем основной виджет для centralwidget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Layout для balance, goal, progress, remaining labels
        info_layout = QVBoxLayout()
        info_layout.addWidget(self.balance_label)
        info_layout.addWidget(self.goal_label)
        info_layout.addWidget(self.progress_label)
        info_layout.addWidget(self.remaining_months_label)
        main_layout.addLayout(info_layout)

        # Layout для input и кнопок deposit, withdraw
        input_button_layout = QHBoxLayout()
        input_button_layout.addWidget(self.amount_input)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.deposit_button)
        button_layout.addWidget(self.withdraw_button)
        input_button_layout.addLayout(button_layout)
        main_layout.addLayout(input_button_layout)

        # Кнопки view history, set goal, clear history
        main_layout.addWidget(self.view_history_button)
        main_layout.addWidget(self.set_goal_button)
        main_layout.addWidget(self.clear_history_button)

         # Устанавливаем layout для centralwidget
        self.setCentralWidget(central_widget)


    def load_history(self):
        try:
            self.df_history = pd.read_excel(self.history_file)
            if not self.df_history.empty:
                self.balance = self.df_history['Баланс'].iloc[-1]
                if 'Цель' in self.df_history.columns:
                    self.goal = self.df_history['Цель'].iloc[-1]
        except FileNotFoundError:
            print("Файл истории не найден, создаю новый")
            self.df_history = pd.DataFrame(columns=['Дата', 'Тип', 'Сумма', 'Баланс', 'Прогресс', 'Цель'])
            self.df_history['Дата'] = pd.to_datetime(self.df_history['Дата'])
            self.df_history['Тип'] = self.df_history['Тип'].astype(str)
            self.df_history['Сумма'] = self.df_history['Сумма'].astype(float)
            self.df_history['Баланс'] = self.df_history['Баланс'].astype(float)
            self.df_history['Прогресс'] = self.df_history['Прогресс'].astype(str)
            self.df_history['Цель'] = self.df_history['Цель'].astype(float)

    def save_history(self):
        try:
            self.df_history.to_excel(self.history_file, index=False)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка сохранения", f"Не удалось сохранить историю: {e}")

    def save_goal(self):
            if not self.df_history.empty:
                new_goal =  pd.DataFrame([{'Дата': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Тип':'Установка цели','Сумма':0, 'Баланс':self.balance,'Прогресс':f"{((self.balance/self.goal) *100) if self.goal >0 else 0:.2f}%", 'Цель': self.goal}])
                self.df_history = pd.concat([self.df_history, new_goal], ignore_index = True)
            else:
                self.df_history = pd.DataFrame([{'Дата': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Тип':'Установка цели','Сумма':0, 'Баланс':self.balance,'Прогресс':f"{((self.balance/self.goal) *100) if self.goal >0 else 0:.2f}%", 'Цель': self.goal}])
            self.save_history()

    def update_balance_label(self):
       self.balance_label.setText(f"Баланс: {self.balance:.2f}")
       self.update_progress_labels()

    def update_goal_label(self):
        self.goal_label.setText(f"Цель: {self.goal:.2f}")
        self.update_progress_labels()

    def update_progress_labels(self):
         if self.goal > 0:
            progress_percent = (self.balance / self.goal) * 100
            progress_percent = min(progress_percent, 100)

            self.progress_label.setText(f"Прогресс: {progress_percent:.2f}%")

            # Расчет месяцев до достижения цели
            if not self.df_history.empty:
               monthly_changes = self.calculate_monthly_changes()
               if monthly_changes != 0 :
                  remaining_months = (self.goal-self.balance) / monthly_changes
                  remaining_months = max(remaining_months, 0)
                  self.remaining_months_label.setText(f"Осталось месяцев: {remaining_months:.2f}")
               else:
                 self.remaining_months_label.setText("Недостаточно данных для расчета")
            else:
                 self.remaining_months_label.setText("Недостаточно данных для расчета")
         else:
            self.progress_label.setText("Установите цель")
            self.remaining_months_label.setText("Установите цель")

    def calculate_monthly_changes(self):
        if self.df_history.empty or len(self.df_history) < 2:
              return 0
        try:
            self.df_history['Дата'] = pd.to_datetime(self.df_history['Дата'])
            self.df_history['Month'] = self.df_history['Дата'].dt.to_period('M')
            monthly_balance = self.df_history.groupby('Month')['Баланс'].diff().dropna()
            if monthly_balance.empty:
                return 0
            return monthly_balance.mean()
        except Exception as e:
                QMessageBox.warning(self, "Ошибка расчета", f"Произошла ошибка при рассчете месячных изменений: {e}")
                return 0

    def deposit(self):
        amount_str = self.amount_input.text()
        try:
            amount = float(amount_str)
            if amount <= 0:
                QMessageBox.warning(self, "Ошибка ввода", "Сумма должна быть положительным числом.")
                return
            self.balance += amount
            self.add_to_history('Пополнение', amount)
            self.update_balance_label()
            QMessageBox.information(self, "Успех", f"Пополнено на {amount:.2f}")
            self.amount_input.clear()
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Введите корректную сумму.")

    def withdraw(self):
        amount_str = self.amount_input.text()
        try:
            amount = float(amount_str)
            if amount <= 0:
                QMessageBox.warning(self, "Ошибка ввода", "Сумма должна быть положительным числом.")
                return
            if amount > self.balance:
                QMessageBox.warning(self, "Ошибка", "Недостаточно средств на балансе.")
                return
            self.balance -= amount
            self.add_to_history('Снятие', amount)
            self.update_balance_label()
            QMessageBox.information(self, "Успех", f"Снято {amount:.2f}")
            self.amount_input.clear()
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Введите корректную сумму.")

    def add_to_history(self, operation_type, amount):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress = f"{((self.balance/self.goal) *100) if self.goal >0 else 0:.2f}%"
        new_row = {'Дата': now, 'Тип': operation_type, 'Сумма': amount, 'Баланс': self.balance, 'Прогресс': progress, 'Цель': self.goal}
        try:
            self.df_history = pd.concat([self.df_history, pd.DataFrame([new_row])], ignore_index=True)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка добавления истории", f"Не удалось добавить историю: {e}")

        self.save_history()

    def view_history(self):
        try:
            if self.df_history.empty:
                QMessageBox.information(self, "История", "История операций пуста.")
                return

            # Open excel file
            if os.path.exists(self.history_file):
                os.startfile(self.history_file)
            else:
                QMessageBox.warning(self, "Ошибка", f"Файл истории '{self.history_file}' не найден")

            history_window = QtWidgets.QDialog(self)
            history_window.setWindowTitle("История операций")
            layout = QtWidgets.QVBoxLayout(history_window)
            table_view = QtWidgets.QTableView(history_window)
            model = PandasModel(self.df_history)
            table_view.setModel(model)

            layout.addWidget(table_view)
            history_window.setLayout(layout)
            history_window.setMinimumSize(700, 400)
            history_window.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Произошла ошибка при открытии истории {e}")

    def set_goal(self):
        dialog = SetGoalDialog(self, self.goal)
        if dialog.exec_() == QDialog.Accepted:
            self.goal = dialog.get_goal()
            self.save_goal()
            self.update_goal_label()

    def clear_history(self):
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите стереть историю операций?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.df_history = pd.DataFrame(columns=['Дата', 'Тип', 'Сумма', 'Баланс', 'Прогресс', 'Цель'])
                self.df_history['Дата'] = pd.to_datetime(self.df_history['Дата'])
                self.df_history['Тип'] = self.df_history['Тип'].astype(str)
                self.df_history['Сумма'] = self.df_history['Сумма'].astype(float)
                self.df_history['Баланс'] = self.df_history['Баланс'].astype(float)
                self.df_history['Прогресс'] = self.df_history['Прогресс'].astype(str)
                self.df_history['Цель'] = self.df_history['Цель'].astype(float)
                self.balance = 0
                self.save_history()
                self.update_balance_label()
                QMessageBox.information(self, "Успех", "История операций удалена.")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка очистки", f"Не удалось удалить историю: {e}")

class SetGoalDialog(QDialog):
   def __init__(self, parent = None, current_goal = 0):
    super().__init__(parent)
    self.setWindowTitle("Установка цели")
    self.goal = current_goal
    layout = QVBoxLayout(self)
    self.goal_input = QLineEdit(self)
    self.goal_input.setText(str(self.goal))
    layout.addWidget(QLabel("Введите желаемую цель:"))
    layout.addWidget(self.goal_input)

    button_layout = QtWidgets.QHBoxLayout()
    set_button = QPushButton("Установить", self)
    set_button.clicked.connect(self.accept)
    cancel_button = QPushButton("Отмена", self)
    cancel_button.clicked.connect(self.reject)

    button_layout.addWidget(set_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

   def get_goal(self):
       try:
         return float(self.goal_input.text())
       except ValueError:
         return 0

class PandasModel(QtCore.QAbstractTableModel):
  def __init__(self, data):
    QtCore.QAbstractTableModel.__init__(self)
    self._data = data
    self.colors = {
         "Пополнение": QColor(219, 238, 213),  # Светло-зеленый
         "Снятие": QColor(255, 204, 204) # Светло-красный
    }

  def rowCount(self, parent=None):
    return self._data.shape[0]

  def columnCount(self, parent=None):
    return self._data.shape[1]

  def data(self, index, role=QtCore.Qt.DisplayRole):
    if index.isValid():
        col = index.column()
        row = index.row()
        if role == QtCore.Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        elif role == QtCore.Qt.BackgroundRole:
            if col == 1:
               operation_type = self._data.iloc[row,1]
               if operation_type in self.colors:
                  return QBrush(self.colors[operation_type])
            elif col == 3:
                 if row > 0 and self._data.iloc[row, 3] != self._data.iloc[row - 1, 3]:
                    return QBrush(QColor(226,235,243))
    return None

  def headerData(self, col, orientation, role):
      if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
        column_names = ["Дата", "Тип", "Сумма", "Баланс", "Прогресс", "Цель"]
        return column_names[col]
      return None


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = PiggyBank()
    window.show()
    sys.exit(app.exec_())