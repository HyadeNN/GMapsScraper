# GMapsScraper

Bu proje, Google Places API kullanarak Türkiye'deki ağız ve diş sağlığı kliniklerinin veri toplanması için geliştirilmiştir.

## Kurulum

1. Projeyi klonlayın:
```
git clone [repository_url]
cd dental_clinics_scraper
```

2. Gerekli paketleri yükleyin:
```
pip install -r requirements.txt
```

3. `.env` dosyası oluşturun:
```
GOOGLE_MAPS_API_KEY=your_api_key_here
MONGODB_URI=mongodb://localhost:27017  # (isteğe bağlı)
```

## Kullanım

### Temel Kullanım

Tüm şehirler ve arama terimleri için veri toplamak:

```
python main.py
```

### Belirli bir şehir için veri toplamak:

```
python main.py --city "İstanbul"
```

### Belirli bir ilçe için veri toplamak:

```
python main.py --city "İstanbul" --district "Kadıköy"
```

### Belirli bir arama terimi kullanmak:

```
python main.py --search-term "diş kliniği"
```

### Arama yarıçapını değiştirmek:

```
python main.py --radius 10000
```

### Çıktı dizinini değiştirmek:

```
python main.py --output-dir "results"
```

## Çıktı Formatı

Veriler JSON formatında `data` dizinine kaydedilir. Her arama için ayrı bir dosya oluşturulur ve tüm veriler birleştirilmiş bir dosyada da saklanır.

JSON formatı şu şekildedir:

```json
{
  "id": "Google Place ID",
  "name": "Klinik Adı",
  "types": ["Kategori1", "Kategori2"],
  "contact": {
    "phone": "Telefon Numarası",
    "website": "Web Sitesi"
  },
  "location": {
    "address": "Tam Adres",
    "city": "Şehir",
    "district": "İlçe",
    "postal_code": "Posta Kodu",
    "latitude": 12.3456,
    "longitude": 34.5678
  },
  "details": {
    "rating": 4.5,
    "user_ratings_total": 125,
    "price_level": 2,
    "opening_hours": {
      "monday": ["09:00-18:00"],
      "tuesday": ["09:00-18:00"]
    }
  },
  "metadata": {
    "retrieved_at": "ISO DateTime",
    "search_term": "Arama Terimi"
  }
}
```

## Ek Bilgiler

- Google Places API'nin kullanım limitleri olduğunu unutmayın.
- Büyük veri setleri için işlem zaman alabilir.
- API kullanımı ücretlidir, görev boyunca kredi tüketimini izleyin.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

gmaps_scraper/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── locations.json
├── core/
│   ├── __init__.py
│   ├── scraper.py
│   ├── data_processor.py
│   └── storage.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── helpers.py
├── data/
│   └── .gitkeep
├── main.py
├── requirements.txt
└── README.md
