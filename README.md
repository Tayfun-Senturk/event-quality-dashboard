# Event Quality Dashboard https://github.com/Tayfun-Senturk/event-quality-dashboard

Bu proje, dijital ürünlerde oluşan event verilerinde veri kalitesi problemlerini izlemek ve basit anomali tespiti yapmak için geliştirilmiş web tabanlı bir dashboard uygulamasıdır.

Uygulamada gerçek şirket verisi kullanılmamıştır. Bunun yerine sentetik event verisi üretilmiş, bu veriye kontrollü olarak bazı bozulmalar eklenmiş ve ardından veri kalitesi metrikleri hesaplanmıştır. Eksik alan oranı, duplicate kayıt oranı, beklenmeyen değer sayısı ve event count gibi metrikler dashboard üzerinden görüntülenebilir.

Anomali tespiti için hareketli ortalama ve z-score yöntemleri kullanılmıştır. Proje, yüksek lisans dönem projesi kapsamında hazırlanmış çalışan bir MVP uygulamasıdır.

## Kullanılan Teknolojiler

- Backend: Python, FastAPI, SQLAlchemy
- Veritabanı: PostgreSQL
- Frontend: React, Vite
- Grafikler: Recharts
- Çalıştırma: Docker Compose

## Proje Yapısı

```text
backend/
  app/
    api/
    services/
    main.py
    models.py
    schemas.py
    database.py
  requirements.txt
  .env.example

frontend/
  src/
    api/
    components/
    pages/
    App.jsx
    main.jsx
  package.json

docker-compose.yml
README.md
```

## Kurulum ve Çalıştırma

### 1. PostgreSQL’i başlatma

Proje ana dizininde:

```powershell
docker compose up -d
```

PostgreSQL Docker üzerinden çalışır. Varsayılan bağlantı bilgileri `backend/.env.example` dosyasında yer almaktadır.

### 2. Backend kurulumu

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Backend adresi:

```text
http://localhost:8000
```

Swagger dokümantasyonu:

```text
http://localhost:8000/docs
```

### 3. Frontend kurulumu

Yeni bir terminal açıp:

```powershell
cd frontend
npm install
npm run dev
```

Frontend adresi:

```text
http://localhost:5173
```

## Demo Akışı

Uygulama açıldıktan sonra aşağıdaki sıra ile test edilebilir:

1. `Reset Demo Data` ile önceki demo kayıtlarını temizle.
2. `Seed Data` ile sentetik event verisi üret.
3. Duplicate, missing fields, invalid values, spike veya drop anomalilerinden birini ekle.
4. `Run Analysis` ile analiz işlemini çalıştır.
5. Overview ekranından genel metrikleri kontrol et.
6. Metric Detail ekranından metriklerin zaman içindeki değişimini incele.
7. Alerts ekranından üretilen alarmları görüntüle.
8. Evaluation ekranından detection rate ve false alarm rate değerlerini kontrol et.

## API Endpointleri

| Endpoint | Metot | Açıklama |
|---|---|---|
| `/health` | GET | Backend servisinin çalışıp çalışmadığını kontrol eder |
| `/api/reset` | POST | Demo verilerini temizler |
| `/api/seed` | POST | Sentetik event verisi üretir |
| `/api/anomalies/inject` | POST | Seçilen anomali türünü veriye ekler |
| `/api/analyze` | POST | Metrikleri hesaplar ve alarmları üretir |
| `/api/summary` | GET | Overview ekranı için özet verileri döndürür |
| `/api/metrics` | GET | Zaman serisi metriklerini döndürür |
| `/api/alerts` | GET | Üretilen alarm kayıtlarını listeler |
| `/api/evaluation` | GET | Detection rate ve false alarm rate sonuçlarını döndürür |

## Desteklenen Anomali Türleri

- `duplicate`
- `missing_fields`
- `invalid_values`
- `spike`
- `drop`

## Frontend Ekranları

Uygulama dört ana ekrandan oluşur:

- Overview
- Metric Detail
- Alerts
- Evaluation

Overview ekranında demo akışını başlatmak için gerekli butonlar ve genel metrik kartları yer alır. Metric Detail ekranında seçilen metriklerin zaman içindeki değişimi görüntülenir. Alerts ekranı analiz sonucunda oluşan alarmları listeler. Evaluation ekranı ise basit değerlendirme sonuçlarını gösterir.

## Notlar

Bu proje üretim ortamında kullanılmak üzere hazırlanmış tam kapsamlı bir veri gözlemleme platformu değildir. Yüksek lisans dönem projesi kapsamında, veri kalitesi izleme ve basit anomali tespiti akışını çalışan bir uygulama üzerinden göstermek amacıyla geliştirilmiştir.

Projede kullanılan veriler sentetiktir. Gerçek müşteri, kullanıcı veya şirket verisi kullanılmamıştır.
