# -*- coding: utf-8 -*-


from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon, QTextDocument
from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton,
    QHBoxLayout, QFormLayout, QCheckBox, QDoubleSpinBox, QGroupBox,
    QLabel, QDialogButtonBox, QComboBox, QGridLayout, QScrollArea, QWidget, QProgressDialog, QApplication, QFileDialog
)

from qgis.PyQt.QtPrintSupport import QPrinter

from .resources import *
from .emsal_degerleme_dockwidget import EmsalDegerlemeDockWidget

import os
from datetime import datetime, timedelta


class EmsalSecimDialog(QDialog):
    def __init__(self, plugin, layer, hedef, parent=None):
        super().__init__(parent)

        self.plugin = plugin
        self.layer = layer
        self.hedef = hedef
        self.oda_checkboxes = {}

        self.setWindowTitle("Emsal Seçim Kriterleri")
        self.resize(820, 650)

        dialog_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        ana_layout = QVBoxLayout(scroll_widget)

        # -----------------------------------------------------
        # Seçilen taşınmazın bilgileri
        # -----------------------------------------------------
        konu_grup = QGroupBox("Seçilen Taşınmazın Bilgileri")
        konu_grid = QGridLayout()

        bilgi_ciftleri = self.plugin.tasinmaz_bilgi_ciftleri(self.hedef)

        for i, (etiket, deger) in enumerate(bilgi_ciftleri):
            row = i // 2
            col = (i % 2) * 2

            lbl_etiket = QLabel(f"{etiket}:")
            lbl_etiket.setStyleSheet("font-weight: bold;")
            lbl_deger = QLabel(str(deger))
            lbl_deger.setTextInteractionFlags(Qt.TextSelectableByMouse)

            konu_grid.addWidget(lbl_etiket, row, col)
            konu_grid.addWidget(lbl_deger, row, col + 1)

        konu_grup.setLayout(konu_grid)
        ana_layout.addWidget(konu_grup)

        # -----------------------------------------------------
        #Oda tipi seçimi
        # -----------------------------------------------------
        oda_grup = QGroupBox("Oda Tipi Seçimi")
        oda_layout = QVBoxLayout()

        mahalle = self.plugin.metin_al(self.hedef, "mahalle")
        hedef_oda_kod = self.plugin.oda_kodu(self.hedef)

        oda_kodlari = self.plugin.oda_kodlarini_bul(layer, mahalle)
        if len(oda_kodlari) == 0:
            oda_kodlari = ["1", "2", "3"]

        for kod in oda_kodlari:
            etiket = self.plugin.oda_etiketi_from_kod(kod)
            cb = QCheckBox(etiket)
            cb.setChecked(str(kod) == str(hedef_oda_kod))
            self.oda_checkboxes[str(kod)] = cb
            oda_layout.addWidget(cb)

        oda_grup.setLayout(oda_layout)
        ana_layout.addWidget(oda_grup)

        # -----------------------------------------------------
        # Sayısal aralık filtreleri
        # -----------------------------------------------------
        aralik_grup = QGroupBox("Alan, Kat ve Bina Yaşı Aralıkları")
        aralik_form = QFormLayout()

        hedef_alan = self.plugin.sayi_al(self.hedef, "net_alan_m2")
        hedef_kat = self.plugin.sayi_al(self.hedef, "bulundugu_kat")
        hedef_yas = self.plugin.sayi_al(self.hedef, "bina_yasi")

        self.sp_min_alan = QDoubleSpinBox()
        self.sp_min_alan.setRange(0, 1000000)
        self.sp_min_alan.setDecimals(2)
        self.sp_min_alan.setSuffix(" m²")
        self.sp_min_alan.setValue(max(0, hedef_alan * 0.70))

        self.sp_max_alan = QDoubleSpinBox()
        self.sp_max_alan.setRange(0, 1000000)
        self.sp_max_alan.setDecimals(2)
        self.sp_max_alan.setSuffix(" m²")
        self.sp_max_alan.setValue(hedef_alan * 1.30)

        self.sp_min_kat = QDoubleSpinBox()
        self.sp_min_kat.setRange(-10, 200)
        self.sp_min_kat.setDecimals(0)
        self.sp_min_kat.setValue(max(-10, hedef_kat - 2))

        self.sp_max_kat = QDoubleSpinBox()
        self.sp_max_kat.setRange(-10, 200)
        self.sp_max_kat.setDecimals(0)
        self.sp_max_kat.setValue(hedef_kat + 2)

        self.sp_min_yas = QDoubleSpinBox()
        self.sp_min_yas.setRange(0, 200)
        self.sp_min_yas.setDecimals(0)
        self.sp_min_yas.setValue(max(0, hedef_yas - 5))

        self.sp_max_yas = QDoubleSpinBox()
        self.sp_max_yas.setRange(0, 200)
        self.sp_max_yas.setDecimals(0)
        self.sp_max_yas.setValue(hedef_yas + 5)

        aralik_form.addRow("Minimum net alan:", self.sp_min_alan)
        aralik_form.addRow("Maksimum net alan:", self.sp_max_alan)
        aralik_form.addRow("Minimum bulunduğu kat:", self.sp_min_kat)
        aralik_form.addRow("Maksimum bulunduğu kat:", self.sp_max_kat)
        aralik_form.addRow("Minimum bina yaşı:", self.sp_min_yas)
        aralik_form.addRow("Maksimum bina yaşı:", self.sp_max_yas)

        aralik_grup.setLayout(aralik_form)
        ana_layout.addWidget(aralik_grup)

        # -----------------------------------------------------
        # Asansör / otopark seçimleri
        # -----------------------------------------------------
        donati_grup = QGroupBox("Asansör ve Otopark Seçimi")
        donati_form = QFormLayout()

        self.cmb_asansor = self.uc_secimli_combo()
        self.cmb_otopark = self.uc_secimli_combo()

        hedef_asansor = int(self.plugin.sayi_al(self.hedef, "asansor", -1))
        hedef_otopark = int(self.plugin.sayi_al(self.hedef, "otopark", -1))

        if hedef_asansor == 1:
            self.cmb_asansor.setCurrentIndex(1)
        elif hedef_asansor == 0:
            self.cmb_asansor.setCurrentIndex(2)

        if hedef_otopark == 1:
            self.cmb_otopark.setCurrentIndex(1)
        elif hedef_otopark == 0:
            self.cmb_otopark.setCurrentIndex(2)

        donati_form.addRow("Asansör:", self.cmb_asansor)
        donati_form.addRow("Otopark:", self.cmb_otopark)

        donati_grup.setLayout(donati_form)
        ana_layout.addWidget(donati_grup)

        # -----------------------------------------------------
        # Manzara seçimleri
        # -----------------------------------------------------
        manzara_grup = QGroupBox("Manzara Seçimi")
        manzara_form = QFormLayout()

        self.cmb_sehir_manz = self.uc_secimli_combo()
        self.cmb_doga_manz = self.uc_secimli_combo()
        self.cmb_gol_manz = self.uc_secimli_combo()
        self.cmb_bogaz_manz = self.uc_secimli_combo()

        self.varsayilan_combo_sec(self.cmb_sehir_manz, self.plugin.sayi_al(self.hedef, "sehir_manz", -1))
        self.varsayilan_combo_sec(self.cmb_doga_manz, self.plugin.sayi_al(self.hedef, "doga_manz", -1))
        self.varsayilan_combo_sec(self.cmb_gol_manz, self.plugin.sayi_al(self.hedef, "gol_manz", -1))
        self.varsayilan_combo_sec(self.cmb_bogaz_manz, self.plugin.sayi_al(self.hedef, "bogaz_manz", -1))

        manzara_form.addRow("Şehir manzarası:", self.cmb_sehir_manz)
        manzara_form.addRow("Doğa manzarası:", self.cmb_doga_manz)
        manzara_form.addRow("Göl manzarası:", self.cmb_gol_manz)
        manzara_form.addRow("Boğaz manzarası:", self.cmb_bogaz_manz)

        manzara_grup.setLayout(manzara_form)
        ana_layout.addWidget(manzara_grup)

        butonlar = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        butonlar.accepted.connect(self.accept)
        butonlar.rejected.connect(self.reject)

        scroll.setWidget(scroll_widget)
        dialog_layout.addWidget(scroll)
        dialog_layout.addWidget(butonlar)

        self.setLayout(dialog_layout)

    def uc_secimli_combo(self):
        cmb = QComboBox()
        cmb.addItem("Farketmez", None)
        cmb.addItem("Var", 1)
        cmb.addItem("Yok", 0)
        return cmb

    def varsayilan_combo_sec(self, cmb, deger):
        try:
            d = int(float(deger))
            if d == 1:
                cmb.setCurrentIndex(1)
            elif d == 0:
                cmb.setCurrentIndex(2)
            else:
                cmb.setCurrentIndex(0)
        except Exception:
            cmb.setCurrentIndex(0)

    def ayarlari_al(self):
        secili_kodlar = []

        for kod, cb in self.oda_checkboxes.items():
            if cb.isChecked():
                secili_kodlar.append(str(kod))

        return {
            "mahalle": self.plugin.metin_al(self.hedef, "mahalle"),
            "secili_oda_kodlari": secili_kodlar,
            "min_alan": self.sp_min_alan.value(),
            "max_alan": self.sp_max_alan.value(),
            "min_kat": self.sp_min_kat.value(),
            "max_kat": self.sp_max_kat.value(),
            "min_yas": self.sp_min_yas.value(),
            "max_yas": self.sp_max_yas.value(),
            "asansor": self.cmb_asansor.currentData(),
            "otopark": self.cmb_otopark.currentData(),
            "sehir_manz": self.cmb_sehir_manz.currentData(),
            "doga_manz": self.cmb_doga_manz.currentData(),
            "gol_manz": self.cmb_gol_manz.currentData(),
            "bogaz_manz": self.cmb_bogaz_manz.currentData()
        }


