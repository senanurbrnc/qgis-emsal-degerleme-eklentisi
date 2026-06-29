# qgis-emsal-degerleme-eklentisi

![QGIS](https://img.shields.io/badge/QGIS-3.28%2B-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PostGIS](https://img.shields.io/badge/PostGIS-3.x-blue)
![Durum](https://img.shields.io/badge/Durum-Aktif-brightgreen)

Bu çalışma, QGIS platformu üzerinde emsal karşılaştırma yöntemine dayalı taşınmaz değerleme işlemlerini desteklemek amacıyla geliştirilmiş bir eklentidir. Eklenti; emsal filtreleme, TÜFE ile değer güncelleme, düzeltme faktörlerinin uygulanması ve değerleme raporu oluşturma süreçlerini kolaylaştırmayı amaçlamaktadır.

## Özellikler

- Emsal taşınmazların filtrelenmesi
- TÜFE verilerine göre satış değerlerinin güncellenmesi
- Net alan, bina yaşı, kat, asansör, otopark, çevresel mesafe ve manzara gibi değişkenlere göre düzeltme yapılması
- Konu taşınmaz için tahmini değer hesabı
- PDF formatında değerleme raporu oluşturma
- QGIS arayüzü üzerinden kullanıcı dostu işlem akışı

## Kullanılan Teknolojiler

- QGIS
- Python
- PyQGIS API
- PostgreSQL / PostGIS
- Qt Designer
- GitHub

## Kurulum

Projeyi bilgisayarınıza indirmek için:

```bash
git clone https://github.com/senanubrnc/qgis-emsal-degerleme-eklentisi.git
