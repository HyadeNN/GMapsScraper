# Google Maps Scraper - Kapsamlı Proje Dokümantasyonu

## 📋 Proje Genel Bakış

**Google Maps Scraper**, Türkiye odaklı diş kliniklerini Google Places API ile scraping eden profesyonel bir uygulamadır. Python 3.11+ ile geliştirilmiş, UV package manager kullanmaktadır.

**Ana Amaç**: Google Places API kullanarak koordinatları sistemde var olan bölgelerden hedef sektör verilerini sistematik olarak toplamak.

**Versiyon**: 2.0

---

## 🏗️ Proje Mimarisi

### 3-Katmanlı Mimari

#### Core Katmanı (Ana İş Mantığı)
- `scraper.py` - Google Places API iletişimi
- `data_processor.py` - Veri dönüştürme ve işleme
- `storage.py` - Esnek depolama soyutlaması

#### Utils Katmanı (Yardımcı Araçlar)
- `grid_search.py` - Grid-tabanlı sistematik arama algoritması
- `logger.py` - Loglama yapılandırması
- `helpers.py` - Genel yardımcı fonksiyonlar
- `district_updater_ui.py` - İlçe güncelleme arayüzü

#### Config Katmanı (Konfigürasyon)
- `settings.py` - API anahtarları, varsayılan ayarlar, sabitler
- `locations.json` - Basit şehir-ilçe listesi (11 büyük şehir)
- `locationsV2.json` - Detaylı il-ilçe sözlüğü (tüm Türkiye)
- `turkey-geo.json` - En detaylı coğrafi veri (mahalle düzeyinde)

---

## 📁 Dizin Yapısı

```
GMapsScraper/
├── gmaps_scraper/                    # Ana uygulama paketi
│   ├── __init__.py                   # Paket başlatıcı
│   ├── __main__.py                   # Ana uygulama giriş noktası, CLI interface
│   ├── config/                       # Konfigürasyon dosyaları
│   │   ├── settings.py               # API anahtarları, varsayılan ayarlar
│   │   ├── locations.json            # Basit şehir-ilçe listesi
│   │   ├── locationsV2.json          # Detaylı il-ilçe sözlüğü
│   │   └── turkey-geo.json           # En detaylı coğrafi veri
│   ├── core/                         # Çekirdek iş mantığı
│   │   ├── scraper.py                # GooglePlacesScraper sınıfı
│   │   ├── data_processor.py         # DataProcessor sınıfı
│   │   └── storage.py                # Depolama soyutlaması
│   ├── utils/                        # Yardımcı araçlar
│   │   ├── grid_search.py            # Grid arama algoritması
│   │   ├── logger.py                 # Loglama yapılandırması
│   │   ├── helpers.py                # Genel yardımcı fonksiyonlar
│   │   └── district_updater_ui.py    # İlçe güncelleme arayüzü
│   └── data/                         # Çıktı veri klasörü
├── pyproject.toml                    # UV package manager konfigürasyonu
├── requirements.txt                  # Pip bağımlılıkları
├── README.md                         # Proje dokümantasyonu
├── .gitignore                        # Git ignore kuralları
├── test_*.py                         # Test dosyaları
├── update_districts.py               # İlçe güncelleme scripti
└── standalone_batch_to_excel.py      # Excel dönüştürme aracı
```

---

## 🔧 Bağımlılıklar

### Runtime Bağımlılıkları
- `requests` (>=2.31.0) - HTTP istekleri için
- `python-dotenv` (>=1.0.0) - Çevre değişkenleri için
- `tqdm` (>=4.66.1) - İlerleme çubuğu için
- `pymongo` (>=4.5.0) - MongoDB bağlantısı için
- `pandas` (>=2.0.3) - Veri işleme için

### Geliştirme Bağımlılıkları
- `pytest` (>=7.4.0) - Test framework
- `black` (>=23.0.0) - Kod formatı
- `ruff` (>=0.1.0) - Linter
- `mypy` (>=1.0.0) - Type checking
- `pytest-cov` (>=4.0.0) - Test coverage

---

## ⚙️ Konfigürasyon

### Settings.py Değişkenleri
```python
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')     # Google Maps API anahtarı
LANGUAGE = 'tr'                                # Dil ayarı
REGION = 'tr'                                  # Bölge ayarı
SEARCH_RADIUS = 15000                          # Varsayılan arama yarıçapı (metre)
REQUEST_DELAY = 1                              # API istekleri arası bekleme (saniye)
MAX_RETRIES = 3                                # Maksimum deneme sayısı
STORAGE_TYPE = 'json'                          # Depolama tipi (json/mongodb)
SEARCH_TERMS = ['dentist']                     # Arama terimleri
LOG_LEVEL = 'DEBUG'                            # Log seviyesi
```

