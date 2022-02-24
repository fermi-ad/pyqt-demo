from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt
from rr_tune import qt60

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

Ui_MainWindow, QMainWindow = loadUiType('tune_window.ui')

class Main(QMainWindow, Ui_MainWindow):
    def __init__(self, ):
        super(Main, self).__init__()
        self.setupUi(self)
        self.qt60 = qt60()
        self.init_plot()
        self.event_comboBox.addItems(['e0','e1','e2','e3','e9'])
        self.event_dict = {'e0':0, 'e1':64, 'e2':128, 'e3':192,'e9':256}

    def read_tune(self):
        timeslot = self.timeslot_spinBox.value() 
        evt=self.event_comboBox.currentText()
        offs=self.event_dict[evt]
        qh,qv = self.qt60.get_tune(offs)
        self.qh_doubleSpinBox.setValue(qh)
        self.qv_doubleSpinBox.setValue(qv)

    def init_plot(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.qtcurrents_mpl_verticalLayout.addWidget(self.canvas)

    def update_plot(self):
        try:
            self.ax.cla()
            timeslot = self.timeslot_spinBox.value() 
            currents = self.qt60.get_currents(timeslot)
            self.ax.bar([0,1,2,3,4,5,6,7,8],height=currents)
            self.canvas.draw_idle()
        except:
            print('bugger')
        


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec_())
