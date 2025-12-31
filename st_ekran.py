import sys
import os
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from satistakip import Ui_MainWindow   # designer ui



def dosya_yolu(dosya):
    # PyInstaller exe içindeysek
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, dosya)

    # Normal .py çalışıyorsa → dosyanın bulunduğu klasör
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, dosya)
class SatisTakipEkrani(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButton.clicked.connect(self.tarihe_gore_getir)
        self.ui.pushButton_2.clicked.connect(self.urune_gore_getir)
        self.ui.pushButton_3.clicked.connect(self.ana_ekrana_don)

        self.urunleri_yukle()

    # ----------------------------------
    def urunleri_yukle(self):
        if not os.path.exists(dosya_yolu("rs.csv")):
            return

        df = pd.read_csv(dosya_yolu("rs.csv"), sep=";", encoding="utf-8-sig")
        urunler = df["urun"].unique()

        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(urunler)

    # ----------------------------------
    def tarihe_gore_getir(self):
        tarih = self.ui.dateEdit_tarih.date().toString("yyyy-MM-dd")

        df = pd.read_csv(dosya_yolu("rs.csv"), sep=";", encoding="utf-8-sig")
        filtre = df[df["Tarih"] == tarih]

        self.ui.listWidget.clear()

        if filtre.empty:
            QMessageBox.information(self, "Bilgi", "Bu tarihte satış yok.")
            return

        for _, row in filtre.iterrows():
            self.ui.listWidget.addItem(
                f"{row['Tarih']} | {row['urun']} | {row['adet']}"
            )

    # ----------------------------------
    def urune_gore_getir(self):
        urun = self.ui.comboBox.currentText()

        df = pd.read_csv(dosya_yolu("rs.csv"), sep=";", encoding="utf-8-sig")
        filtre = df[df["urun"] == urun]

        self.ui.listWidget.clear()

        if filtre.empty:
            QMessageBox.information(self, "Bilgi", "Bu ürün hiç satılmamış.")
            return

        for _, row in filtre.iterrows():
            self.ui.listWidget.addItem(
                f"{row['Tarih']} | {row['urun']} | {row['adet']}"
            )
    def ana_ekrana_don(self):
        from anaekran_uygulama import AnaEkran  # 🔑 GEÇ İMPORT
        self.ana = AnaEkran()
        self.ana.show()
        self.close()


def calistir():
    app = QtWidgets.QApplication(sys.argv)
    win = SatisTakipEkrani()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    calistir()