### Lokasyon Dosyaları

#### locations.json
- **Yapı**: `cities[] -> {name, lat, lng, districts[{name, lat, lng}]}`
- **Kapsam**: 11 büyük şehir, İstanbul için 39 ilçe
- **Kullanım**: Hızlı prototipleme ve büyük şehir aramaları

#### locationsV2.json
- **Yapı**: `cities{} -> {şehir: {lat, lng, districts{ilçe: {lat, lng}}}}`
- **Kapsam**: Tüm Türkiye illeri ve ilçeleri
- **Kullanım**: Kapsamlı il/ilçe bazlı aramalar

#### turkey-geo.json
- **Yapı**: `[{Province, PlateNumber, Coordinates, Districts[{District, Coordinates, Towns[{Town, ZipCode, Neighbourhoods[]}]}]}]`
- **Kapsam**: Tüm iller, ilçeler, beldeler, mahalleler
- **Kullanım**: Mahalle düzeyinde detaylı aramalar

### Çevre Değişkenleri
```bash
GOOGLE_MAPS_API_KEY=your_api_key_here         # Zorunlu
MONGODB_URI=mongodb://localhost:27017         # Opsiyonel
MONGODB_DB=dental_clinics                     # MongoDB veritabanı adı
MONGODB_COLLECTION=places                     # MongoDB koleksiyon adı
LOG_LEVEL=DEBUG                               # Log seviyesi
LOG_FILE=./scraper.log                        # Log dosyası yolu
```

---

## 🎯 Ana Modüller

### 1. GooglePlacesScraper (`gmaps_scraper/core/scraper.py`)

**Amaç**: Google Places API ile iletişim ve veri çekme

**Ana Metodlar**:
- `__init__()` - API anahtarı ve batch konfigürasyonu
- `_make_request()` - HTTP istekleri, hata yönetimi, retry
- `search_places()` - Mekan araması, sayfalama desteği
- `get_place_details()` - Detaylı mekan bilgileri alma
- `fetch_places_with_details()` - Arama + detay alma + batch kayıt
- `_save_batch()` - Toplu veri kaydetme

**Özellikler**:
- Sayfalama desteği (max 3 sayfa/60 sonuç)
- Batch işleme (varsayılan 20 kayıt)
- Otomatik retry mekanizması
- API kotası aşım yönetimi

### 2. DataProcessor (`gmaps_scraper/core/data_processor.py`)

**Amaç**: Ham API verilerini yapılandırılmış formata dönüştürme

**Ana Metodlar**:
- `extract_place_data()` - Tek mekan verisi işleme
- `_extract_city_from_address()` - Adresten şehir çıkarımı
- `_extract_district_from_address()` - Adresten ilçe çıkarımı
- `_extract_postal_code()` - 5 haneli Türkiye posta kodu çıkarımı
- `_format_opening_hours()` - Çalışma saatleri formatı
- `process_places_data()` - Toplu veri işleme

**Çıktı Yapısı**:
```json
{
  "id": "Google Place ID",
  "name": "Mekan adı",
  "contact": {
    "phone": "Telefon",
    "website": "Web sitesi"
  },
  "location": {
    "address": "Adres",
    "city": "Şehir",
    "district": "İlçe",
    "postal_code": "Posta kodu",
    "latitude": "Enlem",
    "longitude": "Boylam"
  },
  "details": {
    "rating": "Puan",
    "user_ratings_total": "Değerlendirme sayısı",
    "price_level": "Fiyat seviyesi",
    "opening_hours": "Çalışma saatleri"
  },
  "metadata": {
    "retrieved_at": "Alınma zamanı",
    "search_term": "Arama terimi"
  }
}
```

### 3. Storage (`gmaps_scraper/core/storage.py`)

**Amaç**: Esnek veri depolama soyutlaması

**Sınıflar**: BaseStorage, JSONStorage, MongoDBStorage

**JSON Depolama**:
- Otomatik dosya isimlendirme
- UTF-8 kodlama
- Timestamp ekleme
- Dosya adı formatı: `dental_clinics_[şehir]_[ilçe]_[arama_terimi]_[timestamp]_batch_[sayı].json`

**MongoDB Depolama**:
- Toplu kayıt (bulk insert)
- Index desteği
- Duplicate kontrolü

### 4. Grid Search (`gmaps_scraper/utils/grid_search.py`)

**Amaç**: Geniş alanları sistematik olarak taramak için grid algoritması

