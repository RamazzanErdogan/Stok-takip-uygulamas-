import sys
import os
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from receteekran import Ui_MainWindow

def dosya_yolu(dosya):
    # PyInstaller exe içindeysek
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, dosya)

    # Normal .py çalışıyorsa → dosyanın bulunduğu klasör
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, dosya)





class ekranrecete(QMainWindow):
     def __init__(self):
        
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # 📦 Hammaddeleri yükle
        self.hammaddeler = self.hammaddeleri_getir()
        self.ui.pushButton_3.clicked.connect(self.ana_ekrana_don)
        self.ui.pushButton_2.clicked.connect(self.urun_ara)
        self.ui.pushButton.clicked.connect(self.secili_urunun_recetesini_goster)
                # tablo başlıkları
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(
            ["Hammadde", "Miktar (gr)"]
        )

        # yeni reçete ekleme butonları
        self.ui.pushButton_5.clicked.connect(self.satir_ekle)
        self.ui.pushButton_4.clicked.connect(self.receteyi_kaydet)

        if not os.path.exists(dosya_yolu("rr.csv")):
            QMessageBox.critical(self, "Hata", "CSV dosyası bulunamadı!")
            sys.exit()

        

        self.csvden_listeye_bas()
     def csvden_listeye_bas(self):
         df = pd.read_csv(dosya_yolu("rr.csv"), encoding="utf-8-sig", sep=";")

         urunler = df.iloc[:, 0].unique()   # TEKRARLARI SİL

         self.ui.listWidget.clear()
         for urun in urunler:
             self.ui.listWidget.addItem(str(urun))
     def hammaddeleri_getir(self):
        df = pd.read_csv(dosya_yolu("rm.csv"), sep=";", encoding="utf-8-sig")
        return df["URUN ISIM"].astype(str).tolist()

     def satir_ekle(self):
        row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)

        combo = QtWidgets.QComboBox()
        combo.setEditable(True)
        combo.addItems(self.hammaddeler)

        completer = QCompleter(self.hammaddeler)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        combo.setCompleter(completer)

        self.ui.tableWidget.setCellWidget(row, 0, combo)

        spin = QtWidgets.QSpinBox()
        spin.setMinimum(1)
        spin.setMaximum(1000000)
        self.ui.tableWidget.setCellWidget(row, 1, spin)


    # -------------------------------------------------
     def receteyi_kaydet(self):
        urun = self.ui.lineEdit.text().strip()

        if not urun:
            QMessageBox.warning(self, "Uyarı", "Ürün adı girin.")
            return

        satir_sayisi = self.ui.tableWidget.rowCount()
        if satir_sayisi == 0:
            QMessageBox.warning(self, "Uyarı", "Reçete boş.")
            return

        yeni_kayitlar = []

        for row in range(satir_sayisi):
            combo = self.ui.tableWidget.cellWidget(row, 0)
            spin = self.ui.tableWidget.cellWidget(row, 1)

            if not combo or not spin:
                continue

            hammadde = combo.currentText().strip()
            miktar = spin.value()

            if miktar > 0:
                yeni_kayitlar.append({
                    "urun": urun,
                    "hammadde": hammadde,
                    "miktar_gr": miktar
                })

        if not yeni_kayitlar:
            QMessageBox.warning(self, "Uyarı", "Geçerli reçete yok.")
            return

        yeni_df = pd.DataFrame(yeni_kayitlar)

        if os.path.exists(dosya_yolu("rr.csv")):
            eski_df = pd.read_csv(dosya_yolu("rr.csv"), sep=";", encoding="utf-8-sig")
            df = pd.concat([eski_df, yeni_df], ignore_index=True)
        else:
            df = yeni_df

        df.to_csv(dosya_yolu("rr.csv"), sep=";", index=False, encoding="utf-8-sig")

        QMessageBox.information(
            self,
            "Başarılı",
            f"{urun} için reçete eklendi ({len(yeni_kayitlar)} hammadde)."
        )

        self.ui.lineEdit.clear()
        self.ui.tableWidget.setRowCount(0)
        self.csvden_listeye_bas()

     def secili_urunun_recetesini_goster(self):
        item = self.ui.listWidget.currentItem()
        if not item:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ürün seçin.")
            return

        secili_urun = item.text()

        df = pd.read_csv(dosya_yolu("rr.csv"), sep=";", encoding="utf-8-sig")
        filtre = df[df["urun"] == secili_urun]

        self.ui.listWidget_2.clear()

        for _, satir in filtre.iterrows():
            hammadde = satir["hammadde"]
            miktar = satir["miktar_gr"]

            self.ui.listWidget_2.addItem(
                f"{hammadde} - {miktar}"
            )


     def urun_ara(self):
        aranan = self.ui.lineEdit_ara.text().strip().lower()
        if not aranan:
            return

        for i in range(self.ui.listWidget.count()):
            item = self.ui.listWidget.item(i)
            if aranan in item.text().lower():
                self.ui.listWidget.setCurrentRow(i)
                self.ui.listWidget.scrollToItem(item)
                return

        QMessageBox.information(self, "Bulunamadı", "Aranan ürün listede yok.")
     def ana_ekrana_don(self):
        from anaekran_uygulama import AnaEkran  # 🔑 GEÇ İMPORT
        self.ana = AnaEkran()
        self.ana.show()
        self.close()

    
def calistir():
    app = QtWidgets.QApplication(sys.argv)
    win = ekranrecete()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    calistir()