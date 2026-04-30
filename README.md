# TurkeyAutoMap

TurkeyAutoMap, QGIS için geliştirilmiş bir Python eklentisidir. Seçilen Türkiye ili veya ilçesi için GADM idari sınırlarını, Geofabrik OpenStreetMap verilerini ve isteğe bağlı XYZ altlık haritalarını kullanarak profesyonel lokasyon haritaları üretir.

Eklenti; il sınırı, ilçe sınırları, komşu iller, yol ağı, yerleşim merkezleri, akarsular, göller, baraj/rezervuarlar, deniz-kıyı bağlamı, konum haritası ve print layout çıktısını tek arayüzden üretmek için tasarlanmıştır.

Powered By AGLSOFT - Ali Ganigülü™

---

## İçindekiler

- [Temel Özellikler](#temel-özellikler)
- [Ekran ve Çıktı Mantığı](#ekran-ve-çıktı-mantığı)
- [Veri Kaynakları](#veri-kaynakları)
- [Gereksinimler](#gereksinimler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Arayüz Seçenekleri](#arayüz-seçenekleri)
- [Altlık Haritalar](#altlık-haritalar)
- [Layout Üretimi](#layout-üretimi)
- [Önbellek Sistemi](#önbellek-sistemi)
- [Katman Sırası ve Gruplama](#katman-sırası-ve-gruplama)
- [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)
- [Geliştirici Notları](#geliştirici-notları)
- [Sürüm Notları](#sürüm-notları)
- [Lisans](#lisans)

---

## Temel Özellikler

- Türkiye'nin 81 ili arasından seçim yapma
- GADM 4.1 il sınırı katmanını otomatik filtreleme
- GADM 4.1 ilçe sınırlarını otomatik oluşturma
- Seçilen ilin sınırını vurgulama
- Belirli bir ilçeyi vurgulama
- İlçe odaklı lokasyon haritası oluşturma
- Komşu illeri isteğe bağlı gösterme
- Komşu illeri iki farklı stille çizme:
  - Sadece sınır
  - Dolgulu sınır
- Komşu il adlarını isteğe bağlı etiketleme
- Yol ağı kapsamı seçimi:
  - Yol ağı yok
  - Tüm il yolları
  - Odak ilçe yolları
- İl ve ilçe merkezi sembollerini isteğe bağlı ekleme
- İl ve ilçe merkezi adlarını isteğe bağlı etiketleme
- Hidrografya katmanlarını isteğe bağlı ekleme:
  - Büyük akarsular
  - Küçük akarsular
  - Göller
  - Baraj / rezervuarlar
  - Deniz / kıyı bağlamı
- Su katmanı adlarını isteğe bağlı etiketleme
- Çok sayıda tema ve renk paleti
- İlçe renklendirme paleti seçimi
- İlçe vurgu rengi seçimi
- A3/A4 sayfa boyutu seçimi
- Yatay/dikey layout seçimi
- Otomatik lejant, ölçek çubuğu ve yön oku
- İl veya ilçe konum haritası
- QGIS XYZ altlık haritaları
- Kalıcı önbellek sistemi
- Büyük Geofabrik verisini yalnızca ihtiyaç olduğunda indirme

---

## Ekran ve Çıktı Mantığı

TurkeyAutoMap iki ana çıktı üretir:

1. QGIS harita tuvaline eklenen katmanlar
2. QGIS Layout Manager içinde oluşturulan profesyonel harita layout'u

Eklenti katmanları tematik gruplar halinde düzenler:

- Merkezler
- Ulaşım
- Akarsular
- İdari Sınırlar
- Su Alanları
- Altlık Harita

Bu yapı, Layers panelinde katmanları daha anlaşılır yönetmeyi sağlar.

---

## Veri Kaynakları

### GADM

İdari sınırlar için GADM 4.1 Türkiye shapefile verisi kullanılır.

Kaynak:

```text
https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_TUR_shp.zip
```

Kullanılan dosyalar:

```text
gadm41_TUR_1.shp   -> İl sınırları
gadm41_TUR_2.shp   -> İlçe sınırları
```

İl filtreleme alanı:

```text
NAME_1
```

İlçe adı alanı:

```text
NAME_2
```

### Geofabrik OpenStreetMap

Yol, yerleşim ve su katmanları için Geofabrik Türkiye OSM shapefile verisi kullanılır.

Kaynak:

```text
https://download.geofabrik.de/europe/turkey.html
```

Kullanılan dosya:

```text
turkey-latest-free.shp.zip
```

Kullanılan katmanlar:

```text
gis_osm_roads_free_1.shp       -> Yol ağı
gis_osm_places_free_1.shp      -> İl/ilçe merkezleri
gis_osm_waterways_free_1.shp   -> Akarsular
gis_osm_water_a_free_1.shp     -> Göl, baraj, deniz/kıyı bağlamı
```

Önemli not:

Geofabrik verisi büyüktür. TurkeyAutoMap, yol/merkez/su katmanları kapalıysa bu veriyi indirmez. Böylece sadece sınır haritası oluşturulacaksa işlem daha hızlı ilerler.

---

## Gereksinimler

- QGIS 3.16 veya üzeri
- İnternet bağlantısı
- QGIS Processing eklentisinin aktif olması
- İlk çalıştırmada veri indirme izni

Ek Python paketi gerekmez. Eklenti QGIS'in kendi Python ortamıyla çalışır.

---

## Kurulum

1. GitHub Releases bölümünden `TurkeyAutoMap.zip` dosyasını indirin.
2. QGIS'i açın.
3. Menüden şu yolu izleyin:

```text
Plugins > Manage and Install Plugins
```

4. Sol menüden şu sekmeyi açın:

```text
Install from ZIP
```

5. `TurkeyAutoMap.zip` dosyasını seçin.
6. Eklentiyi kurun.
7. QGIS'i yeniden başlatın.

Kurulumdan sonra eklenti şu menü altında görünür:

```text
Vector > TurkeyAutoMap
```

Ayrıca araç çubuğunda TurkeyAutoMap ikonu da görünür.

---

## Kullanım

1. QGIS'i açın.
2. `Vector > TurkeyAutoMap` menüsünden eklentiyi başlatın.
3. İl listesinden çalışmak istediğiniz ili seçin.
4. Harita kapsamı seçeneklerini belirleyin.
5. Gerekirse ek veri katmanlarını açın.
6. Tema, renk paleti ve vurgu rengini seçin.
7. Layout ayarlarını belirleyin.
8. `Haritayı Oluştur` düğmesine basın.

Eklenti şu işlemleri otomatik yapar:

- Gerekli verileri kontrol eder.
- Eksik verileri indirir.
- Zip dosyalarını geçici klasöre çıkarır.
- İl sınırını filtreler.
- İlçe sınırlarını oluşturur.
- İsteğe bağlı yol, yerleşim ve su katmanlarını üretir.
- Katmanları QGIS'e ekler.
- Semboloji uygular.
- Harita görünümünü ayarlar.
- Layout Manager içinde çıktı layout'u oluşturur.

---

## Arayüz Seçenekleri

### İl

Haritası oluşturulacak Türkiye ilini seçer.

### Yol Kapsamı

Yol katmanının nasıl üretileceğini belirler.

Seçenekler:

- `Yol ağı yok`
- `Tüm il yolları`
- `Odak ilçe yolları`

`Yol ağı yok` seçilirse Geofabrik yol verisi işlenmez.

`Tüm il yolları` seçilirse yol ağı seçilen il sınırına göre kırpılır.

`Odak ilçe yolları` seçilirse yol ağı yalnızca yazılan odak ilçe sınırına göre kırpılır.

### İl Sınırını Belirgin Vurgula

Seçilen ilin dış sınırını kalın ve yüksek kontrastlı gösterir.

### Komşu İlleri Göster

Seçilen ile komşu olan illeri haritaya bağlam katmanı olarak ekler.

### Komşu İl Görünümü

Komşu illerin nasıl çizileceğini belirler.

Seçenekler:

- `Sadece sınır`
- `Dolgulu sınır`

`Sadece sınır` seçilirse komşu illerin içi boş görünür.

`Dolgulu sınır` seçilirse komşu iller aktif temaya uygun yarı saydam dolgu ve sınırla gösterilir.

### Komşu İl Adlarını Göster

Komşu illerin adlarını etiket olarak ekler.

Yoğun haritalarda kapalı tutulması önerilir.

### Ek Veri Katmanları

Ek veri katmanları ayrı bir başlık altında toplanır. Varsayılan olarak kapalı gelir.

#### Yerleşim Merkezleri

- İl/ilçe merkezi sembolleri
- Merkez adları

İl merkezi ve ilçe merkezleri farklı sembolojiyle gösterilir.

#### Hidrografya

- Büyük akarsular
- Küçük akarsular
- Göller
- Baraj / rezervuarlar
- Deniz / kıyı bağlamı
- Su katmanı adları

Bu katmanlar haritayı kalabalıklaştırabileceği için kullanıcı isteğine bağlıdır.

### Tema

Haritanın genel görünümünü belirler.

Mevcut temalar:

- Profesyonel
- Dark Mode
- Blueprint
- Retro
- Minimal
- Topo
- Municipal
- High Contrast

Tema; il sınırı, ilçe sınırı, komşu il, etiket, yol ve layout renklerini etkiler.

### İlçe Renk Paleti

İlçeleri farklı renklerde göstermek için kullanılacak renk setini belirler.

Mevcut paletler:

- Canlı Ayrışan
- Pastel Ayrışan
- Tableau
- ColorBrewer Set3
- Topo Doğal
- Belediye
- Yüksek Kontrast
- Sıcak
- Soğuk
- Retro Çoklu

### İlçe Vurgu Rengi

Odak veya vurgulanan ilçenin rengini belirler.

Seçenekler:

- Otomatik
- Magenta / Fuşya
- Parlak Cyan
- Lime Yeşil
- Sinyal Sarı
- Turuncu
- Kırmızı
- Mor
- Siyah
- Beyaz

### İlçe Odak Modu

Ana haritayı yazılan ilçeye yakınlaştırır.

Başlık şu formata dönüşür:

```text
<İlçe> ilçesi (<İl>) Lokasyon Haritası
```

### Sadece Belirli İlçeyi Vurgula

Harita ili göstermeye devam eder; yalnızca yazılan ilçe kalın sınırla vurgulanır.

Bu seçenek zoom yapmaz.

### Layout Ayarları

Sayfa ve layout görünümü için kullanılır.

Seçenekler:

- A4 / A3
- Yatay / Dikey
- Dinamik QGIS lejantı
- Konum haritası
- Altlık harita

---

## Altlık Haritalar

Altlık haritalar QGIS XYZ tile yöntemiyle eklenir. QuickMapServices ile benzer servisler kullanılır; ancak eklenti doğrudan QGIS raster/XYZ katmanı oluşturur.

Mevcut altlıklar:

- Google Satellite
- Google Hybrid
- Google Roadmap
- Google Terrain
- Esri World Imagery
- Esri World Street Map
- Esri World Topographic
- Esri World Terrain
- Esri Light Gray
- Esri Dark Gray
- OpenStreetMap Standard
- OpenStreetMap HOT
- OpenTopoMap
- CyclOSM
- CartoDB Positron
- CartoDB Dark Matter
- CartoDB Voyager
- CartoDB Voyager No Labels

Altlık haritaların çalışması şunlara bağlıdır:

- İnternet bağlantısı
- Servis sağlayıcının erişilebilir olması
- QGIS'in XYZ/WMS raster desteği

Not:

Bazı servisler yoğun kullanımda geç cevap verebilir veya geçici olarak erişilemeyebilir.

---

## Layout Üretimi

TurkeyAutoMap otomatik olarak QGIS Layout Manager içinde bir layout oluşturur.

Layout içeriği:

- Başlık
- Ana harita
- Lejant
- Ölçek çubuğu
- Yön oku
- Konum haritası

Başlık formatı:

İl haritası için:

```text
Adana İli Lokasyon Haritası
```

İlçe odak modu için:

```text
Seyhan ilçesi (Adana) Lokasyon Haritası
```

---

## Önbellek Sistemi

TurkeyAutoMap verileri QGIS profil dizinindeki kalıcı önbellekte saklar.

Önbellek dizini:

```text
<QGIS profil dizini>/TurkeyAutoMap/cache
```

Üretilen geçici çıktılar:

```text
<QGIS profil dizini>/TurkeyAutoMap/cache/generated
```

`Önbelleği Temizle` düğmesi:

- Üretilen geçici GeoPackage çıktılarını siler.
- TurkeyAutoMap tarafından eklenen katmanları projeden kaldırır.
- TurkeyAutoMap tarafından oluşturulan layer tree gruplarını temizler.
- İndirilen büyük kaynak zip dosyalarını korur.

Korunan dosyalar:

- `gadm41_TUR_shp.zip`
- `turkey-latest-free.shp.zip`

Bu sayede aynı veriler tekrar tekrar indirilmez.

---

## Katman Sırası ve Gruplama

Katmanlar QGIS Layers panelinde anlaşılır gruplar altında düzenlenir.

Tipik yapı:

```text
Merkezler
Ulaşım
Akarsular
İdari Sınırlar
Su Alanları
Altlık Harita
```

Bu yapı harita okumasını kolaylaştırır.

---

## Sık Karşılaşılan Sorunlar

### Eklenti ZIP olarak kurulmuyor

QGIS içinde şu yolu kullanın:

```text
Plugins > Manage and Install Plugins > Install from ZIP
```

ZIP dosyasının içinde doğrudan `TurkeyAutoMap` klasörü bulunmalıdır.

### Eklenti nerede görünüyor?

Kurulumdan sonra:

```text
Vector > TurkeyAutoMap
```

altında görünür.

Araç çubuğunda da TurkeyAutoMap ikonu eklenir.

### İlk çalıştırma uzun sürüyor

İlk çalıştırmada GADM ve seçilen seçeneklere göre Geofabrik verileri indirilebilir.

Geofabrik Türkiye shapefile verisi büyük olduğu için yol, merkez veya su katmanı seçiliyse indirme süresi uzayabilir.

### Altlık harita görünmüyor

Kontrol edin:

- İnternet bağlantısı var mı?
- Servis sağlayıcı erişilebilir mi?
- QGIS raster/XYZ katmanlarını açabiliyor mu?
- Layout penceresinde harita öğesi yenilendi mi?

### Önbelleği temizlerken dosya kilitli hatası

QGIS bazen GeoPackage dosyalarını kilitli tutabilir.

Çözüm:

1. TurkeyAutoMap katmanlarını projeden kaldırın.
2. QGIS'i yeniden başlatın.
3. Tekrar `Önbelleği Temizle` düğmesine basın.

### İlçe bulunamadı hatası

İlçe adını GADM verisindeki yazıma yakın girin. Türkçe karakterler çoğu durumda normalize edilir; yine de resmi ilçe adını kullanmak en güvenli yoldur.

---

## Geliştirici Notları

Ana dosyalar:

```text
TurkeyAutoMap/
├── __init__.py
├── metadata.txt
├── turkey_auto_map.py
├── turkey_auto_map_dialog.py
├── turkey_auto_map_dialog.ui
├── resources.py
├── resources.qrc
├── icon.png
└── cache/
```

Ana sınıf:

```text
turkey_auto_map.py
```

Arayüz:

```text
turkey_auto_map_dialog.ui
turkey_auto_map_dialog.py
```

Eklenti metadata:

```text
metadata.txt
```

QGIS minimum sürüm:

```text
3.16
```

---

## Sürüm Notları

### 2.4.0

- Altlık harita listesi genişletildi.
- Komşu il görünüm modu eklendi.
- Ek veri katmanları ayrı arayüz başlığı altında toplandı.
- Tema bazlı komşu il dolgu/sınır renkleri güncellendi.

### 2.3.0

- Komşu illeri göster seçeneği eklendi.
- Önbellek temizleme işlemi layer tree gruplarını da temizleyecek şekilde genişletildi.
- README kurulum adımları İngilizce QGIS menülerine göre güncellendi.

### 2.2.0

- Yol ağı yok seçeneği varsayılan hale getirildi.
- Altlık harita seçenekleri eklendi.
- Geofabrik verisi yalnızca ihtiyaç halinde indirilecek şekilde optimize edildi.

### 2.1.0

- README dosyası eklendi.
- İl/ilçe merkezi, akarsu, göl, baraj ve deniz/kıyı seçenekleri varsayılan kapalı hale getirildi.

### 2.0.0

- Su katmanları ayrı katmanlara ayrıldı.
- Dinamik lejant varsayılan kapalı hale getirildi.

---

## Katkı

Geri bildirimler, hata raporları ve geliştirme önerileri değerlidir.

Önerilen katkı başlıkları:

- Yeni altlık harita servisleri
- Yeni tema seçenekleri
- Mahalle sınırı desteği
- TÜİK nüfus verisi entegrasyonu
- Fay hattı veya afet riski katmanları
- Gelişmiş layout şablonları

---

## Geliştirici

Powered By AGLSOFT - Ali Ganigülü™

Geliştirici:

```text
Ali Ganigülü
```

E-posta:

```text
aliganigulu.44@gmail.com
```

---

## Lisans

Yayınlamadan önce tercih ettiğiniz açık kaynak lisansını eklemeniz önerilir.

Önerilen lisanslar:

- MIT License
- GPL-3.0
- Apache-2.0

QGIS eklentileri için lisans seçerken kullandığınız veri kaynaklarının lisans koşullarını da dikkate alın.