**Ana Fonksiyonlar**:
- `haversine_distance()` - İki nokta arası mesafe hesaplama
- `calculate_lat_lon_distance()` - Yön ve mesafe ile yeni koordinat hesaplama
- `generate_grid_coordinates()` - Optimal grid noktaları oluşturma
- `grid_search_places()` - Grid noktalarında sistematik arama

**Algoritma Özellikleri**:
- Hexagonal packing benzeri yerleşim
- Arama yarıçapı × 1.5 nokta aralığı (örtüşme için)
- Zigzag düzen, satırlar kaydırılmış
- `seen_place_ids` set ile tekrar filtreleme

---

## 🚀 Ana Uygulama ve CLI

### Giriş Noktası
`gmaps_scraper/__main__.py`

### CLI Parametreleri
```bash
python -m gmaps_scraper [OPTIONS]

--config              Konum konfigürasyon dosyası
--city                Belirli şehir için arama
--district            Belirli ilçe için arama
--search-term         Özel arama terimi
--radius              Arama yarıçapı (metre, max 50000)
--skip-city-search    Şehir düzeyinde aramayı atla
--use-grid-search     Grid arama metodunu kullan
--grid-width          Grid alan genişliği (km)
--grid-height         Grid alan yüksekliği (km)
--batch-size          Toplu kayıt boyutu
```

### Çalışma Akışı
1. Komut satırı argümanları parse et
2. API anahtarı kontrolü
3. Konum verilerini yükle
4. Scraper, processor, storage başlat
5. Şehir/ilçe bazında arama yap
6. Veri işle ve kaydet
7. Sonuç raporla

---

## 🔍 Arama Stratejileri

### Normal Arama
- **Açıklama**: Tek merkez nokta etrafında arama
- **Maksimum yarıçap**: 50000 metre (50 km)
- **Sonuç limiti**: 20 per istek (max 3 sayfa = 60 toplam)
- **Kullanım**: Küçük alanlar veya belirli noktalar için

### Grid Search
- **Açıklama**: Sistematik grid tabanlı arama
- **Varsayılan alan**: 5km × 5km
- **Grid yarıçapı**: 800 metre per nokta
- **Nokta aralığı**: 1200 metre (800 × 1.5)
- **Kapsama**: Yaklaşık 49 nokta per 25 km²
- **Kullanım**: Geniş alanların kapsamlı taranması

---

## 📊 Veri Akışı

### Adım Adım İşlem
1. CLI parametreleri → ArgumentParser
2. API key kontrolü → .env dosyası
3. Lokasyon verisi → JSON dosyalarından
4. Arama stratejisi seçimi → Normal/Grid
5. GooglePlacesScraper.search_places() → API isteği
6. Her sonuç için get_place_details() → Detay bilgisi
7. DataProcessor.extract_place_data() → Veri yapılandırma
8. Batch kontrolü → 20 kayıt dolduğunda
9. Storage.save() → JSON/MongoDB'ye kayıt
10. Sonraki nokta/şehir/ilçe → Döngü devam

### Batch İşleme
- **Tetikleme koşulları**: Batch boyutu dolduğunda, arama bittiğinde, hata durumunda
- **Varsayılan boyut**: 20 kayıt
- **Bellek optimizasyonu**: Büyük veri setleri için bellek tasarrufu
- **Dosya isimlendirme**: Benzersiz timestamp ve batch numarası

---

## ⚠️ Hata Yönetimi

### Retry Mekanizması
- **Maksimum deneme**: 3
- **Bekleme deseni**: Exponential backoff (2s, 4s, 8s)
- **Özel durumlar**:
  - `OVER_QUERY_LIMIT`: 5x normal bekleme süresi
  - `INVALID_REQUEST`: Hemen başarısız olur
  - `REQUEST_DENIED`: API key kontrolü gerekir

### Hata Türleri
- **API Hataları**: OVER_QUERY_LIMIT, INVALID_REQUEST, REQUEST_DENIED, ZERO_RESULTS
- **Network Hataları**: ConnectionTimeout, RequestException
- **Veri Hataları**: MissingData, InvalidFormat

### Loglama
- **Seviyeler**: DEBUG, INFO, WARNING, ERROR
- **Hedefler**: Console, File (scraper.log)
- **Format**: Timestamp + Level + Module + Message

---

## 💡 Kullanım Örnekleri

### Temel Kullanım
```bash
python -m gmaps_scraper
# Tüm Türkiye'yi varsayılan ayarlarla tara
```

### Şehir Özelinde Arama
```bash
python -m gmaps_scraper --city 'İstanbul'
# Sadece İstanbul'u tara
```

### İlçe Özelinde Arama
```bash
python -m gmaps_scraper --city 'İstanbul' --district 'Kadıköy'
# İstanbul/Kadıköy'ü tara
```

