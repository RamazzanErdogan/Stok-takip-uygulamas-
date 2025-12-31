import sys
import os
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from satıs import Ui_MainWindow


# -------------------------------------------------
# DOSYA YOLLARI
# -------------------------------------------------

def dosya_yolu(dosya):
    # PyInstaller exe içindeysek
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, dosya)

    # Normal .py çalışıyorsa → dosyanın bulunduğu klasör
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, dosya)
def guvenli_sayi(deger):
    if pd.isna(deger):
        return 0.0
    return float(str(deger).replace(",", "."))


# -------------------------------------------------
# 🔁 REKÜRSİF STOKTAN DÜŞME (STABİL)
# -------------------------------------------------
def stoktan_dus(urun_adi, carpan, rr_df, rm_df, ziyaret=None, stokta_olmayanlar=None):
    carpan = guvenli_sayi(carpan)

    if ziyaret is None:
        ziyaret = set()
    if stokta_olmayanlar is None:
        stokta_olmayanlar = set()

    if urun_adi in ziyaret:
        return

    ziyaret.add(urun_adi)

    recete = rr_df[rr_df["urun"] == urun_adi]

    # 🔹 Reçetesi yoksa → gerçek stok kalemi
    if recete.empty:
        idx = rm_df[rm_df["URUN ISIM"] == urun_adi].index
        if idx.empty:
            stokta_olmayanlar.add(urun_adi)
        else:
            rm_df.loc[idx[0], "DEGER"] -= carpan
        return

    # 🔹 Reçetesi varsa
    for _, satir in recete.iterrows():
        ic_urun = satir["hammadde"]
        miktar = guvenli_sayi(satir["miktar_gr"]) * carpan

        # ürün kendini içeriyorsa
        if ic_urun == urun_adi:
            idx = rm_df[rm_df["URUN ISIM"] == ic_urun].index
            if idx.empty:
                stokta_olmayanlar.add(ic_urun)
            else:
                rm_df.loc[idx[0], "DEGER"] -= miktar
            continue

        stoktan_dus(ic_urun, miktar, rr_df, rm_df, ziyaret, stokta_olmayanlar)


# -------------------------------------------------
# 🛒 SATIŞ EKRANI
# -------------------------------------------------
class satisEkrani(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.satis_listesi = []

        self.urunleri_yukle()
        self.ui.pushButton_4.clicked.connect(self.ana_ekrana_don)
        self.ui.pushButton.clicked.connect(self.listeye_ekle)
        self.ui.pushButton_2.clicked.connect(self.satislari_kaydet)
        self.ui.pushButton_3.clicked.connect(self.gunumuz)

    # -----------------------------
    def urunleri_yukle(self):
        if not os.path.exists(dosya_yolu("rr.csv")):
            return

        df = pd.read_csv(dosya_yolu("rr.csv"), sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()

        self.ui.comboBox.clear()
        for urun in df["urun"].unique():
            self.ui.comboBox.addItem(str(urun))

    # -----------------------------
    def gunumuz(self):
        self.ui.dateEdit.setDate(QDate.currentDate())

    # -----------------------------
    def listeye_ekle(self):
        tarih = self.ui.dateEdit.date().toString("yyyy-MM-dd")
        urun = self.ui.comboBox.currentText().strip()
        adet = self.ui.spinBox.value()

        if adet <= 0:
            QMessageBox.warning(self, "Uyarı", "Adet 0 olamaz.")
            return

        self.satis_listesi.append([tarih, urun, adet])
        self.ui.listWidget.addItem(f"{tarih} | {urun} | {adet}")

        self.ui.spinBox.setValue(0)

    # -----------------------------
    def satislari_kaydet(self):
        if not self.satis_listesi:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek satış yok.")
            return

        # 1️⃣ YENİ SATIŞLAR
        yeni_df = pd.DataFrame(
            self.satis_listesi,
            columns=["Tarih", "urun", "adet"]
        )

        # 2️⃣ ESKİ + YENİ BİRLEŞTİR
        if os.path.exists(dosya_yolu("rs.csv")):
            eski_df = pd.read_csv(dosya_yolu("rs.csv"), sep=";", encoding="utf-8-sig")
            df_satis = pd.concat([eski_df, yeni_df], ignore_index=True)
        else:
            df_satis = yeni_df

        # 3️⃣ TARİHİ GERÇEK DATETIME YAP
        df_satis["Tarih"] = pd.to_datetime(
            df_satis["Tarih"],
            format="mixed",     # 🔑 hangi format gelirse gelsin
            dayfirst=True,      # 1.01.2000 gibi tarihler için
            errors="coerce"     # bozuk varsa NaT yap, programı patlatma
        )


        # 4️⃣ TARİHE GÖRE SIRALA
        df_satis = df_satis.sort_values("Tarih").reset_index(drop=True)

        # 5️⃣ TEKRAR STRING YAP
        df_satis["Tarih"] = df_satis["Tarih"].dt.strftime("%Y-%m-%d")

        # 6️⃣ CSV’YE TEK KEZ YAZ
        df_satis.to_csv(dosya_yolu("rs.csv"), sep=";", index=False, encoding="utf-8-sig")

        # -------------------------------------------------
        # 7️⃣ STOKTAN DÜŞ
        rr_df = pd.read_csv(dosya_yolu("rr.csv"), sep=";", encoding="utf-8-sig")
        rm_df = pd.read_csv(dosya_yolu("rm.csv"), sep=";", encoding="utf-8-sig")

        rr_df.columns = rr_df.columns.str.strip()
        rm_df.columns = rm_df.columns.str.strip()

        rm_df["DEGER"] = (
            rm_df["DEGER"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        rr_df["urun"] = rr_df["urun"].astype(str).str.strip()
        rr_df["hammadde"] = rr_df["hammadde"].astype(str).str.strip()
        rm_df["URUN ISIM"] = rm_df["URUN ISIM"].astype(str).str.strip()

        stokta_olmayanlar = set()

        for tarih, urun, adet in self.satis_listesi:
            stoktan_dus(
                urun,
                adet,
                rr_df,
                rm_df,
                ziyaret=set(),
                stokta_olmayanlar=stokta_olmayanlar
            )

        rm_df.to_csv(dosya_yolu("rm.csv"), sep=";", index=False, encoding="utf-8-sig")

        QMessageBox.information(
            self,
            "Başarılı",
            "Satışlar tarihe göre sıralı şekilde kaydedildi ve stoktan düşüldü."
        )

        self.satis_listesi.clear()
        self.ui.listWidget.clear()

    def ana_ekrana_don(self):
        from anaekran_uygulama import AnaEkran  # 🔑 GEÇ İMPORT
        self.ana = AnaEkran()
        self.ana.show()
        self.close()


# -------------------------------------------------
def calistir():
    app = QtWidgets.QApplication(sys.argv)
    win = satisEkrani()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    calistir()