class SonucDialog(QDialog):
    def __init__(self, rapor, pdf_rapor=None, parent=None):
        super().__init__(parent)

        self.rapor = rapor
        self.pdf_rapor = pdf_rapor if pdf_rapor is not None else rapor

        self.setWindowTitle("Karşılaştırma Yöntemi Sonucu")
        self.resize(1100, 780)

        layout = QVBoxLayout()

        self.text = QTextEdit()
        self.text.setReadOnly(True)

        if isinstance(rapor, str) and rapor.lstrip().lower().startswith("<html"):
            self.text.setHtml(rapor)
        else:
            self.text.setPlainText(rapor)

        btn_layout = QHBoxLayout()

        btn_pdf = QPushButton("PDF Raporu Kaydet")
        btn_pdf.clicked.connect(self.pdf_kaydet)

        btn_kapat = QPushButton("Kapat")
        btn_kapat.clicked.connect(self.close)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_pdf)
        btn_layout.addWidget(btn_kapat)

        layout.addWidget(self.text)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def pdf_kaydet(self):
        dosya_yolu, _ = QFileDialog.getSaveFileName(
            self,
            "PDF Raporu Kaydet",
            "emsal_degerleme_raporu.pdf",
            "PDF Dosyası (*.pdf)"
        )

        if not dosya_yolu:
            return

        if not dosya_yolu.lower().endswith(".pdf"):
            dosya_yolu += ".pdf"

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(dosya_yolu)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Landscape)
        try:
            printer.setFullPage(True)
            printer.setPageMargins(3, 3, 3, 3, QPrinter.Millimeter)
        except Exception:
            pass

        doc = QTextDocument()
        try:
            page_size = printer.pageRect().size()
            doc.setPageSize(page_size)
            doc.setTextWidth(page_size.width())
        except Exception:
            pass
        doc.setHtml(self.pdf_rapor)
        doc.print_(printer)

        QMessageBox.information(self, "PDF Raporu", "PDF raporu başarıyla kaydedildi.")