### Grid Search
```bash
python -m gmaps_scraper --city 'İstanbul' --district 'Kadıköy' --use-grid-search --grid-width 10 --grid-height 10
# Kadıköy'de 10x10 km grid arama
```

### Özel Parametreler
```bash
python -m gmaps_scraper --search-term 'ortodontist' --radius 25000 --batch-size 50
# Özel arama terimi ve parametreler
```

### MongoDB Depolama
```bash
export STORAGE_TYPE=mongodb
export MONGODB_URI=mongodb://localhost:27017
python -m gmaps_scraper
# MongoDB'ye kaydetme
```

---

## 📁 Çıktı Formatları

### JSON Yapısı
- **Dosya isimlendirme**: `dental_clinics_[location]_[term]_[timestamp]_batch_[number].json`
- **Kodlama**: UTF-8
- **Yapı**: Place objelerinin dizisi

### MongoDB Yapısı
- **Veritabanı**: dental_clinics
- **Koleksiyon**: places
- **İndeksler**: place_id, city, district
- **Özellikler**: Bulk insert, Duplicate prevention

---

## ⚡ Performans Değerlendirmeleri

### API Limitleri
- **Google Places**: Günlük ve anlık limitler var
- **İstek gecikmesi**: 1 saniye arası bekleme önerisi
- **Batch boyutu**: 20 kayıt optimal performans için

### Bellek Kullanımı
- **Batch işleme**: Bellek tüketimini sınırlar
- **Duplicate kontrolü**: Set veri yapısı ile hızlı arama
- **Streaming**: Büyük veri setleri için akış işleme

### Network Optimizasyonu
- **Connection pooling**: Requests kütüphanesi ile
- **Retry stratejisi**: Exponential backoff
- **Timeout handling**: Uygun timeout değerleri

---

## 🧪 Test Yapısı

### Test Dosyaları
- `test_api.py` - API bağlantı ve yanıt testleri
- `test_grid_search.py` - Grid algoritması testleri
- `test_v2.py` - Diğer test senaryoları

### Test Framework
- **Ana framework**: pytest
- **Coverage**: pytest-cov ile

---

## 🛠️ Yardımcı Araçlar

- `update_districts.py` - İlçe verilerini güncelleme scripti
- `standalone_batch_to_excel.py` - JSON verilerini Excel'e dönüştürme
- `district_updater_ui.py` - İlçe güncelleme için UI arayüzü

---

## 🔄 Geliştirme İş Akışı

### Kurulum
```bash
1. uv sync                           # Bağımlılıkları yükle
2. .env dosyası oluştur              # Çevre değişkenlerini ayarla
3. GOOGLE_MAPS_API_KEY ayarla        # API anahtarını ekle
4. python -m gmaps_scraper --help    # Yardım menüsünü görüntüle
```

### Kod Kalitesi
```bash
black .                              # Kod formatı
ruff check .                         # Linting
mypy gmaps_scraper/                  # Type checking
pytest tests/                        # Testing
```

---

## 🚨 Yaygın Sorunlar ve Çözümler

### API Key Bulunamadı
- **Hata**: API key not found
- **Çözüm**: .env dosyasında GOOGLE_MAPS_API_KEY ayarla

### Kota Aşımı
- **Hata**: OVER_QUERY_LIMIT
- **Çözüm**: REQUEST_DELAY artır veya sonra dene

### Sonuç Bulunamadı
- **Hata**: ZERO_RESULTS
- **Çözüm**: Arama yarıçapını artır veya farklı terim kullan

### Depolama İzni
- **Hata**: Permission denied
- **Çözüm**: data/ klasörü izinlerini kontrol et

---

## 🚀 Deployment Notları

### Gereksinimler
- Python 3.11+
- uv package manager
- Google Maps API key
- MongoDB (opsiyonel)

### Ortam Ayarları
- **Production**: LOG_LEVEL=INFO, REQUEST_DELAY=2
- **Development**: LOG_LEVEL=DEBUG, REQUEST_DELAY=0.5
- **Testing**: LOG_LEVEL=WARNING, API_KEY=test_key

---

## 🔮 Gelecek Geliştirmeler

### Planlanan Özellikler
- Çoklu arama terimi desteği
- Elasticsearch entegrasyonu
- REST API sunucusu
- Web dashboard
- Zamanlanmış görevler
- Gerçek zamanlı veri güncelleme

---

## 📝 Sonuç

Bu dokümantasyon, Google Maps Scraper projesinin tüm yönlerini kapsamlı bir şekilde açıklamaktadır. Proje context'i temizlense veya yeniden başlatılsa bile, bu dokümantasyon referans alınarak projenin tüm detaylarına hakim olunabilir.