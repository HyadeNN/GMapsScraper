import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# API anahtarını .env dosyasından al
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

if not api_key:
    print("API anahtarı bulunamadı. Lütfen .env dosyasında GOOGLE_MAPS_API_KEY tanımlayın.")
    exit(1)

# Test parametreleri
test_queries = [
    "dentist",
    "diş hekimi",
    "dental clinic"
]

test_location = "41.0082,28.9784"  # İstanbul
test_radius = 10000

# Her sorgu için API'yi test et
for query in test_queries:
    print(f"\n----- '{query}' sorgusu için test -----")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'location': test_location,
        'radius': test_radius,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        print(f"API Yanıt Durumu: {data.get('status')}")

        if 'error_message' in data:
            print(f"Hata Mesajı: {data.get('error_message')}")

        if 'results' in data:
            results_count = len(data['results'])
            print(f"Sonuç Sayısı: {results_count}")

            if results_count > 0:
                first_result = data['results'][0]
                print(f"\nİlk Sonuç:")
                print(f"- İsim: {first_result.get('name')}")
                print(f"- Adres: {first_result.get('formatted_address')}")
                print(f"- Place ID: {first_result.get('place_id')}")
            else:
                print("Sonuç bulunamadı!")

    except requests.exceptions.RequestException as e:
        print(f"İstek Hatası: {str(e)}")

print("\nTüm testler tamamlandı.")