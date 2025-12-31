import sys
import os
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from stok import Ui_MainWindow   # stok.ui'den üretilen py dosyası


def dosya_yolu(dosya):
    # PyInstaller exe içindeysek
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, dosya)

    # Normal .py çalışıyorsa → dosyanın bulunduğu klasör
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, dosya)

class StokEkrani(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.doubleSpinBox.setMinimum(0)
        self.ui.doubleSpinBox.setMaximum(10**12)
        self.ui.doubleSpinBox_2.setMinimum(0)
        self.ui.doubleSpinBox_2.setMaximum(10**12)
        # Buton bağlantıları
        self.ui.pushButton.clicked.connect(self.yeni_urun_ekle)
        self.ui.pushButton_2.clicked.connect(self.stok_arttir)
        self.ui.pushButton_3.clicked.connect(self.urun_ara)
        self.ui.pushButton_4.clicked.connect(self.ana_ekrana_don)

        self.stoklari_yukle()

    # -------------------------------------------------
    def stoklari_yukle(self):
        if not os.path.exists(dosya_yolu("rm.csv")):
            return

        df = pd.read_csv(dosya_yolu("rm.csv"), sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        self.ui.tableWidget.setRowCount(len(df))
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Ürün", "Stok"])

        for row, (_, satir) in enumerate(df.iterrows()):
            self.ui.tableWidget.setItem(
                row, 0, QtWidgets.QTableWidgetItem(str(satir["URUN ISIM"]))
            )
            self.ui.tableWidget.setItem(
                row, 1, QtWidgets.QTableWidgetItem(str(satir["DEGER"]))
            )

        self.ui.tableWidget.resizeColumnsToContents()

    # -------------------------------------------------
    def yeni_urun_ekle(self):
        urun = self.ui.lineEdit.text().strip()
        miktar = self.ui.doubleSpinBox.value()

        if not urun:
            QMessageBox.warning(self, "Uyarı", "Ürün adı boş olamaz.")
            return

        df = pd.read_csv(dosya_yolu("rm.csv"), sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        if urun.lower() in df["URUN ISIM"].astype(str).str.lower().values:
            QMessageBox.warning(self, "Uyarı", "Bu ürün zaten mevcut.")
            return

        yeni_satir = pd.DataFrame([[urun, miktar]], columns=["URUN ISIM", "DEGER"])
        df = pd.concat([df, yeni_satir], ignore_index=True)

        df.to_csv(dosya_yolu("rm.csv"), sep=";", index=False, encoding="utf-8-sig")

        self.stoklari_yukle()
        self.ui.lineEdit.clear()
        self.ui.doubleSpinBox.setValue(0)

    # -------------------------------------------------
    def stok_arttir(self):
        secili = self.ui.tableWidget.currentRow()
        if secili < 0:
            QMessageBox.warning(self, "Uyarı", "Tablodan bir ürün seçin.")
            return

        miktar = self.ui.doubleSpinBox_2.value()
        if miktar <= 0:
            QMessageBox.warning(self, "Uyarı", "Eklenecek miktar 0 olamaz.")
            return

        urun = self.ui.tableWidget.item(secili, 0).text()

        df = pd.read_csv(dosya_yolu("rm.csv"), sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        idx = df[df["URUN ISIM"] == urun].index
        if idx.empty:
            QMessageBox.warning(self, "Hata", "Ürün bulunamadı.")
            return

        df.loc[idx[0], "DEGER"] += miktar
        df.to_csv(dosya_yolu("rm.csv"), sep=";", index=False, encoding="utf-8-sig")

        self.stoklari_yukle()
        self.ui.doubleSpinBox_2.setValue(0)

    # -------------------------------------------------
    def urun_ara(self):
        aranan = self.ui.lineEdit_2.text().strip().lower()
        if not aranan:
            return

        for i in range(self.ui.tableWidget.rowCount()):
            urun = self.ui.tableWidget.item(i, 0).text().lower()
            if aranan in urun:
                self.ui.tableWidget.selectRow(i)
                self.ui.tableWidget.scrollToItem(
                    self.ui.tableWidget.item(i, 0)
                )
                return

        QMessageBox.information(self, "Bulunamadı", "Ürün listede yok.")
    def ana_ekrana_don(self):
        from anaekran_uygulama import AnaEkran  # 🔑 GEÇ İMPORT
        self.ana = AnaEkran()
        self.ana.show()
        self.close()

# -------------------------------------------------
def calistir():
    app = QtWidgets.QApplication(sys.argv)
    win = StokEkrani()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    calistir()
