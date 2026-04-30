TurkeyAutoMap
TurkeyAutoMap, Türkiye illeri ve ilçeleri için QGIS üzerinde otomatik lokasyon haritası üreten bir Python eklentisidir. Eklenti; GADM idari sınırlarını, Geofabrik OpenStreetMap verilerini ve isteğe bağlı altlık haritaları kullanarak profesyonel görünümlü harita katmanları ve layout çıktıları hazırlar.

Özellikler
Türkiye'nin 81 ili arasından seçim yapma
GADM il ve ilçe sınırlarını otomatik ekleme
İl sınırını vurgulama
Belirli bir ilçeyi vurgulama
İlçe odaklı lokasyon haritası oluşturma
Yol ağı kapsamı seçimi:
Yol ağı yok
Tüm il yolları
Odak ilçe yolları
İsteğe bağlı il/ilçe merkezi sembolleri
İsteğe bağlı su katmanları:
Büyük akarsular
Küçük akarsular
Göller
Baraj / rezervuarlar
Deniz / kıyı bağlamı
İsteğe bağlı altlık haritalar:
Google Satellite
Google Hybrid
Esri World Imagery
OpenStreetMap Standard
CartoDB Positron
Profesyonel layout üretimi:
Başlık
Lejant
Ölçek
Yön oku
Konum haritası
A3/A4 ve yatay/dikey sayfa seçenekleri
Kalıcı önbellek sistemi sayesinde büyük veri dosyalarını tekrar tekrar indirmeme
Veri Kaynakları
Eklenti aşağıdaki açık veri kaynaklarını kullanır:

GADM 4.1 Türkiye idari sınırları
https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_TUR_shp.zip

Geofabrik OpenStreetMap Türkiye Shapefile
https://download.geofabrik.de/europe/turkey.html

Kullanılan Geofabrik katmanları:

gis_osm_roads_free_1.shp
gis_osm_places_free_1.shp
gis_osm_waterways_free_1.shp
gis_osm_water_a_free_1.shp
Gereksinimler
QGIS 3.16 veya üzeri
İlk veri indirme için internet bağlantısı
QGIS Processing eklentisinin aktif olması
QGIS'in kendi Python ortamı dışında ek bir Python paketi gerekmez.

Kurulum
GitHub Releases bölümünden TurkeyAutoMap.zip dosyasını indirin.
QGIS'i açın.
Eklentiler > Eklentileri Yönet ve Kur menüsüne gidin.
ZIP'ten kur sekmesini açın.
TurkeyAutoMap.zip dosyasını seçin.
Kurulumdan sonra QGIS'i yeniden başlatın.
Kullanım
TurkeyAutoMap eklentisini QGIS araç çubuğundan veya eklenti menüsünden açın.
Haritasını oluşturmak istediğiniz ili seçin.
Yol kapsamı, tema, ilçe vurgusu, su katmanları, altlık harita ve layout seçeneklerini belirleyin.
Haritayı Oluştur düğmesine basın.
Eklenti eksik verileri indirir, katmanları üretir, QGIS'e ekler ve layout oluşturur.
Önbellek
İndirilen kaynak zip dosyaları QGIS profil dizinindeki kalıcı önbellekte saklanır:

<QGIS profil dizini>/TurkeyAutoMap/cache
Üretilen geçici harita çıktıları şu klasöre yazılır:

<QGIS profil dizini>/TurkeyAutoMap/cache/generated
Önbelleği Temizle düğmesi üretilen geçici çıktıları temizler; indirilen büyük kaynak zip dosyalarını korur.

Altlık Haritalar
Altlık haritalar QGIS XYZ tile yöntemiyle eklenir. QuickMapServices ile benzer servisler kullanılır ancak eklenti doğrudan QGIS raster/XYZ katmanı oluşturur. Böylece QuickMapServices kurulu olmasa bile seçili servis çalışabilir.

Altlık servislerinin çalışması internet bağlantısına ve ilgili servis sağlayıcının erişilebilir olmasına bağlıdır.

Notlar
Haritanın kalabalık olmaması için il/ilçe merkezi sembolleri ve su katmanları varsayılan olarak kapalı gelir.
Yol ağı varsayılan olarak kapalıdır; kullanıcı isterse tüm il yollarını veya odak ilçe yollarını açabilir.
Layout haritası QGIS katman ağacını takip edecek şekilde ayarlanmıştır.
Sonradan eklenen katmanların layoutta görünmesi için layout penceresinde haritayı yenilemek gerekebilir.
Geliştirici
Powered By AGLSOFT - Ali Ganigülü™

Geliştirici: Ali Ganigülü
E-posta: aliganigulu.44@gmail.com