class EmsalDegerleme:

    REFERANS_TUFE = 121.47
    RAPORDA_GOSTERILECEK_EMSAL = 150

    ODA_KOD_ETIKET = {
        "1": "2+1",
        "2": "3+1",
        "3": "4+1"
    }

    # İlk ekrandaki taşınmaz bilgileri içinde gösterilmeyecek alanlar
    GIZLI_ALANLAR = {
        "satis_id", "bb_id", "bina_id"
    }

    # İlk ekranda gösterilecek alan sırası
    GOSTERILECEK_ALANLAR = [
        "satis_fiyati",
        "satis_tarihi",
        "oda_sayisi",
        "net_alan_m2",
        "bulundugu_kat",
        "bina_yasi",
        "asansor",
        "otopark",
        "mahalle",
        "sehir_manz",
        "doga_manz",
        "gol_manz",
        "bogaz_manz",
        "kuzey_cephe",
        "guney_cephe",
        "dogu_cephe",
        "bati_cephe",
        "marmaray_mesafe",
        "metro_mesafe",
        "havaalani_mesafe",
        "durak_mesafe"
    ]

    # Alan adlarını ekranda daha anlaşılır göstermek için
    ALAN_ETIKETLERI = {
        "satis_fiyati": "Satış Fiyatı",
        "satis_tarihi": "Satış Tarihi",
        "oda_sayisi": "Oda Sayısı",
        "net_alan_m2": "Net Alan",
        "bulundugu_kat": "Bulunduğu Kat",
        "bina_yasi": "Bina Yaşı",
        "asansor": "Asansör",
        "otopark": "Otopark",
        "mahalle": "Mahalle",
        "sehir_manz": "Şehir Manzarası",
        "doga_manz": "Doğa Manzarası",
        "gol_manz": "Göl Manzarası",
        "bogaz_manz": "Boğaz Manzarası",
        "kuzey_cephe": "Kuzey Cephe",
        "guney_cephe": "Güney Cephe",
        "dogu_cephe": "Doğu Cephe",
        "bati_cephe": "Batı Cephe",
        "marmaray_mesafe": "Marmaray Mesafesi",
        "metro_mesafe": "Metro Mesafesi",
        "havaalani_mesafe": "Havaalanı Mesafesi",
        "durak_mesafe": "Durak Mesafesi"
    }

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "Emsal Değerleme"
        self.toolbar = self.iface.addToolBar("Emsal Değerleme")
        self.toolbar.setObjectName("EmsalDegerleme")
        self.pluginIsActive = False
        self.dockwidget = None

    def tr(self, message):
        return QCoreApplication.translate("EmsalDegerleme", message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        action = QAction(QIcon(icon_path), "Emsal Değerleme", self.iface.mainWindow())
        action.triggered.connect(self.run)

        self.iface.addToolBarIcon(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

        try:
            del self.toolbar
        except Exception:
            pass

    def run(self):
        if not self.pluginIsActive:
            self.pluginIsActive = True

            if self.dockwidget is None:
                self.dockwidget = EmsalDegerlemeDockWidget()
                self.dockwidget.pushButton.clicked.connect(self.baslat)

            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    def baslat(self):
        layer = self.iface.activeLayer()

        if layer is None:
            QMessageBox.warning(None, "Hata", "Aktif katman bulunamadı.")
            return

        secili = layer.selectedFeatures()

        if len(secili) != 1:
            self.iface.actionSelect().trigger()
            QMessageBox.information(
                None,
                "Haritadan Taşınmaz Seç",
                "Lütfen haritadan değerlemesi yapılacak 1 adet taşınmaz seçin.\n\n"
                "Taşınmazı seçtikten sonra tekrar 'Haritadan Ev Seç' butonuna basın."
            )
            return

        hedef = secili[0]

        secim_dialog = EmsalSecimDialog(self, layer, hedef, self.iface.mainWindow())
        if secim_dialog.exec_() != QDialog.Accepted:
            return

        ayar = secim_dialog.ayarlari_al()

        if len(ayar["secili_oda_kodlari"]) == 0:
            QMessageBox.warning(None, "Hata", "En az bir oda tipi seçmelisiniz.")
            return

        if ayar["min_alan"] > ayar["max_alan"]:
            QMessageBox.warning(None, "Hata", "Minimum net alan, maksimum net alandan büyük olamaz.")
            return

        if ayar["min_kat"] > ayar["max_kat"]:
            QMessageBox.warning(None, "Hata", "Minimum kat, maksimum kattan büyük olamaz.")
            return

        if ayar["min_yas"] > ayar["max_yas"]:
            QMessageBox.warning(None, "Hata", "Minimum bina yaşı, maksimum bina yaşından büyük olamaz.")
            return

        yukleniyor = QProgressDialog("Karşılaştırma yöntemi uygulanıyor...\nLütfen bekleyin.", None, 0, 0, self.iface.mainWindow())
        yukleniyor.setWindowTitle("Hesaplanıyor")
        yukleniyor.setWindowModality(Qt.ApplicationModal)
        yukleniyor.setCancelButton(None)
        yukleniyor.setMinimumDuration(0)
        yukleniyor.show()
        QApplication.processEvents()

        rapor = self.degerleme_raporu(layer, hedef, ayar)

        yukleniyor.close()
        QApplication.processEvents()

        pdf_rapor = self.pdf_raporu_olustur(layer, hedef, ayar)
        sonuc_dialog = SonucDialog(rapor, pdf_rapor, self.iface.mainWindow())
        sonuc_dialog.exec_()

    # ---------------------------------------------------------
    # VERİ OKUMA
    # ---------------------------------------------------------
    def alan_var_mi(self, feature, alan):
        try:
            return alan in feature.fields().names()
        except Exception:
            return False

    def sayi_al(self, feature, alan, varsayilan=0.0):
        try:
            if not self.alan_var_mi(feature, alan):
                return varsayilan
            deger = feature[alan]
            if deger is None or deger == "":
                return varsayilan
            return float(str(deger).replace(",", "."))
        except Exception:
            return varsayilan

    def metin_al(self, feature, alan, varsayilan=""):
        try:
            if not self.alan_var_mi(feature, alan):
                return varsayilan
            deger = feature[alan]
            if deger is None:
                return varsayilan
            return str(deger).strip().upper()
        except Exception:
            return varsayilan

    def oda_kodu(self, feature):
        try:
            if not self.alan_var_mi(feature, "oda_sayisi"):
                return ""
            deger = feature["oda_sayisi"]
            if deger is None:
                return ""
            s = str(deger).strip()
            if s.endswith(".0"):
                s = s[:-2]
            return s
        except Exception:
            return ""

    def oda_etiketi_from_kod(self, kod):
        kod = str(kod).strip()
        return self.ODA_KOD_ETIKET.get(kod, kod)

    def evet_hayir(self, deger):
        try:
            d = int(float(deger))
            if d == 1:
                return "Var"
            if d == 0:
                return "Yok"
        except Exception:
            pass
        return str(deger)

    def filtre_deger_yaz(self, deger):
        if deger is None:
            return "Farketmez"
        return "Var" if int(deger) == 1 else "Yok"

    def tarih_parse(self, val):
        if val is None:
            return None

        try:
            if hasattr(val, "toPyDate"):
                d = val.toPyDate()
                return datetime(d.year, d.month, d.day)
        except Exception:
            pass

        try:
            if isinstance(val, (int, float)):
                if val > 20000:
                    return datetime(1899, 12, 30) + timedelta(days=int(val))
        except Exception:
            pass

        try:
            if hasattr(val, "toString"):
                s = val.toString("yyyy-MM-dd")
            else:
                s = str(val)
        except Exception:
            s = str(val)

        s = s.strip()[:10]

        formatlar = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]

        for fmt in formatlar:
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                pass

        return None

    # ---------------------------------------------------------
    # SEÇİLEN TAŞINMAZ BİLGİLERİ
    # ---------------------------------------------------------
    def tasinmaz_bilgi_ciftleri(self, feature):
        ciftler = []

        for alan in self.GOSTERILECEK_ALANLAR:
            if not self.alan_var_mi(feature, alan):
                continue

            try:
                deger = feature[alan]
            except Exception:
                deger = ""

            if alan == "oda_sayisi":
                kod = self.oda_kodu(feature)
                deger = self.oda_etiketi_from_kod(kod)

            elif alan in ["asansor", "otopark", "sehir_manz", "doga_manz", "gol_manz", "bogaz_manz",
                          "kuzey_cephe", "guney_cephe", "dogu_cephe", "bati_cephe"]:
                deger = self.evet_hayir(deger)

            elif alan == "satis_tarihi":
                tarih = self.tarih_parse(deger)
                if tarih is not None:
                    deger = tarih.strftime("%Y-%m-%d")

            elif alan == "satis_fiyati":
                try:
                    deger = f"{float(deger):,.0f} TL"
                except Exception:
                    pass

            elif alan in ["net_alan_m2", "marmaray_mesafe", "metro_mesafe", "havaalani_mesafe", "durak_mesafe"]:
                try:
                    birim = "m²" if alan == "net_alan_m2" else "m"
                    deger = f"{float(deger):,.2f} {birim}"
                except Exception:
                    pass

            elif alan in ["bulundugu_kat", "bina_yasi"]:
                try:
                    deger = f"{float(deger):.0f}"
                except Exception:
                    pass

            etiket = self.ALAN_ETIKETLERI.get(alan, alan)
            ciftler.append((etiket, deger))

        return ciftler

    def tasinmaz_bilgiler_raporu(self, feature):
        return "\n".join([f"{etiket}: {deger}" for etiket, deger in self.tasinmaz_bilgi_ciftleri(feature)])

    # ---------------------------------------------------------
    # TÜFE
    # ---------------------------------------------------------
    def tufe(self, y, m):
        tablo = {
            (2022, 1): 23.98, (2022, 2): 25.13, (2022, 3): 26.50,
            (2022, 4): 28.42, (2022, 5): 29.27, (2022, 6): 30.72,
            (2022, 7): 31.45, (2022, 8): 31.91, (2022, 9): 32.89,
            (2022, 10): 34.05, (2022, 11): 35.04, (2022, 12): 35.45,

            (2023, 1): 37.81, (2023, 2): 39.00, (2023, 3): 39.89,
            (2023, 4): 40.84, (2023, 5): 40.86, (2023, 6): 42.46,
            (2023, 7): 46.49, (2023, 8): 50.71, (2023, 9): 53.12,
            (2023, 10): 54.95, (2023, 11): 56.75, (2023, 12): 58.41,

            (2024, 1): 62.33, (2024, 2): 65.15, (2024, 3): 67.21,
            (2024, 4): 69.35, (2024, 5): 71.68, (2024, 6): 72.86,
            (2024, 7): 75.21, (2024, 8): 77.07, (2024, 9): 79.36,
            (2024, 10): 81.64, (2024, 11): 83.48, (2024, 12): 84.33,

            (2025, 1): 88.58, (2025, 2): 90.59, (2025, 3): 92.82,
            (2025, 4): 95.60, (2025, 5): 97.06, (2025, 6): 98.40,
            (2025, 7): 100.42, (2025, 8): 102.47, (2025, 9): 105.78,
            (2025, 10): 108.48, (2025, 11): 109.42, (2025, 12): 110.39,

            (2026, 1): 115.73, (2026, 2): 119.16, (2026, 3): 121.47
        }
        return tablo.get((y, m), None)

    def fiyat_reel(self, fiyat, tarih):
        satis_tufe = self.tufe(tarih.year, tarih.month)

        if satis_tufe is None or satis_tufe <= 0:
            return None

        return fiyat * (self.REFERANS_TUFE / satis_tufe)

    # ---------------------------------------------------------
    # ODA SEÇENEKLERİ VE EMSAL FİLTRELEME
    # ---------------------------------------------------------
    def oda_kodlarini_bul(self, layer, mahalle):
        kodlar = set()

        for f in layer.getFeatures():
            if self.metin_al(f, "mahalle") != mahalle:
                continue

            kod = self.oda_kodu(f)
            if kod != "":
                kodlar.add(kod)

        def siralama_anahtari(x):
            try:
                return int(float(x))
            except Exception:
                return 9999

        return sorted(list(kodlar), key=siralama_anahtari)

    def veri_gecerli_mi(self, f):
        satis = self.sayi_al(f, "satis_fiyati")
        alan = self.sayi_al(f, "net_alan_m2")

        if not self.alan_var_mi(f, "satis_tarihi"):
            return False

        tarih = self.tarih_parse(f["satis_tarihi"])

        return satis > 0 and alan > 0 and tarih is not None

    def filtre_uygun_mu(self, f, alan, secilen_deger):
        if secilen_deger is None:
            return True
        return int(self.sayi_al(f, alan, -1)) == int(secilen_deger)

    def emsal_uygun_mu(self, f, hedef, ayar):
        if f.id() == hedef.id():
            return False

        if not self.veri_gecerli_mi(f):
            return False

        # Mahalle şartı burada otomatik ve zorunlu uygulanır.
        if self.metin_al(f, "mahalle") != ayar["mahalle"]:
            return False

        if self.oda_kodu(f) not in ayar["secili_oda_kodlari"]:
            return False

        alan = self.sayi_al(f, "net_alan_m2")
        if alan < ayar["min_alan"] or alan > ayar["max_alan"]:
            return False

        kat = self.sayi_al(f, "bulundugu_kat")
        if kat < ayar["min_kat"] or kat > ayar["max_kat"]:
            return False

        yas = self.sayi_al(f, "bina_yasi")
        if yas < ayar["min_yas"] or yas > ayar["max_yas"]:
            return False

        if not self.filtre_uygun_mu(f, "asansor", ayar["asansor"]):
            return False

        if not self.filtre_uygun_mu(f, "otopark", ayar["otopark"]):
            return False

        if not self.filtre_uygun_mu(f, "sehir_manz", ayar["sehir_manz"]):
            return False

        if not self.filtre_uygun_mu(f, "doga_manz", ayar["doga_manz"]):
            return False

        if not self.filtre_uygun_mu(f, "gol_manz", ayar["gol_manz"]):
            return False

        if not self.filtre_uygun_mu(f, "bogaz_manz", ayar["bogaz_manz"]):
            return False

        return True

    def emsalleri_bul(self, layer, hedef, ayar):
        emsaller = []

        for f in layer.getFeatures():
            if self.emsal_uygun_mu(f, hedef, ayar):
                emsaller.append(f)

        return emsaller

    # ---------------------------------------------------------
    # HESAPLAMA VE DÜZELTME KATSAYILARI
    # ---------------------------------------------------------
    def alan_grubu(self, deger):
        try:
            v = float(deger)
        except Exception:
            return None
        if v <= 75:
            return "0-75 m²"
        if v <= 100:
            return "76-100 m²"
        if v <= 125:
            return "101-125 m²"
        if v <= 150:
            return "126-150 m²"
        return "151 m² ve üzeri"

    def yas_grubu(self, deger):
        try:
            v = float(deger)
        except Exception:
            return None
        if v <= 5:
            return "0-5 yaş"
        if v <= 10:
            return "6-10 yaş"
        if v <= 15:
            return "11-15 yaş"
        if v <= 20:
            return "16-20 yaş"
        return "21 yaş ve üzeri"

    def kat_grubu(self, deger):
        try:
            v = float(deger)
        except Exception:
            return None
        if v <= -1:
            return "Bodrum kat"
        if v == 0:
            return "Zemin kat"
        if v <= 2:
            return "Alt katlar"
        if v <= 5:
            return "Ara katlar"
        if v <= 9:
            return "Üst katlar"
        return "Çok üst katlar"

    def mesafe_grubu(self, deger, alan):
        try:
            v = float(deger)
        except Exception:
            return None

        if alan == "marmaray_mesafe":
            if v <= 1000:
                return "0-1000 m"
            if v <= 2500:
                return "1001-2500 m"
            if v <= 5000:
                return "2501-5000 m"
            if v <= 7500:
                return "5001-7500 m"
            return "7501 m ve üzeri"

        if alan == "metro_mesafe":
            if v <= 1000:
                return "0-1000 m"
            if v <= 2500:
                return "1001-2500 m"
            if v <= 5000:
                return "2501-5000 m"
            if v <= 7500:
                return "5001-7500 m"
            return "7501 m ve üzeri"

        if alan == "havaalani_mesafe":
            if v <= 3000:
                return "0-3000 m"
            if v <= 5000:
                return "3001-5000 m"
            if v <= 7000:
                return "5001-7000 m"
            if v <= 9000:
                return "7001-9000 m"
            return "9001 m ve üzeri"

        if alan == "durak_mesafe":
            if v <= 100:
                return "0-100 m"
            if v <= 200:
                return "101-200 m"
            if v <= 300:
                return "201-300 m"
            if v <= 400:
                return "301-400 m"
            return "401 m ve üzeri"

        return None

    def var_yok_grubu(self, deger):
        try:
            d = int(float(deger))
            if d == 1:
                return "Var"
            if d == 0:
                return "Yok"
        except Exception:
            pass
        return None

    def duzeltme_degiskenleri(self):
        return [
            ("alan", "Net alan"),
            ("yas", "Bina yaşı"),
            ("kat", "Bulunduğu kat"),
            ("asansor", "Asansör"),
            ("otopark", "Otopark"),
            ("marmaray_mesafe", "Marmaray mesafesi"),
            ("metro_mesafe", "Metro mesafesi"),
            ("havaalani_mesafe", "Havaalanı mesafesi"),
            ("durak_mesafe", "Durak mesafesi")
        ]

    def duzeltme_grubu(self, feature, degisken):
        if degisken == "alan":
            return self.alan_grubu(self.sayi_al(feature, "net_alan_m2"))
        if degisken == "yas":
            return self.yas_grubu(self.sayi_al(feature, "bina_yasi"))
        if degisken == "kat":
            return self.kat_grubu(self.sayi_al(feature, "bulundugu_kat"))
        if degisken in ["asansor", "otopark"]:
            return self.var_yok_grubu(self.sayi_al(feature, degisken, -1))
        if degisken in ["marmaray_mesafe", "metro_mesafe", "havaalani_mesafe", "durak_mesafe"]:
            return self.mesafe_grubu(self.sayi_al(feature, degisken), degisken)
        return None

    def emsal_hesapla_temel(self, f):
        satis_fiyati = self.sayi_al(f, "satis_fiyati")
        alan = self.sayi_al(f, "net_alan_m2")
        tarih = self.tarih_parse(f["satis_tarihi"]) if self.alan_var_mi(f, "satis_tarihi") else None

        if satis_fiyati <= 0 or alan <= 0 or tarih is None:
            return None

        duzeltilmis_fiyat = self.fiyat_reel(satis_fiyati, tarih)

        if duzeltilmis_fiyat is None or duzeltilmis_fiyat <= 0:
            return None

        ham_m2 = satis_fiyati / alan
        guncel_m2 = duzeltilmis_fiyat / alan

        return {
            "feature": f,
            "satis_fiyati": satis_fiyati,
            "satis_tarihi": tarih,
            "alan": alan,
            "ham_m2": ham_m2,
            "duzeltilmis_fiyat": duzeltilmis_fiyat,
            "guncel_m2": guncel_m2
        }

    def duzeltme_baz_verisi(self, layer, hedef, ayar, emsaller=None):

        baz_veri = []

        if emsaller is not None:
            # Önce konu taşınmaz, sonra filtre sonucu bulunan emsaller kullanılır.
            adaylar = [hedef] + list(emsaller)
            gorulen_idler = set()

            for f in adaylar:
                try:
                    fid = f.id()
                except Exception:
                    fid = id(f)

                if fid in gorulen_idler:
                    continue
                gorulen_idler.add(fid)

                if not self.veri_gecerli_mi(f):
                    continue

                baz_veri.append(f)

            return baz_veri

        # Geriye dönük kullanım için eski davranış korunur.
        for f in layer.getFeatures():
            if f.id() == hedef.id():
                continue
            if not self.veri_gecerli_mi(f):
                continue
            if self.metin_al(f, "mahalle") != ayar["mahalle"]:
                continue
            if self.oda_kodu(f) not in ayar["secili_oda_kodlari"]:
                continue

            baz_veri.append(f)

        return baz_veri

    def duzeltme_ortalamalari_hazirla(self, layer, hedef, ayar, emsaller=None):

        baz_veri = self.duzeltme_baz_verisi(layer, hedef, ayar, emsaller)
        sonuc = {}

        for degisken, etiket in self.duzeltme_degiskenleri():
            gruplar = {}

            for f in baz_veri:
                temel = self.emsal_hesapla_temel(f)
                if temel is None:
                    continue

                grup = self.duzeltme_grubu(f, degisken)
                if grup is None:
                    continue

                if grup not in gruplar:
                    gruplar[grup] = {"adet": 0, "toplam": 0.0, "ortalama": 0.0}

                gruplar[grup]["adet"] += 1
                gruplar[grup]["toplam"] += temel["ham_m2"]

            for grup in gruplar:
                if gruplar[grup]["adet"] > 0:
                    gruplar[grup]["ortalama"] = gruplar[grup]["toplam"] / gruplar[grup]["adet"]

            sonuc[degisken] = {"etiket": etiket, "gruplar": gruplar}

        return sonuc

    def duzeltme_tutari(self, hedef, emsal, degisken, ortalamalar):

        hedef_grup = self.duzeltme_grubu(hedef, degisken)
        emsal_grup = self.duzeltme_grubu(emsal, degisken)
        hedef_alan = self.sayi_al(hedef, "net_alan_m2")

        if hedef_grup is None or emsal_grup is None:
            return 0.0, hedef_grup, emsal_grup, "Grup bilgisi yok", None, None

        if hedef_grup == emsal_grup:
            return 0.0, hedef_grup, emsal_grup, "Aynı grup", None, None

        degisken_bilgi = ortalamalar.get(degisken, {}) if ortalamalar else {}
        gruplar = degisken_bilgi.get("gruplar", {})
        hedef_istatistik = gruplar.get(hedef_grup)
        emsal_istatistik = gruplar.get(emsal_grup)

        if hedef_istatistik is None or emsal_istatistik is None:
            return 0.0, hedef_grup, emsal_grup, "Ortalama bulunamadı", None, None

        hedef_ortalama = hedef_istatistik.get("ortalama", 0)
        emsal_ortalama = emsal_istatistik.get("ortalama", 0)

        if hedef_ortalama <= 0 or emsal_ortalama <= 0 or hedef_alan <= 0:
            return 0.0, hedef_grup, emsal_grup, "Geçersiz ortalama", hedef_ortalama, emsal_ortalama

        tutar = (hedef_ortalama - emsal_ortalama) * hedef_alan
        return tutar, hedef_grup, emsal_grup, "Uygulandı", hedef_ortalama, emsal_ortalama

    def emsal_hesapla(self, f, hedef=None, duzeltme_ortalamalari=None):
        temel = self.emsal_hesapla_temel(f)
        if temel is None:
            return None

        toplam_duzeltme_tutari = 0.0
        detaylar = []

        if hedef is not None and duzeltme_ortalamalari is not None:
            for degisken, etiket in self.duzeltme_degiskenleri():
                tutar, hedef_grup, emsal_grup, durum, hedef_ortalama, emsal_ortalama = self.duzeltme_tutari(
                    hedef, f, degisken, duzeltme_ortalamalari
                )
                toplam_duzeltme_tutari += tutar
                detaylar.append({
                    "degisken": degisken,
                    "etiket": etiket,
                    "konu_grup": hedef_grup,
                    "emsal_grup": emsal_grup,
                    "konu_ortalama_m2": hedef_ortalama,
                    "emsal_ortalama_m2": emsal_ortalama,
                    "duzeltme_tutari": tutar,
                    "durum": durum
                })

        ozellik_duzeltilmis_satis_fiyati = temel["satis_fiyati"] + toplam_duzeltme_tutari

        # Özellik düzeltmesi sonrası fiyat sıfır veya negatif olursa hesap güvenilir değildir.
        if ozellik_duzeltilmis_satis_fiyati <= 0:
            return None

        tufe_guncellenmis_duzeltilmis_deger = self.fiyat_reel(
            ozellik_duzeltilmis_satis_fiyati,
            temel["satis_tarihi"]
        )

        if tufe_guncellenmis_duzeltilmis_deger is None or tufe_guncellenmis_duzeltilmis_deger <= 0:
            return None

        hedef_alan = self.sayi_al(hedef, "net_alan_m2") if hedef is not None else temel["alan"]
        if hedef_alan <= 0:
            hedef_alan = temel["alan"]

        temel["toplam_duzeltme_tutari"] = toplam_duzeltme_tutari
        temel["ozellik_duzeltilmis_satis_fiyati"] = ozellik_duzeltilmis_satis_fiyati
        temel["tufe_guncellenmis_duzeltilmis_deger"] = tufe_guncellenmis_duzeltilmis_deger
        temel["duzeltilmis_emsal_deger"] = tufe_guncellenmis_duzeltilmis_deger
        temel["duzeltilmis_m2"] = tufe_guncellenmis_duzeltilmis_deger / hedef_alan
        temel["duzeltme_detaylari"] = detaylar
        return temel

    def duzeltme_detay_hucre(self, sonuc, degisken):

        detaylar = sonuc.get("duzeltme_detaylari", [])
        for d in detaylar:
            if d.get("degisken") == degisken:
                tutar = d.get("duzeltme_tutari", 0.0)
                durum = d.get("durum", "")
                if durum == "Aynı grup" or abs(tutar) < 0.5:
                    return "0 TL"
                return f"{tutar:,.0f} TL"
        return "-"

    # ---------------------------------------------------------
    # PDF RAPORU İÇİN EN YAKIN EMSAL SEÇİMİ
    # ---------------------------------------------------------
    def emsal_yakinlik_puani(self, f, hedef):
 
        puan = 0.0

        hedef_alan = self.sayi_al(hedef, "net_alan_m2")
        emsal_alan = self.sayi_al(f, "net_alan_m2")

        if hedef_alan > 0 and emsal_alan > 0:
            puan += abs(emsal_alan - hedef_alan) / hedef_alan * 10.0

        puan += abs(self.sayi_al(f, "bulundugu_kat") - self.sayi_al(hedef, "bulundugu_kat")) * 0.50
        puan += abs(self.sayi_al(f, "bina_yasi") - self.sayi_al(hedef, "bina_yasi")) * 0.20

        # Oda tipi farklıysa raporda biraz geriye düşsün.
        if self.oda_kodu(f) != self.oda_kodu(hedef):
            puan += 3.0

        # Var/yok özellikler farklıysa küçük ceza verilir.
        for alan in ["asansor", "otopark", "sehir_manz", "doga_manz", "gol_manz", "bogaz_manz"]:
            if int(self.sayi_al(f, alan, -1)) != int(self.sayi_al(hedef, alan, -1)):
                puan += 1.0

        return puan

    def html_escape(self, deger):
        s = str(deger)
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
        )

    def pdf_raporu_olustur(self, layer, hedef, ayar):
        emsaller = self.emsalleri_bul(layer, hedef, ayar)
        duzeltme_ortalamalari = self.duzeltme_ortalamalari_hazirla(layer, hedef, ayar, emsaller)

        hesap_sonuclari = []
        for f in emsaller:
            sonuc = self.emsal_hesapla(f, hedef, duzeltme_ortalamalari)
            if sonuc is not None:
                sonuc["yakinlik_puani"] = self.emsal_yakinlik_puani(f, hedef)
                hesap_sonuclari.append(sonuc)

        hedef_alan = self.sayi_al(hedef, "net_alan_m2")
        hedef_oda = self.oda_etiketi_from_kod(self.oda_kodu(hedef))
        hedef_mahalle = self.metin_al(hedef, "mahalle")

        secili_oda_etiketleri = [
            self.oda_etiketi_from_kod(k) for k in ayar["secili_oda_kodlari"]
        ]

        if len(hesap_sonuclari) == 0:
            return """
            <html><body>
            <h2>Değerleme Sonuç Raporu</h2>
            <p>Seçilen filtrelerle hesaplanabilir emsal bulunamadı.</p>
            </body></html>
            """

        degerler = [s["tufe_guncellenmis_duzeltilmis_deger"] for s in hesap_sonuclari]
        tahmini_deger = sum(degerler) / len(degerler)
        ortalama_m2 = tahmini_deger / hedef_alan if hedef_alan > 0 else 0
        en_dusuk = min(degerler)
        en_yuksek = max(degerler)

        # Rapor tablosunda her zaman en yakın en fazla 5 emsal gösterilir.
        rapor_emsalleri = sorted(
            hesap_sonuclari,
            key=lambda s: s["yakinlik_puani"]
        )[:5]

        def fbool(feature, field):
            return self.evet_hayir(self.sayi_al(feature, field, -1)) if self.alan_var_mi(feature, field) else "-"

        def fnum(feature, field, suffix="", decimals=0):
            if not self.alan_var_mi(feature, field):
                return "-"
            try:
                val = float(str(feature[field]).replace(",", "."))
                if decimals == 0:
                    return f"{val:,.0f}{suffix}"
                return f"{val:,.{decimals}f}{suffix}"
            except Exception:
                return self.html_escape(feature[field])

        def ftext(feature, field):
            if not self.alan_var_mi(feature, field):
                return "-"
            if field == "oda_sayisi":
                return self.oda_etiketi_from_kod(self.oda_kodu(feature))
            if field == "satis_tarihi":
                t = self.tarih_parse(feature[field])
                return t.strftime('%Y-%m-%d') if t else "-"
            val = feature[field]
            return "-" if val in [None, ""] else self.html_escape(val)

        def hedef_hucre(row_key):
            if row_key == "niteligi":
                return "Konut"
            if row_key == "mahalle":
                return self.html_escape(hedef_mahalle)
            if row_key == "oda":
                return self.html_escape(hedef_oda)
            if row_key == "alan":
                return f"{hedef_alan:,.2f} m²"
            if row_key == "kat":
                return fnum(hedef, "bulundugu_kat")
            if row_key == "yas":
                return fnum(hedef, "bina_yasi")
            if row_key == "asansor":
                return fbool(hedef, "asansor")
            if row_key == "otopark":
                return fbool(hedef, "otopark")
            if row_key == "sehir":
                return fbool(hedef, "sehir_manz")
            if row_key == "doga":
                return fbool(hedef, "doga_manz")
            if row_key == "gol":
                return fbool(hedef, "gol_manz")
            if row_key == "bogaz":
                return fbool(hedef, "bogaz_manz")
            if row_key == "kuzey":
                return fbool(hedef, "kuzey_cephe")
            if row_key == "guney":
                return fbool(hedef, "guney_cephe")
            if row_key == "dogu":
                return fbool(hedef, "dogu_cephe")
            if row_key == "bati":
                return fbool(hedef, "bati_cephe")
            if row_key == "marmaray":
                return fnum(hedef, "marmaray_mesafe", " m", 2)
            if row_key == "metro":
                return fnum(hedef, "metro_mesafe", " m", 2)
            if row_key == "havaalani":
                return fnum(hedef, "havaalani_mesafe", " m", 2)
            if row_key == "durak":
                return fnum(hedef, "durak_mesafe", " m", 2)
            if row_key == "tarih":
                return ftext(hedef, "satis_tarihi")
            if row_key == "fiyat":
                return fnum(hedef, "satis_fiyati", " TL", 0)
            if row_key == "duzeltilmis":
                return "-"
            if row_key == "guncel_m2":
                return "-"
            if row_key == "toplam_duzeltme_tutari":
                return "-"
            if row_key == "ozellik_duzeltilmis":
                return "-"
            if row_key == "tufe_guncellenmis_duzeltilmis":
                return "-"
            if row_key == "duzeltilmis_m2":
                return "-"
            if row_key.startswith("duz_"):
                return "-"
            return "-"

        def emsal_hucre(sonuc, row_key):
            f = sonuc["feature"]
            if row_key == "niteligi":
                return "Konut"
            if row_key == "mahalle":
                return self.html_escape(self.metin_al(f, "mahalle"))
            if row_key == "oda":
                return self.html_escape(self.oda_etiketi_from_kod(self.oda_kodu(f)))
            if row_key == "alan":
                return f"{sonuc['alan']:,.2f} m²"
            if row_key == "kat":
                return fnum(f, "bulundugu_kat")
            if row_key == "yas":
                return fnum(f, "bina_yasi")
            if row_key == "asansor":
                return fbool(f, "asansor")
            if row_key == "otopark":
                return fbool(f, "otopark")
            if row_key == "sehir":
                return fbool(f, "sehir_manz")
            if row_key == "doga":
                return fbool(f, "doga_manz")
            if row_key == "gol":
                return fbool(f, "gol_manz")
            if row_key == "bogaz":
                return fbool(f, "bogaz_manz")
            if row_key == "kuzey":
                return fbool(f, "kuzey_cephe")
            if row_key == "guney":
                return fbool(f, "guney_cephe")
            if row_key == "dogu":
                return fbool(f, "dogu_cephe")
            if row_key == "bati":
                return fbool(f, "bati_cephe")
            if row_key == "marmaray":
                return fnum(f, "marmaray_mesafe", " m", 2)
            if row_key == "metro":
                return fnum(f, "metro_mesafe", " m", 2)
            if row_key == "havaalani":
                return fnum(f, "havaalani_mesafe", " m", 2)
            if row_key == "durak":
                return fnum(f, "durak_mesafe", " m", 2)
            if row_key == "tarih":
                return sonuc['satis_tarihi'].strftime('%Y-%m-%d')
            if row_key == "fiyat":
                return f"{sonuc['satis_fiyati']:,.0f} TL"
            if row_key == "duzeltilmis":
                return f"{sonuc['duzeltilmis_fiyat']:,.0f} TL"
            if row_key == "guncel_m2":
                return f"{sonuc['guncel_m2']:,.0f} TL/m²"
            if row_key == "toplam_duzeltme_tutari":
                return f"{sonuc.get('toplam_duzeltme_tutari', 0.0):,.0f} TL"
            if row_key == "ozellik_duzeltilmis":
                return f"{sonuc.get('ozellik_duzeltilmis_satis_fiyati', sonuc['satis_fiyati']):,.0f} TL"
            if row_key == "tufe_guncellenmis_duzeltilmis":
                return f"{sonuc.get('tufe_guncellenmis_duzeltilmis_deger', sonuc['duzeltilmis_fiyat']):,.0f} TL"
            if row_key == "duzeltilmis_m2":
                return f"{sonuc.get('duzeltilmis_m2', sonuc['guncel_m2']):,.0f} TL/m²"
            if row_key.startswith("duz_"):
                return self.duzeltme_detay_hucre(sonuc, row_key.replace("duz_", "", 1))
            return "-"

        row_defs = [
            ("Niteliği", "niteligi"),
            ("Mahalle", "mahalle"),
            ("Oda Tipi", "oda"),
            ("Net Alan (m²)", "alan"),
            ("Net Alan Düzeltmesi", "duz_alan"),
            ("Bulunduğu Kat", "kat"),
            ("Kat Düzeltmesi", "duz_kat"),
            ("Bina Yaşı", "yas"),
            ("Bina Yaşı Düzeltmesi", "duz_yas"),
            ("Asansör", "asansor"),
            ("Asansör Düzeltmesi", "duz_asansor"),
            ("Otopark", "otopark"),
            ("Otopark Düzeltmesi", "duz_otopark"),
            ("Şehir Manzarası", "sehir"),
            ("Doğa Manzarası", "doga"),
            ("Göl Manzarası", "gol"),
            ("Boğaz Manzarası", "bogaz"),
            ("Kuzey Cephe", "kuzey"),
            ("Güney Cephe", "guney"),
            ("Doğu Cephe", "dogu"),
            ("Batı Cephe", "bati"),
            ("Marmaray Mesafesi (m)", "marmaray"),
            ("Marmaray Düzeltmesi", "duz_marmaray_mesafe"),
            ("Metro Mesafesi (m)", "metro"),
            ("Metro Düzeltmesi", "duz_metro_mesafe"),
            ("Havaalanı Mesafesi (m)", "havaalani"),
            ("Havaalanı Düzeltmesi", "duz_havaalani_mesafe"),
            ("Durak Mesafesi (m)", "durak"),
            ("Durak Düzeltmesi", "duz_durak_mesafe"),
            ("Satış Tarihi", "tarih"),
            ("Satış Fiyatı", "fiyat"),
            ("TÜFE Düzeltilmiş Fiyat", "duzeltilmis"),
            ("TÜFE Güncel m² Birim Fiyatı", "guncel_m2"),
            ("Toplam Düzeltme Tutarı", "toplam_duzeltme_tutari"),
            ("Özelliklere Göre Düzeltilmiş Satış Fiyatı", "ozellik_duzeltilmis"),
            ("TÜFE Güncellenmiş Düzeltilmiş Değer", "tufe_guncellenmis_duzeltilmis"),
            ("Düzeltilmiş m² Birim Fiyatı", "duzeltilmis_m2"),
        ]

        header_cells = '<th class="ozellik" width="20%">Özellikleri</th><th width="13%">Konu Taşınmaz</th>'
        for i in range(len(rapor_emsalleri)):
            header_cells += f'<th width="13%">Emsal {i+1}</th>'

        # Uzun karşılaştırma tablosu tek parça olduğunda PDF sayfa geçişlerinde
        # satırlar bölünebiliyor. Bu nedenle rapor daha temiz görünsün diye
        # tablo bölümlere ayrılmıştır.
        section_defs = [
            ("Temel Özellikler", [
                ("Niteliği", "niteligi"),
                ("Mahalle", "mahalle"),
                ("Oda Tipi", "oda"),
                ("Net Alan (m²)", "alan"),
                ("Net Alan Düzeltmesi", "duz_alan"),
                ("Bulunduğu Kat", "kat"),
                ("Kat Düzeltmesi", "duz_kat"),
                ("Bina Yaşı", "yas"),
                ("Bina Yaşı Düzeltmesi", "duz_yas"),
            ]),
            ("Donatı, Manzara ve Cephe Özellikleri", [
                ("Asansör", "asansor"),
                ("Asansör Düzeltmesi", "duz_asansor"),
                ("Otopark", "otopark"),
                ("Otopark Düzeltmesi", "duz_otopark"),
                ("Şehir Manzarası", "sehir"),
                ("Doğa Manzarası", "doga"),
                ("Göl Manzarası", "gol"),
                ("Boğaz Manzarası", "bogaz"),
                ("Kuzey Cephe", "kuzey"),
                ("Güney Cephe", "guney"),
                ("Doğu Cephe", "dogu"),
                ("Batı Cephe", "bati"),
            ]),
            ("Ulaşım ve Çevresel Mesafeler", [
                ("Marmaray Mesafesi (m)", "marmaray"),
                ("Marmaray Düzeltmesi", "duz_marmaray_mesafe"),
                ("Metro Mesafesi (m)", "metro"),
                ("Metro Düzeltmesi", "duz_metro_mesafe"),
                ("Havaalanı Mesafesi (m)", "havaalani"),
                ("Havaalanı Düzeltmesi", "duz_havaalani_mesafe"),
                ("Durak Mesafesi (m)", "durak"),
                ("Durak Düzeltmesi", "duz_durak_mesafe"),
            ]),
            ("Satış ve Değer Hesabı", [
                ("Satış Tarihi", "tarih"),
                ("Satış Fiyatı", "fiyat"),
                ("TÜFE Düzeltilmiş Fiyat", "duzeltilmis"),
                ("TÜFE Güncel m² Birim Fiyatı", "guncel_m2"),
                ("Toplam Düzeltme Tutarı", "toplam_duzeltme_tutari"),
                ("Özelliklere Göre Düzeltilmiş Satış Fiyatı", "ozellik_duzeltilmis"),
                ("TÜFE Güncellenmiş Düzeltilmiş Değer", "tufe_guncellenmis_duzeltilmis"),
                ("Düzeltilmiş m² Birim Fiyatı", "duzeltilmis_m2"),
            ]),
        ]

        def karsilastirma_tablosu_olustur(baslik, satirlar):
            body = ''
            for row_label, row_key in satirlar:
                row_html = f'<tr><td class="ozellik">{self.html_escape(row_label)}</td>'
                row_html += f'<td>{hedef_hucre(row_key)}</td>'
                for sonuc in rapor_emsalleri:
                    row_html += f'<td>{emsal_hucre(sonuc, row_key)}</td>'
                row_html += '</tr>'
                body += row_html

            # QGIS QTextDocument bazen başlığı sayfa sonunda bırakıp tabloyu
            # sonraki sayfaya atabiliyor. Ulaşım tablosu genelde ilk sayfaya
            # sığmadığı için bu bölümü bilinçli olarak yeni sayfadan başlatıyoruz.
            ek_sinif = ' force-new-page' if baslik == 'Ulaşım ve Çevresel Mesafeler' else ''

            return f'''
<div class="subsection-block{ek_sinif}">
    <div class="subsection-title">{self.html_escape(baslik)}</div>
    <table class="compare" width="100%" cellspacing="0" cellpadding="0">
        <tr>{header_cells}</tr>
        {body}
    </table>
</div>
<div class="table-space">&nbsp;</div>
'''

        karsilastirma_tablolari = ''.join(
            karsilastirma_tablosu_olustur(baslik, satirlar)
            for baslik, satirlar in section_defs
        )

        filtre_ozeti = (
            f"Aynı mahalle şartı otomatik uygulanmıştır. Kullanılan filtreler: "
            f"oda tipi = {self.html_escape(', '.join(secili_oda_etiketleri))}; "
            f"net alan = {ayar['min_alan']:.2f} - {ayar['max_alan']:.2f} m²; "
            f"kat = {ayar['min_kat']:.0f} - {ayar['max_kat']:.0f}; "
            f"bina yaşı = {ayar['min_yas']:.0f} - {ayar['max_yas']:.0f}; "
            f"asansör = {self.filtre_deger_yaz(ayar['asansor'])}; "
            f"otopark = {self.filtre_deger_yaz(ayar['otopark'])}; "
            f"şehir manzarası = {self.filtre_deger_yaz(ayar['sehir_manz'])}; "
            f"doğa manzarası = {self.filtre_deger_yaz(ayar['doga_manz'])}; "
            f"göl manzarası = {self.filtre_deger_yaz(ayar['gol_manz'])}; "
            f"boğaz manzarası = {self.filtre_deger_yaz(ayar['bogaz_manz'])}."
        )

        rapora_giren = len(rapor_emsalleri)

        return f"""
<html>
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: Arial, sans-serif;
    font-size: 7.2pt;
    color: #222;
    margin: 0;
    padding: 0;
}}
.hdr {{
    text-align: center;
}}
.hdr h1 {{
    margin: 0;
    padding: 0;
    font-size: 14pt;
    font-weight: bold;
}}
.hdr .sub {{
    margin-top: 6px;
    font-size: 9pt;
    color: #555;
}}
.title-space {{
    height: 8px;
}}
.section-space-top {{
    height: 10px;
}}
.section-space-bottom {{
    height: 6px;
}}
.summary {{
    border-collapse: collapse;
    width: 100%;
}}
.summary td {{
    border: 1px solid #cfcfcf;
    padding: 5px 6px;
    font-size: 7.0pt;
}}
.summary .label {{
    background: #e9eef3;
    font-weight: bold;
}}
.big-value {{
    font-size: 7.0pt;
    font-weight: bold;
    color: #000;
}}
.section-title {{
    font-size: 9.5pt;
    font-weight: bold;
    color: #d56f16;
}}
.compare {{
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;
    page-break-inside: avoid;
}}
.compare tr {{
    page-break-inside: avoid;
}}
.compare th, .compare td {{
    border: 1px solid #ffffff;
    padding: 2px 2px;
    vertical-align: top;
    word-wrap: break-word;
    font-size: 6.2pt;
    line-height: 1.08;
}}
.compare th {{
    background: #b9cedf;
    font-weight: bold;
    text-align: center;
}}
.compare td {{
    background: #dbe5f1;
}}
.compare .ozellik {{
    background: #aec4d7;
    font-weight: bold;
}}

.subsection-block {{
    page-break-inside: avoid;
    break-inside: avoid;
}}
.force-new-page {{
    page-break-before: always;
    break-before: page;
}}
.subsection-title {{
    margin-top: 7px;
    margin-bottom: 3px;
    font-size: 8.0pt;
    font-weight: bold;
    color: #333;
    page-break-after: avoid;
    break-after: avoid;
}}
.table-space {{
    height: 5px;
}}
</style>
</head>
<body>
<div class="hdr">
    <h1>DEĞERLEME SONUÇ RAPORU</h1>
    <div class="sub">Karşılaştırma Yöntemi - Emsal Analizi</div>
</div>

<div class="title-space">&nbsp;</div>

<table class="summary" width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td class="label">Konu Taşınmaz Mahallesi</td>
        <td>{self.html_escape(hedef_mahalle)}</td>
        <td class="label">Konu Taşınmaz Oda Tipi</td>
        <td>{self.html_escape(hedef_oda)}</td>
    </tr>
    <tr>
        <td class="label">Konu Taşınmaz Net Alanı</td>
        <td>{hedef_alan:,.2f} m²</td>
        <td class="label">Hesaplanabilir Emsal Sayısı</td>
        <td>{len(hesap_sonuclari)}</td>
    </tr>
    <tr>
        <td class="label">Raporda Gösterilen Emsal Sayısı</td>
        <td>{rapora_giren}</td>
        <td class="label">Ortalama Düzeltilmiş m² Birim Fiyatı</td>
        <td>{ortalama_m2:,.0f} TL/m²</td>
    </tr>
    <tr>
        <td class="label">En Düşük Düzeltilmiş Değer</td>
        <td>{en_dusuk:,.0f} TL</td>
        <td class="label">En Yüksek Düzeltilmiş Değer</td>
        <td>{en_yuksek:,.0f} TL</td>
    </tr>
    <tr>
        <td class="label">Tahmini Değer</td>
        <td colspan="3" class="big-value">{tahmini_deger:,.0f} TL</td>
    </tr>
</table>

<div class="section-space-top">&nbsp;</div>
<div class="section-title">Emsal Analizi</div>
<div class="section-space-bottom">&nbsp;</div>

{karsilastirma_tablolari}


</body>
</html>
"""

    # ---------------------------------------------------------
    # RAPOR
    # ---------------------------------------------------------
    def degerleme_raporu(self, layer, hedef, ayar):
        emsaller = self.emsalleri_bul(layer, hedef, ayar)
        duzeltme_ortalamalari = self.duzeltme_ortalamalari_hazirla(layer, hedef, ayar, emsaller)

        hesap_sonuclari = []
        for f in emsaller:
            sonuc = self.emsal_hesapla(f, hedef, duzeltme_ortalamalari)
            if sonuc is not None:
                hesap_sonuclari.append(sonuc)

        hedef_alan = self.sayi_al(hedef, "net_alan_m2")
        hedef_oda_kod = self.oda_kodu(hedef)
        hedef_oda = self.oda_etiketi_from_kod(hedef_oda_kod)
        hedef_mahalle = self.metin_al(hedef, "mahalle")

        secili_oda_etiketleri = [
            self.oda_etiketi_from_kod(k) for k in ayar["secili_oda_kodlari"]
        ]

        filtre_metni = (
            f"Mahalle: {ayar['mahalle']}\n"
            f"Seçilen oda tipleri: {', '.join(secili_oda_etiketleri)}\n"
            f"Net alan aralığı: {ayar['min_alan']:.2f} - {ayar['max_alan']:.2f} m²\n"
            f"Bulunduğu kat aralığı: {ayar['min_kat']:.0f} - {ayar['max_kat']:.0f}\n"
            f"Bina yaşı aralığı: {ayar['min_yas']:.0f} - {ayar['max_yas']:.0f}\n"
            f"Asansör: {self.filtre_deger_yaz(ayar['asansor'])}\n"
            f"Otopark: {self.filtre_deger_yaz(ayar['otopark'])}\n"
            f"Şehir manzarası: {self.filtre_deger_yaz(ayar['sehir_manz'])}\n"
            f"Doğa manzarası: {self.filtre_deger_yaz(ayar['doga_manz'])}\n"
            f"Göl manzarası: {self.filtre_deger_yaz(ayar['gol_manz'])}\n"
            f"Boğaz manzarası: {self.filtre_deger_yaz(ayar['bogaz_manz'])}"
        )

        if len(hesap_sonuclari) == 0:
            return (
                "KARŞILAŞTIRMA YÖNTEMİ SONUCU\n"
                "============================\n\n"
                "Seçilen filtrelerle hesaplanabilir emsal bulunamadı.\n\n"
                "KONU TAŞINMAZ\n"
                "-------------\n"
                f"Mahalle: {hedef_mahalle}\n"
                f"Oda Tipi: {hedef_oda}\n"
                f"Net Alan: {hedef_alan:.2f} m²\n\n"
                "SEÇİLEN FİLTRELER\n"
                "-----------------\n"
                f"{filtre_metni}\n\n"
                "Öneri: Net alan, kat veya bina yaşı aralığını genişletin; bazı özellikleri 'Farketmez' yapmayı deneyin."
            )

        degerler = [s["tufe_guncellenmis_duzeltilmis_deger"] for s in hesap_sonuclari]
        tahmini_deger = sum(degerler) / len(degerler)
        ortalama_m2 = tahmini_deger / hedef_alan if hedef_alan > 0 else 0

        en_dusuk = min(degerler)
        en_yuksek = max(degerler)

        detaylar = []
        for i, s in enumerate(hesap_sonuclari[:self.RAPORDA_GOSTERILECEK_EMSAL], start=1):
            f = s["feature"]
            detaylar.append(
                f"Emsal {i}\n"
                f"--------\n"
                f"Mahalle: {self.metin_al(f, 'mahalle')}\n"
                f"Oda Tipi: {self.oda_etiketi_from_kod(self.oda_kodu(f))}\n"
                f"Net Alan: {s['alan']:.2f} m²\n"
                f"Bulunduğu Kat: {self.sayi_al(f, 'bulundugu_kat'):.0f}\n"
                f"Bina Yaşı: {self.sayi_al(f, 'bina_yasi'):.0f}\n"
                f"Asansör: {self.evet_hayir(self.sayi_al(f, 'asansor'))}\n"
                f"Otopark: {self.evet_hayir(self.sayi_al(f, 'otopark'))}\n"
                f"Şehir Manzarası: {self.evet_hayir(self.sayi_al(f, 'sehir_manz'))}\n"
                f"Doğa Manzarası: {self.evet_hayir(self.sayi_al(f, 'doga_manz'))}\n"
                f"Göl Manzarası: {self.evet_hayir(self.sayi_al(f, 'gol_manz'))}\n"
                f"Boğaz Manzarası: {self.evet_hayir(self.sayi_al(f, 'bogaz_manz'))}\n"
                f"Satış Tarihi: {s['satis_tarihi'].strftime('%Y-%m-%d')}\n"
                f"Satış Fiyatı: {s['satis_fiyati']:,.0f} TL\n"
                f"Ham m²: {s['ham_m2']:,.0f} TL/m²\n"
                f"TÜFE Düzeltilmiş Fiyat: {s['duzeltilmis_fiyat']:,.0f} TL\n"
                f"Güncel m²: {s['guncel_m2']:,.0f} TL/m²\n"
                f"Toplam Düzeltme Tutarı: {s.get('toplam_duzeltme_tutari', 0.0):,.0f} TL\n"
                f"Özelliklere Göre Düzeltilmiş Satış Fiyatı: {s.get('ozellik_duzeltilmis_satis_fiyati', s['satis_fiyati']):,.0f} TL\n"
                f"TÜFE Güncellenmiş Düzeltilmiş Değer: {s.get('tufe_guncellenmis_duzeltilmis_deger', s['duzeltilmis_fiyat']):,.0f} TL\n"
                f"Düzeltilmiş m²: {s.get('duzeltilmis_m2', s['guncel_m2']):,.0f} TL/m²\n"
            )

        detay_metni = "\n".join(detaylar)

        if len(hesap_sonuclari) > self.RAPORDA_GOSTERILECEK_EMSAL:
            detay_metni += f"\n... Toplam {len(hesap_sonuclari)} emsal hesaplamaya dahil edildi."

        return f"""
<html>
<head>
<style>
body {{
    font-family: Arial, sans-serif;
    font-size: 7.5pt;
    color: #111;
}}
h2 {{
    margin-bottom: 6px;
}}
h3 {{
    margin-top: 18px;
    margin-bottom: 6px;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 3px;
}}
.info-table {{
    border-collapse: collapse;
    width: 100%;
}}
.info-table td {{
    padding: 4px 8px;
    vertical-align: top;
}}
.label {{
    font-weight: bold;
    width: 135px;
}}
.result-box {{
    margin-top: 12px;
    padding: 14px;
    border: 2px solid #222;
    background-color: #f5f5f5;
}}
.result-label {{
    font-size: 9pt;
    font-weight: bold;
}}
.result-value {{
    font-size: 20pt;
    font-weight: 900;
    color: #000;
}}
</style>
</head>
<body>

<h2>KARŞILAŞTIRMA YÖNTEMİ SONUCU</h2>

<h3>KONU TAŞINMAZ</h3>
<table class="info-table">
<tr><td class="label">Mahalle</td><td>{hedef_mahalle}</td></tr>
<tr><td class="label">Oda Tipi</td><td>{hedef_oda}</td></tr>
<tr><td class="label">Net Alan</td><td>{hedef_alan:.2f} m²</td></tr>
</table>

<h3>SEÇİLEN FİLTRELER</h3>
<table class="info-table">
<tr><td class="label">Mahalle</td><td>{ayar['mahalle']}</td></tr>
<tr><td class="label">Seçilen oda tipleri</td><td>{', '.join(secili_oda_etiketleri)}</td></tr>
<tr><td class="label">Net alan aralığı</td><td>{ayar['min_alan']:.2f} - {ayar['max_alan']:.2f} m²</td></tr>
<tr><td class="label">Bulunduğu kat aralığı</td><td>{ayar['min_kat']:.0f} - {ayar['max_kat']:.0f}</td></tr>
<tr><td class="label">Bina yaşı aralığı</td><td>{ayar['min_yas']:.0f} - {ayar['max_yas']:.0f}</td></tr>
<tr><td class="label">Asansör</td><td>{self.filtre_deger_yaz(ayar['asansor'])}</td></tr>
<tr><td class="label">Otopark</td><td>{self.filtre_deger_yaz(ayar['otopark'])}</td></tr>
<tr><td class="label">Şehir manzarası</td><td>{self.filtre_deger_yaz(ayar['sehir_manz'])}</td></tr>
<tr><td class="label">Doğa manzarası</td><td>{self.filtre_deger_yaz(ayar['doga_manz'])}</td></tr>
<tr><td class="label">Göl manzarası</td><td>{self.filtre_deger_yaz(ayar['gol_manz'])}</td></tr>
<tr><td class="label">Boğaz manzarası</td><td>{self.filtre_deger_yaz(ayar['bogaz_manz'])}</td></tr>
</table>

<h3>EMSAL SAYILARI</h3>
<table class="info-table">
<tr><td class="label">Filtreye uyan emsal sayısı</td><td>{len(emsaller)}</td></tr>
<tr><td class="label">Hesaplanabilir emsal sayısı</td><td>{len(hesap_sonuclari)}</td></tr>
</table>

<h3>DÜZELTİLMİŞ DEĞER ARALIĞI</h3>
<table class="info-table">
<tr><td class="label">En düşük düzeltilmiş değer</td><td>{en_dusuk:,.0f} TL</td></tr>
<tr><td class="label">En yüksek düzeltilmiş değer</td><td>{en_yuksek:,.0f} TL</td></tr>
<tr><td class="label">Ortalama düzeltilmiş m²</td><td>{ortalama_m2:,.0f} TL/m²</td></tr>
</table>

<div class="result-box">
<div class="result-label">TAHMİNİ DEĞER</div>
<div class="result-value">{tahmini_deger:,.0f} TL</div>
</div>

</body>
</html>
"""
