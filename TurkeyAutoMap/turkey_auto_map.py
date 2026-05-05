# -*- coding: utf-8 -*-
"""Main implementation for the TurkeyAutoMap QGIS plugin."""

import os
import re
import shutil
import tempfile
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from qgis.PyQt.QtCore import QObject, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFont, QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import (
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFillSymbol,
    QgsFeatureRequest,
    QgsLineSymbol,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemPage,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutMeasurement,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLegendStyle,
    QgsMessageLog,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsProcessingFeedback,
    QgsPrintLayout,
    QgsProject,
    QgsRasterLayer,
    QgsRendererCategory,
    QgsSingleSymbolRenderer,
    QgsTask,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsWkbTypes,
    Qgis,
)

try:
    import processing
except ImportError:  # pragma: no cover - depends on QGIS runtime
    processing = None

from .turkey_auto_map_dialog import TurkeyAutoMapDialog


PLUGIN_NAME = "TurkeyAutoMap"
PLUGIN_MENU = "&TurkeyAutoMap"
GADM_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_TUR_shp.zip"
GEOFABRIK_PAGE_URL = "https://download.geofabrik.de/europe/turkey.html"
GEOFABRIK_ZIP_URL = (
    "https://download.geofabrik.de/europe/turkey-latest-free.shp.zip"
)
GADM_ZIP_NAME = "gadm41_TUR_shp.zip"
GEOFABRIK_ZIP_NAME = "turkey-latest-free.shp.zip"
GADM_SHP_NAME = "gadm41_TUR_1.shp"
GADM_DISTRICT_SHP_NAME = "gadm41_TUR_2.shp"
ROADS_SHP_NAME = "gis_osm_roads_free_1.shp"
PLACES_SHP_NAME = "gis_osm_places_free_1.shp"
WATERWAYS_SHP_NAME = "gis_osm_waterways_free_1.shp"
WATER_AREAS_SHP_NAME = "gis_osm_water_a_free_1.shp"
GADM_NAME_FIELD = "NAME_1"
DISTRICT_NAME_FIELD = "NAME_2"
ROAD_CLASS_FIELD = "fclass"
OSM_NAME_FIELD = "name"
OSM_CLASS_FIELD = "fclass"
DOWNLOAD_CHUNK_SIZE = 8192
LOG_TAG = "TurkeyAutoMap"
BOUNDARY_LAYER_NAME = "{province} İl Sınırı"
DISTRICTS_LAYER_NAME = "{province} İlçe Sınırları"
FOCUS_DISTRICT_LAYER_NAME = "{district} İlçe Odağı"
NEIGHBORS_LAYER_NAME = "{province} Komşu İlleri"
TURKEY_LOCATOR_LAYER_NAME = "Türkiye İl Konum Haritası"
ROADS_LAYER_NAME = "{province} Yol Ağı"
PLACES_LAYER_NAME = "{province} İl ve İlçe Merkezleri"
MAJOR_WATERWAYS_LAYER_NAME = "{province} Büyük Akarsular"
MINOR_WATERWAYS_LAYER_NAME = "{province} Küçük Akarsular"
LAKES_LAYER_NAME = "{province} Göller"
RESERVOIRS_LAYER_NAME = "{province} Baraj ve Rezervuarlar"
SEA_CONTEXT_LAYER_NAME = "{province} Deniz ve Kıyı Bağlamı"
LAYOUT_NAME = "{province} Profesyonel Harita"
CACHE_FOLDER_NAME = "TurkeyAutoMap"
READY_MESSAGE = "✓ {province} haritası hazır."
NO_INTERNET_MESSAGE = (
    "İnternet bağlantısı kurulamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin."
)
HTTP_ERROR_MESSAGE = "İndirme başarısız oldu: {url} (HTTP {code})"
PROCESSING_IMPORT_ERROR = (
    "QGIS processing modülü yüklenemedi. Processing eklentisinin etkin olduğundan "
    "emin olun."
)
SAVE_FILTER = "QGIS Project (*.qgz)"

PROVINCES = [
    ("Adana", "Adana"),
    ("Adıyaman", "Adiyaman"),
    ("Afyonkarahisar", "Afyonkarahisar"),
    ("Ağrı", "Agri"),
    ("Aksaray", "Aksaray"),
    ("Amasya", "Amasya"),
    ("Ankara", "Ankara"),
    ("Antalya", "Antalya"),
    ("Ardahan", "Ardahan"),
    ("Artvin", "Artvin"),
    ("Aydın", "Aydin"),
    ("Balıkesir", "Balikesir"),
    ("Bartın", "Bartin"),
    ("Batman", "Batman"),
    ("Bayburt", "Bayburt"),
    ("Bilecik", "Bilecik"),
    ("Bingöl", "Bingol"),
    ("Bitlis", "Bitlis"),
    ("Bolu", "Bolu"),
    ("Burdur", "Burdur"),
    ("Bursa", "Bursa"),
    ("Çanakkale", "Canakkale"),
    ("Çankırı", "Cankiri"),
    ("Çorum", "Corum"),
    ("Denizli", "Denizli"),
    ("Diyarbakır", "Diyarbakir"),
    ("Düzce", "Duzce"),
    ("Edirne", "Edirne"),
    ("Elazığ", "Elazig"),
    ("Erzincan", "Erzincan"),
    ("Erzurum", "Erzurum"),
    ("Eskişehir", "Eskisehir"),
    ("Gaziantep", "Gaziantep"),
    ("Giresun", "Giresun"),
    ("Gümüşhane", "Gumushane"),
    ("Hakkari", "Hakkari"),
    ("Hatay", "Hatay"),
    ("Iğdır", "Igdir"),
    ("Isparta", "Isparta"),
    ("İstanbul", "Istanbul"),
    ("İzmir", "Izmir"),
    ("Kahramanmaraş", "Kahramanmaras"),
    ("Karabük", "Karabuk"),
    ("Karaman", "Karaman"),
    ("Kars", "Kars"),
    ("Kastamonu", "Kastamonu"),
    ("Kayseri", "Kayseri"),
    ("Kırıkkale", "Kirikkale"),
    ("Kırklareli", "Kirklareli"),
    ("Kırşehir", "Kirsehir"),
    ("Kilis", "Kilis"),
    ("Kocaeli", "Kocaeli"),
    ("Konya", "Konya"),
    ("Kütahya", "Kutahya"),
    ("Malatya", "Malatya"),
    ("Manisa", "Manisa"),
    ("Mardin", "Mardin"),
    ("Mersin", "Mersin"),
    ("Muğla", "Mugla"),
    ("Muş", "Mus"),
    ("Nevşehir", "Nevsehir"),
    ("Niğde", "Nigde"),
    ("Ordu", "Ordu"),
    ("Osmaniye", "Osmaniye"),
    ("Rize", "Rize"),
    ("Sakarya", "Sakarya"),
    ("Samsun", "Samsun"),
    ("Siirt", "Siirt"),
    ("Sinop", "Sinop"),
    ("Sivas", "Sivas"),
    ("Şanlıurfa", "Sanliurfa"),
    ("Şırnak", "Sirnak"),
    ("Tekirdağ", "Tekirdag"),
    ("Tokat", "Tokat"),
    ("Trabzon", "Trabzon"),
    ("Tunceli", "Tunceli"),
    ("Uşak", "Usak"),
    ("Van", "Van"),
    ("Yalova", "Yalova"),
    ("Yozgat", "Yozgat"),
    ("Zonguldak", "Zonguldak"),
]

ROAD_STYLES = [
    ("motorway", "Motorway", "#c81d25", 3.0),
    ("primary", "Primary", "#f28e2b", 2.0),
    ("secondary", "Secondary", "#edc948", 1.5),
    ("tertiary", "Tertiary", "#6f6f6f", 1.0),
    ("__other__", "Diğer", "#d9d9d9", 0.5),
]

LEGEND_BORDER_COLOR = "#2f3640"
LEGEND_TEXT_COLOR = "#263238"
LAYOUT_MUTED_TEXT_COLOR = "#5f6c72"
MAP_FRAME_COLOR = "#cfd8dc"

THEMES = {
    "professional": {
        "name": "Profesyonel",
        "page_bg": "#ffffff",
        "title": "#17212b",
        "muted": "#5f6c72",
        "district_fill": "#dbeafe",
        "district_outline": "95,105,110,150",
        "district_palette": [
            "#dbeafe",
            "#dcfce7",
            "#fef3c7",
            "#fde2e2",
            "#ede9fe",
            "#cffafe",
            "#fce7f3",
            "#e5e7eb",
        ],
        "neighbor_fill": "229,231,235,95",
        "neighbor_outline": "55,65,81,220",
        "boundary": "0,0,0,255",
        "focus": "#d000ff",
        "label": "#263238",
        "label_buffer": "#ffffff",
        "map_frame": "#cfd8dc",
    },
    "dark": {
        "name": "Dark Mode",
        "page_bg": "#111827",
        "title": "#f8fafc",
        "muted": "#cbd5e1",
        "district_fill": "#1f3a5f",
        "district_outline": "148,163,184,180",
        "district_palette": [
            "#1e3a5f",
            "#164e63",
            "#365314",
            "#713f12",
            "#581c87",
            "#7f1d1d",
            "#334155",
        ],
        "neighbor_fill": "30,41,59,115",
        "neighbor_outline": "203,213,225,230",
        "boundary": "248,250,252,255",
        "focus": "#00e5ff",
        "label": "#f8fafc",
        "label_buffer": "#0f172a",
        "map_frame": "#64748b",
    },
    "blueprint": {
        "name": "Blueprint",
        "page_bg": "#eaf4ff",
        "title": "#0f3d66",
        "muted": "#426b91",
        "district_fill": "#d6ebff",
        "district_outline": "28,89,128,170",
        "district_palette": [
            "#cfe8ff",
            "#b9dcff",
            "#dff2ff",
            "#c7f0ff",
            "#e7f5ff",
        ],
        "neighbor_fill": "213,232,247,110",
        "neighbor_outline": "15,61,102,225",
        "boundary": "15,61,102,255",
        "focus": "#ffb703",
        "label": "#0f3d66",
        "label_buffer": "#ffffff",
        "map_frame": "#6aa6d8",
    },
    "retro": {
        "name": "Retro",
        "page_bg": "#f8f1df",
        "title": "#3f3426",
        "muted": "#7b6a55",
        "district_fill": "#ead7ad",
        "district_outline": "109,89,59,155",
        "district_palette": [
            "#ead7ad",
            "#d9c48f",
            "#f0c987",
            "#d7b98e",
            "#e8c6a2",
            "#c9b27e",
        ],
        "neighbor_fill": "220,207,176,110",
        "neighbor_outline": "91,70,43,225",
        "boundary": "63,52,38,255",
        "focus": "#d000ff",
        "label": "#3f3426",
        "label_buffer": "#fff8e8",
        "map_frame": "#a68a64",
    },
    "minimal": {
        "name": "Minimal",
        "page_bg": "#fafafa",
        "title": "#202124",
        "muted": "#6b7280",
        "district_fill": "#f3f4f6",
        "district_outline": "107,114,128,135",
        "district_palette": ["#f3f4f6", "#e5e7eb", "#eef2f7", "#f8fafc"],
        "neighbor_fill": "243,244,246,85",
        "neighbor_outline": "75,85,99,215",
        "boundary": "17,24,39,255",
        "focus": "#e31a1c",
        "label": "#374151",
        "label_buffer": "#ffffff",
        "map_frame": "#d1d5db",
    },
    "topo": {
        "name": "Topo",
        "page_bg": "#eef7ea",
        "title": "#1f3d2b",
        "muted": "#58735f",
        "district_fill": "#dceccf",
        "district_outline": "79,111,82,165",
        "district_palette": ["#dceccf", "#c9dfb5", "#e8dcb2", "#d7e8c4", "#bdd7a8"],
        "neighbor_fill": "218,232,206,105",
        "neighbor_outline": "52,88,57,220",
        "boundary": "31,61,43,255",
        "focus": "#d000ff",
        "label": "#24402d",
        "label_buffer": "#f8fff2",
        "map_frame": "#8aaa7c",
    },
    "municipal": {
        "name": "Municipal",
        "page_bg": "#ffffff",
        "title": "#0b3b5a",
        "muted": "#4f6f82",
        "district_fill": "#e5f3fb",
        "district_outline": "69,104,124,155",
        "district_palette": ["#d8ecf7", "#e8f5e9", "#fff3cd", "#fde2e4", "#e8eaf6"],
        "neighbor_fill": "232,240,244,95",
        "neighbor_outline": "47,79,95,220",
        "boundary": "19,31,48,255",
        "focus": "#d000ff",
        "label": "#0b3b5a",
        "label_buffer": "#ffffff",
        "map_frame": "#b7c9d3",
    },
    "contrast": {
        "name": "High Contrast",
        "page_bg": "#ffffff",
        "title": "#000000",
        "muted": "#222222",
        "district_fill": "#ffffff",
        "district_outline": "0,0,0,210",
        "district_palette": ["#ffffff", "#f2f2f2", "#e6e6e6", "#d9d9d9"],
        "neighbor_fill": "235,235,235,95",
        "neighbor_outline": "0,0,0,255",
        "boundary": "0,0,0,255",
        "focus": "#ff0000",
        "label": "#000000",
        "label_buffer": "#ffffff",
        "map_frame": "#000000",
    },
}

THEME_KEYS_BY_LABEL = {
    "Profesyonel": "professional",
    "Dark Mode": "dark",
    "Blueprint": "blueprint",
    "Retro": "retro",
    "Minimal": "minimal",
    "Topo": "topo",
    "Municipal": "municipal",
    "High Contrast": "contrast",
}

HIGHLIGHT_COLORS_BY_LABEL = {
    "Otomatik - tema için en belirgin": "auto",
    "Magenta / Fuşya": "#d000ff",
    "Parlak Cyan": "#00bcd4",
    "Lime Yeşil": "#76ff03",
    "Sinyal Sarı": "#ffd400",
    "Turuncu": "#ff6d00",
    "Kırmızı": "#e31a1c",
    "Mor": "#7b2cbf",
    "Siyah": "#000000",
    "Beyaz": "#ffffff",
}

BASEMAPS_BY_LABEL = {
    "Altlık yok": None,
    "Google Satellite": {
        "name": "Altlık Harita - Google Satellite",
        "url": "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    },
    "Google Hybrid": {
        "name": "Altlık Harita - Google Hybrid",
        "url": "https://mt0.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    },
    "Google Roadmap": {
        "name": "Altlık Harita - Google Roadmap",
        "url": "https://mt0.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    },
    "Google Terrain": {
        "name": "Altlık Harita - Google Terrain",
        "url": "https://mt0.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    },
    "Esri World Imagery": {
        "name": "Altlık Harita - Esri World Imagery",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "Esri World Street Map": {
        "name": "Altlık Harita - Esri World Street Map",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "Esri World Topographic": {
        "name": "Altlık Harita - Esri World Topographic",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "Esri World Terrain": {
        "name": "Altlık Harita - Esri World Terrain",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Terrain_Base/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "Esri Light Gray": {
        "name": "Altlık Harita - Esri Light Gray",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "Esri Dark Gray": {
        "name": "Altlık Harita - Esri Dark Gray",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        ),
    },
    "OpenStreetMap Standard": {
        "name": "Altlık Harita - OpenStreetMap",
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    },
    "OpenStreetMap HOT": {
        "name": "Altlık Harita - OpenStreetMap HOT",
        "url": "https://tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
    },
    "OpenTopoMap": {
        "name": "Altlık Harita - OpenTopoMap",
        "url": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
    },
    "CyclOSM": {
        "name": "Altlık Harita - CyclOSM",
        "url": "https://a.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
    },
    "CartoDB Positron": {
        "name": "Altlık Harita - CartoDB Positron",
        "url": "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
    },
    "CartoDB Dark Matter": {
        "name": "Altlık Harita - CartoDB Dark Matter",
        "url": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
    },
    "CartoDB Voyager": {
        "name": "Altlık Harita - CartoDB Voyager",
        "url": "https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png",
    },
    "CartoDB Voyager No Labels": {
        "name": "Altlık Harita - CartoDB Voyager No Labels",
        "url": (
            "https://basemaps.cartocdn.com/rastertiles/"
            "voyager_nolabels/{z}/{x}/{y}.png"
        ),
    },
}

PAGE_SIZES_MM = {
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
}

PALETTE_KEYS_BY_LABEL = {
    "Canlı Ayrışan": "vivid",
    "Pastel Ayrışan": "pastel",
    "Tableau": "tableau",
    "ColorBrewer Set3": "set3",
    "Topo Doğal": "topo",
    "Belediye": "municipal",
    "Yüksek Kontrast": "contrast",
    "Sıcak": "warm",
    "Soğuk": "cool",
    "Retro Çoklu": "retro_multi",
}

DISTRICT_PALETTES = {
    "vivid": [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
        "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000",
    ],
    "pastel": [
        "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
        "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
        "#ccebc5", "#ffed6f",
    ],
    "tableau": [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ab",
    ],
    "set3": [
        "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
        "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
        "#ccebc5", "#ffed6f",
    ],
    "topo": [
        "#a6cee3", "#b2df8a", "#fdbf6f", "#cab2d6", "#ffff99",
        "#1f78b4", "#33a02c", "#fb9a99", "#e31a1c", "#6a3d9a",
    ],
    "municipal": [
        "#0077b6", "#90be6d", "#f9c74f", "#f8961e", "#577590",
        "#43aa8b", "#f3722c", "#277da1", "#4d908e", "#f94144",
    ],
    "contrast": [
        "#000000", "#ffffff", "#ff0000", "#0000ff", "#ffff00",
        "#00ff00", "#ff00ff", "#00ffff", "#808080", "#ffa500",
    ],
    "warm": [
        "#7f0000", "#b30000", "#d7301f", "#ef6548", "#fc8d59",
        "#fdbb84", "#fdd49e", "#fee8c8", "#8c2d04", "#cc4c02",
    ],
    "cool": [
        "#08306b", "#08519c", "#2171b5", "#4292c6", "#6baed6",
        "#9ecae1", "#c6dbef", "#deebf7", "#006d77", "#83c5be",
    ],
    "retro_multi": [
        "#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51",
        "#8ab17d", "#b56576", "#6d597a", "#355070", "#cb997e",
    ],
}


def stable_cache_dir():
    """Return the persistent cache directory outside the plugin install folder."""
    return os.path.join(QgsApplication.qgisSettingsDirPath(), CACHE_FOLDER_NAME, "cache")


class TurkeyAutoMapError(Exception):
    """Base exception for user-facing plugin errors."""


class DownloadError(TurkeyAutoMapError):
    """Raised when a remote file cannot be downloaded."""


class ProvinceNotFoundError(TurkeyAutoMapError):
    """Raised when the selected province is not found in GADM data."""


class TurkeyAutoMapFeedback(QgsProcessingFeedback):
    """Processing feedback that relays text and progress to a QgsTask."""

    def __init__(self, task):
        """Create feedback bound to the map generation task."""
        super().__init__()
        self.task = task

    def setProgressText(self, text):
        """Forward processing text messages to the task status label."""
        super().setProgressText(text)
        if text:
            self.task.status_changed.emit(text)

    def setProgress(self, progress):
        """Map processing progress to the final quarter of total progress."""
        super().setProgress(progress)
        self.task.setProgress(75 + (float(progress) * 0.20))


class MapBuildTask(QgsTask):
    """Background task that downloads, extracts, filters, and clips data."""

    status_changed = pyqtSignal(str)

    def __init__(self, province_label, province_gadm_name, plugin_dir, options):
        """Initialize task input values and output placeholders."""
        super().__init__(
            "TurkeyAutoMap harita oluşturma",
            QgsTask.CanCancel,
        )
        self.province_label = province_label
        self.province_gadm_name = province_gadm_name
        self.plugin_dir = plugin_dir
        self.options = options
        self.cache_dir = stable_cache_dir()
        self.legacy_cache_dir = os.path.join(plugin_dir, "cache")
        self.generated_dir = os.path.join(self.cache_dir, "generated")
        self.boundary_output = ""
        self.districts_output = ""
        self.focus_district_output = ""
        self.focus_district_name = ""
        self.neighbors_output = ""
        self.turkey_locator_output = ""
        self.roads_output = ""
        self.places_output = ""
        self.major_waterways_output = ""
        self.minor_waterways_output = ""
        self.lakes_output = ""
        self.reservoirs_output = ""
        self.sea_context_output = ""
        self.error = None

    def run(self):
        """Execute all long-running map preparation steps off the GUI thread."""
        temp_dir = tempfile.mkdtemp(prefix="turkey_auto_map_")
        try:
            if processing is None:
                raise TurkeyAutoMapError(PROCESSING_IMPORT_ERROR)

            os.makedirs(self.cache_dir, exist_ok=True)
            os.makedirs(self.generated_dir, exist_ok=True)
            self._seed_stable_cache_from_legacy()

            gadm_zip = os.path.join(self.cache_dir, GADM_ZIP_NAME)
            roads_zip = os.path.join(self.cache_dir, GEOFABRIK_ZIP_NAME)
            needs_geofabrik = self._needs_geofabrik_data()

            self._download_if_missing(GADM_URL, gadm_zip, 0, 25)
            if needs_geofabrik:
                self._download_if_missing(GEOFABRIK_ZIP_URL, roads_zip, 25, 55)
            else:
                self.setProgress(55)

            self._check_cancelled()
            self.status_changed.emit("Zip dosyaları çıkarılıyor...")
            self.setProgress(58)
            gadm_dir = os.path.join(temp_dir, "gadm")
            roads_dir = os.path.join(temp_dir, "roads")
            os.makedirs(gadm_dir, exist_ok=True)
            self._extract_zip(gadm_zip, gadm_dir)
            if needs_geofabrik:
                os.makedirs(roads_dir, exist_ok=True)
                self._extract_zip(roads_zip, roads_dir)

            gadm_path = self._find_file(gadm_dir, GADM_SHP_NAME)
            district_path = self._find_file(gadm_dir, GADM_DISTRICT_SHP_NAME)
            roads_path = ""
            places_path = ""
            waterways_path = ""
            water_areas_path = ""
            if needs_geofabrik:
                if self.options.get("road_scope") != "none":
                    roads_path = self._find_file(roads_dir, ROADS_SHP_NAME)
                places_path = self._find_optional_file(roads_dir, PLACES_SHP_NAME)
                waterways_path = self._find_optional_file(roads_dir, WATERWAYS_SHP_NAME)
                water_areas_path = self._find_optional_file(roads_dir, WATER_AREAS_SHP_NAME)

            self._check_cancelled()
            self.status_changed.emit("İl sınırı filtreleniyor...")
            boundary_layer = self._build_boundary_layer(gadm_path)
            turkey_locator_layer = self._build_turkey_locator_layer(gadm_path)
            self.setProgress(70)

            self._check_cancelled()
            self.status_changed.emit("İlçe sınırları hazırlanıyor...")
            districts_layer = self._build_district_layer(district_path)
            self.setProgress(72)

            focus_layer = None
            focus_district_name = self._requested_focus_district_name()
            if focus_district_name:
                self._check_cancelled()
                self.status_changed.emit("Seçili ilçe hazırlanıyor...")
                focus_layer = self._build_focus_district_layer(
                    district_path,
                    focus_district_name,
                )
                self.focus_district_name = self._first_attribute(
                    focus_layer,
                    DISTRICT_NAME_FIELD,
                )
                self.setProgress(73)

            self._check_cancelled()
            neighbors_layer = None
            if self.options.get("show_neighbors", False):
                self.status_changed.emit("Komşu iller belirleniyor...")
                neighbors_layer = self._build_neighbor_layer(gadm_path, boundary_layer)
            self.setProgress(74)

            safe_name = self._safe_name(self.province_gadm_name)
            if focus_district_name:
                safe_name = "{0}_{1}".format(
                    safe_name,
                    self._safe_name(focus_district_name),
                )
            output_dir = os.path.join(self.generated_dir, safe_name)
            if os.path.isdir(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)

            self.boundary_output = os.path.join(output_dir, "boundary.gpkg")
            self.districts_output = os.path.join(output_dir, "districts.gpkg")
            self.neighbors_output = os.path.join(output_dir, "neighbors.gpkg")
            self.turkey_locator_output = os.path.join(output_dir, "turkey_locator.gpkg")
            self.roads_output = os.path.join(output_dir, "roads.gpkg")
            self.places_output = os.path.join(output_dir, "places.gpkg")
            self.major_waterways_output = os.path.join(output_dir, "major_waterways.gpkg")
            self.minor_waterways_output = os.path.join(output_dir, "minor_waterways.gpkg")
            self.lakes_output = os.path.join(output_dir, "lakes.gpkg")
            self.reservoirs_output = os.path.join(output_dir, "reservoirs.gpkg")
            self.sea_context_output = os.path.join(output_dir, "sea_context.gpkg")
            self._write_vector_layer(boundary_layer, self.boundary_output, "boundary")
            self._write_vector_layer(districts_layer, self.districts_output, "districts")
            if focus_layer is not None:
                self.focus_district_output = os.path.join(
                    output_dir,
                    "focus_district.gpkg",
                )
                self._write_vector_layer(
                    focus_layer,
                    self.focus_district_output,
                    "focus_district",
                )
            if neighbors_layer is not None:
                self._write_vector_layer(neighbors_layer, self.neighbors_output, "neighbors")
            else:
                self.neighbors_output = ""
            self._write_vector_layer(
                turkey_locator_layer,
                self.turkey_locator_output,
                "turkey_locator",
            )

            if self.options.get("show_places", True) and places_path:
                self._check_cancelled()
                self.status_changed.emit("İl ve ilçe merkezleri hazırlanıyor...")
                places_layer = self._build_places_layer(places_path, boundary_layer)
                self._write_vector_layer(places_layer, self.places_output, "places")
            else:
                self.places_output = ""

            self._prepare_context_water_layers(
                waterways_path,
                water_areas_path,
                boundary_layer,
            )

            if self.options.get("road_scope") == "none":
                self.roads_output = ""
            else:
                self._check_cancelled()
                self.status_changed.emit("Yol ağı yükleniyor...")
                roads_layer = QgsVectorLayer(roads_path, "Turkey OSM Roads", "ogr")
                if not roads_layer.isValid():
                    raise TurkeyAutoMapError("Geofabrik yol katmanı yüklenemedi.")

                self._check_cancelled()
                self.status_changed.emit("Yollar kırpılıyor...")
                feedback = TurkeyAutoMapFeedback(self)
                processing.run(
                    "native:clip",
                    {
                        "INPUT": roads_layer,
                        "OVERLAY": (
                            focus_layer
                            if self.options.get("road_scope") == "district"
                            and focus_layer is not None
                            else boundary_layer
                        ),
                        "OUTPUT": self.roads_output,
                    },
                    feedback=feedback,
                )

            self._check_cancelled()
            self.status_changed.emit("Katmanlar hazırlanıyor...")
            self.setProgress(100)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.error = exc
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                LOG_TAG,
                Qgis.Critical,
            )
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def finished(self, result):
        """Keep Qt's task lifecycle hook available for QGIS."""
        super().finished(result)

    def _needs_geofabrik_data(self):
        """Return True when the selected options require Geofabrik data."""
        return (
            self.options.get("road_scope") != "none"
            or self.options.get("show_places", False)
            or self.options.get("show_major_waterways", False)
            or self.options.get("show_minor_waterways", False)
            or self.options.get("show_lakes", False)
            or self.options.get("show_reservoirs", False)
            or self.options.get("show_sea_context", False)
        )

    def _download_if_missing(self, url, output_path, start, end):
        """Download a file in chunks unless it is already cached."""
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            self.status_changed.emit(
                "Önbellekte bulundu: {0}".format(os.path.basename(output_path))
            )
            self.setProgress(end)
            return

        self.status_changed.emit("Veri indiriliyor: {0}".format(os.path.basename(url)))
        temp_output = output_path + ".part"
        if os.path.exists(temp_output):
            os.remove(temp_output)

        try:
            request = urllib.request.Request(url, headers={"User-Agent": PLUGIN_NAME})
            with urllib.request.urlopen(request, timeout=60) as response:
                status_code = getattr(response, "status", response.getcode())
                if status_code != 200:
                    raise DownloadError(
                        HTTP_ERROR_MESSAGE.format(url=url, code=status_code)
                    )

                total = int(response.headers.get("Content-Length", "0") or 0)
                downloaded = 0
                with open(temp_output, "wb") as file_obj:
                    while True:
                        self._check_cancelled()
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        file_obj.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            ratio = min(downloaded / float(total), 1.0)
                            self.setProgress(start + ((end - start) * ratio))
            os.replace(temp_output, output_path)
            self.setProgress(end)
        except urllib.error.URLError as exc:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise DownloadError(NO_INTERNET_MESSAGE) from exc
        except DownloadError:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            raise

    def _seed_stable_cache_from_legacy(self):
        """Copy existing plugin-local downloads into the stable QGIS cache once."""
        if not os.path.isdir(self.legacy_cache_dir):
            return

        for filename in (GADM_ZIP_NAME, GEOFABRIK_ZIP_NAME):
            source = os.path.join(self.legacy_cache_dir, filename)
            target = os.path.join(self.cache_dir, filename)
            if not os.path.exists(source) or os.path.exists(target):
                continue
            if os.path.getsize(source) <= 0:
                continue
            shutil.copy2(source, target)

    def _extract_zip(self, zip_path, output_dir):
        """Extract a zip file to the requested temporary directory."""
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(output_dir)

    def _find_file(self, root_dir, filename):
        """Find a file by name under a directory tree."""
        for current_root, _, files in os.walk(root_dir):
            if filename in files:
                return os.path.join(current_root, filename)
        raise TurkeyAutoMapError("{0} zip içinde bulunamadı.".format(filename))

    def _find_optional_file(self, root_dir, filename):
        """Find an optional file by name and return an empty string if missing."""
        for current_root, _, files in os.walk(root_dir):
            if filename in files:
                return os.path.join(current_root, filename)
        QgsMessageLog.logMessage(
            "Opsiyonel Geofabrik katmanı bulunamadı: {0}".format(filename),
            LOG_TAG,
            Qgis.Warning,
        )
        return ""

    def _build_boundary_layer(self, gadm_path):
        """Create a memory layer containing only the selected province."""
        source_layer = QgsVectorLayer(gadm_path, "GADM TUR Level 1", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("GADM il sınırı katmanı yüklenemedi.")

        if GADM_NAME_FIELD not in [field.name() for field in source_layer.fields()]:
            raise TurkeyAutoMapError(
                'GADM katmanında "{0}" alanı bulunamadı.'.format(GADM_NAME_FIELD)
            )

        memory_uri = "{0}?crs={1}".format(
            QgsWkbTypes.displayString(source_layer.wkbType()),
            source_layer.crs().authid(),
        )
        boundary_layer = QgsVectorLayer(
            memory_uri,
            BOUNDARY_LAYER_NAME.format(province=self.province_label),
            "memory",
        )
        provider = boundary_layer.dataProvider()
        provider.addAttributes(source_layer.fields())
        boundary_layer.updateFields()

        wanted = self._normalize_name(self.province_gadm_name)
        selected_features = []
        for feature in source_layer.getFeatures(QgsFeatureRequest()):
            current_name = str(feature[GADM_NAME_FIELD])
            if self._normalize_name(current_name) == wanted:
                new_feature = QgsFeature(boundary_layer.fields())
                new_feature.setAttributes(feature.attributes())
                new_feature.setGeometry(feature.geometry())
                selected_features.append(new_feature)

        if not selected_features:
            raise ProvinceNotFoundError(
                "{0} ili GADM verisinde bulunamadı.".format(self.province_label)
            )

        provider.addFeatures(selected_features)
        boundary_layer.updateExtents()
        return boundary_layer

    def _build_district_layer(self, district_path):
        """Create a memory layer with all districts of the selected province."""
        source_layer = QgsVectorLayer(district_path, "GADM TUR Level 2", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("GADM ilçe sınırı katmanı yüklenemedi.")

        if GADM_NAME_FIELD not in [field.name() for field in source_layer.fields()]:
            raise TurkeyAutoMapError(
                'GADM ilçe katmanında "{0}" alanı bulunamadı.'.format(GADM_NAME_FIELD)
            )

        districts_layer = self._create_memory_layer_like(
            source_layer,
            DISTRICTS_LAYER_NAME.format(province=self.province_label),
        )
        provider = districts_layer.dataProvider()
        wanted = self._normalize_name(self.province_gadm_name)
        selected_features = []

        for feature in source_layer.getFeatures(QgsFeatureRequest()):
            current_name = str(feature[GADM_NAME_FIELD])
            if self._normalize_name(current_name) == wanted:
                new_feature = QgsFeature(districts_layer.fields())
                new_feature.setAttributes(feature.attributes())
                new_feature.setGeometry(feature.geometry())
                selected_features.append(new_feature)

        if not selected_features:
            raise TurkeyAutoMapError(
                "{0} için GADM ilçe sınırları bulunamadı.".format(self.province_label)
            )

        provider.addFeatures(selected_features)
        districts_layer.updateExtents()
        return districts_layer

    def _build_focus_district_layer(self, district_path, district_name):
        """Create a memory layer containing only the selected focus district."""
        source_layer = QgsVectorLayer(district_path, "GADM TUR Level 2", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("GADM odak ilçe katmanı yüklenemedi.")

        required_fields = [GADM_NAME_FIELD, DISTRICT_NAME_FIELD]
        available_fields = [field.name() for field in source_layer.fields()]
        for field_name in required_fields:
            if field_name not in available_fields:
                raise TurkeyAutoMapError(
                    'GADM ilçe katmanında "{0}" alanı bulunamadı.'.format(field_name)
                )

        focus_layer = self._create_memory_layer_like(
            source_layer,
            FOCUS_DISTRICT_LAYER_NAME.format(district=district_name),
        )
        provider = focus_layer.dataProvider()
        wanted_province = self._normalize_name(self.province_gadm_name)
        wanted_district = self._normalize_name(district_name)
        selected_features = []

        for feature in source_layer.getFeatures(QgsFeatureRequest()):
            province_name = self._normalize_name(str(feature[GADM_NAME_FIELD]))
            current_district = self._normalize_name(str(feature[DISTRICT_NAME_FIELD]))
            if province_name == wanted_province and current_district == wanted_district:
                new_feature = QgsFeature(focus_layer.fields())
                new_feature.setAttributes(feature.attributes())
                new_feature.setGeometry(feature.geometry())
                selected_features.append(new_feature)

        if not selected_features:
            raise TurkeyAutoMapError(
                "{0} ili içinde '{1}' ilçesi GADM verisinde bulunamadı.".format(
                    self.province_label,
                    district_name,
                )
            )

        provider.addFeatures(selected_features)
        focus_layer.updateExtents()
        return focus_layer

    def _first_attribute(self, layer, field_name):
        """Return the first feature attribute value from a layer."""
        for feature in layer.getFeatures(QgsFeatureRequest()):
            return str(feature[field_name])
        return ""

    def _build_neighbor_layer(self, gadm_path, boundary_layer):
        """Create a memory layer with provinces adjacent to the selected province."""
        source_layer = QgsVectorLayer(gadm_path, "GADM TUR Level 1", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("GADM komşu il katmanı yüklenemedi.")

        neighbors_layer = self._create_memory_layer_like(
            source_layer,
            NEIGHBORS_LAYER_NAME.format(province=self.province_label),
        )
        provider = neighbors_layer.dataProvider()
        selected_geometry = self._combined_geometry(boundary_layer)
        selected_name = self._normalize_name(self.province_gadm_name)
        neighbor_features = []

        request = QgsFeatureRequest().setFilterRect(selected_geometry.boundingBox())
        for feature in source_layer.getFeatures(request):
            current_name = self._normalize_name(str(feature[GADM_NAME_FIELD]))
            if current_name == selected_name:
                continue

            geometry = feature.geometry()
            if geometry and (
                geometry.touches(selected_geometry)
                or geometry.intersects(selected_geometry)
                or geometry.distance(selected_geometry) <= 0.00001
            ):
                new_feature = QgsFeature(neighbors_layer.fields())
                new_feature.setAttributes(feature.attributes())
                new_feature.setGeometry(geometry)
                neighbor_features.append(new_feature)

        provider.addFeatures(neighbor_features)
        neighbors_layer.updateExtents()
        return neighbors_layer

    def _build_turkey_locator_layer(self, gadm_path):
        """Create a memory layer containing all Turkish provinces for locator maps."""
        source_layer = QgsVectorLayer(gadm_path, "GADM TUR Level 1", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("GADM Türkiye locator katmanı yüklenemedi.")

        locator_layer = self._create_memory_layer_like(source_layer, TURKEY_LOCATOR_LAYER_NAME)
        provider = locator_layer.dataProvider()
        features = []
        for feature in source_layer.getFeatures(QgsFeatureRequest()):
            new_feature = QgsFeature(locator_layer.fields())
            new_feature.setAttributes(feature.attributes())
            new_feature.setGeometry(feature.geometry())
            features.append(new_feature)

        provider.addFeatures(features)
        locator_layer.updateExtents()
        return locator_layer

    def _build_places_layer(self, places_path, boundary_layer):
        """Create a point layer for province and district center labels."""
        source_layer = QgsVectorLayer(places_path, "Geofabrik OSM Places", "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError("Geofabrik yerleşim katmanı yüklenemedi.")
        if OSM_CLASS_FIELD not in [field.name() for field in source_layer.fields()]:
            raise TurkeyAutoMapError(
                'Geofabrik yerleşim katmanında "{0}" alanı bulunamadı.'.format(
                    OSM_CLASS_FIELD
                )
            )

        places_layer = self._create_memory_layer_like(
            source_layer,
            PLACES_LAYER_NAME.format(province=self.province_label),
        )
        provider = places_layer.dataProvider()
        boundary_geometry = self._combined_geometry(boundary_layer)
        selected_features = []
        allowed_classes = {"city", "town"}

        request = QgsFeatureRequest().setFilterRect(boundary_geometry.boundingBox())
        for feature in source_layer.getFeatures(request):
            feature_class = str(feature[OSM_CLASS_FIELD]).lower()
            if feature_class not in allowed_classes:
                continue

            geometry = feature.geometry()
            if not geometry or geometry.isEmpty():
                continue
            if not geometry.intersects(boundary_geometry):
                continue

            new_feature = QgsFeature(places_layer.fields())
            new_feature.setAttributes(feature.attributes())
            new_feature.setGeometry(geometry)
            selected_features.append(new_feature)

        provider.addFeatures(selected_features)
        places_layer.updateExtents()
        return places_layer

    def _prepare_context_water_layers(self, waterways_path, water_areas_path, boundary_layer):
        """Prepare separate optional water layers from Geofabrik OSM data."""
        if waterways_path:
            if self.options.get("show_major_waterways", True):
                self._check_cancelled()
                self.status_changed.emit("Büyük akarsular hazırlanıyor...")
                major_layer = self._build_filtered_osm_layer(
                    waterways_path,
                    MAJOR_WATERWAYS_LAYER_NAME.format(province=self.province_label),
                    boundary_layer,
                    {"river", "canal"},
                )
                self._write_vector_layer(
                    major_layer,
                    self.major_waterways_output,
                    "major_waterways",
                )
            else:
                self.major_waterways_output = ""

            if self.options.get("show_minor_waterways", False):
                self._check_cancelled()
                self.status_changed.emit("Küçük akarsular hazırlanıyor...")
                minor_layer = self._build_filtered_osm_layer(
                    waterways_path,
                    MINOR_WATERWAYS_LAYER_NAME.format(province=self.province_label),
                    boundary_layer,
                    {"stream", "drain", "ditch"},
                )
                self._write_vector_layer(
                    minor_layer,
                    self.minor_waterways_output,
                    "minor_waterways",
                )
            else:
                self.minor_waterways_output = ""
        else:
            self.major_waterways_output = ""
            self.minor_waterways_output = ""

        if water_areas_path:
            water_context_layer = self._buffer_layer(boundary_layer, 0.20)
            if self.options.get("show_lakes", True):
                self._check_cancelled()
                self.status_changed.emit("Göller hazırlanıyor...")
                lakes_layer = self._build_filtered_osm_layer(
                    water_areas_path,
                    LAKES_LAYER_NAME.format(province=self.province_label),
                    water_context_layer,
                    {"water", "lake", "pond"},
                    excluded_classes={"reservoir", "riverbank", "dock"},
                )
                self._write_vector_layer(lakes_layer, self.lakes_output, "lakes")
            else:
                self.lakes_output = ""

            if self.options.get("show_reservoirs", True):
                self._check_cancelled()
                self.status_changed.emit("Baraj ve rezervuarlar hazırlanıyor...")
                reservoirs_layer = self._build_filtered_osm_layer(
                    water_areas_path,
                    RESERVOIRS_LAYER_NAME.format(province=self.province_label),
                    water_context_layer,
                    {"reservoir", "dam"},
                )
                self._write_vector_layer(
                    reservoirs_layer,
                    self.reservoirs_output,
                    "reservoirs",
                )
            else:
                self.reservoirs_output = ""

            if self.options.get("show_sea_context", True):
                self._check_cancelled()
                self.status_changed.emit("Deniz ve kıyı bağlamı hazırlanıyor...")
                sea_layer = self._build_filtered_osm_layer(
                    water_areas_path,
                    SEA_CONTEXT_LAYER_NAME.format(province=self.province_label),
                    water_context_layer,
                    {"water", "sea", "ocean", "bay", "strait"},
                    excluded_classes={"reservoir", "riverbank", "dock"},
                    exclude_intersection_layer=boundary_layer,
                )
                self._write_vector_layer(
                    sea_layer,
                    self.sea_context_output,
                    "sea_context",
                )
            else:
                self.sea_context_output = ""
        else:
            self.lakes_output = ""
            self.reservoirs_output = ""
            self.sea_context_output = ""

    def _build_filtered_osm_layer(
        self,
        input_path,
        layer_name,
        overlay_layer,
        included_classes,
        excluded_classes=None,
        exclude_intersection_layer=None,
    ):
        """Build a memory layer filtered by OSM fclass and overlay intersection."""
        source_layer = QgsVectorLayer(input_path, os.path.basename(input_path), "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError(
                "Geofabrik katmanı yüklenemedi: {0}".format(os.path.basename(input_path))
            )
        if OSM_CLASS_FIELD not in [field.name() for field in source_layer.fields()]:
            raise TurkeyAutoMapError(
                'Geofabrik katmanında "{0}" alanı bulunamadı.'.format(OSM_CLASS_FIELD)
            )

        output_layer = self._create_memory_layer_like(source_layer, layer_name)
        provider = output_layer.dataProvider()
        overlay_geometry = self._combined_geometry(overlay_layer)
        excluded_geometry = (
            self._combined_geometry(exclude_intersection_layer)
            if exclude_intersection_layer is not None
            else None
        )
        excluded_classes = excluded_classes or set()
        selected_features = []

        request = QgsFeatureRequest().setFilterRect(overlay_geometry.boundingBox())
        for feature in source_layer.getFeatures(request):
            feature_class = str(feature[OSM_CLASS_FIELD]).lower()
            if feature_class in excluded_classes:
                continue
            if included_classes and feature_class not in included_classes:
                continue

            geometry = feature.geometry()
            if not geometry or geometry.isEmpty():
                continue
            if not geometry.intersects(overlay_geometry):
                continue
            if excluded_geometry is not None and geometry.intersects(excluded_geometry):
                continue

            new_feature = QgsFeature(output_layer.fields())
            new_feature.setAttributes(feature.attributes())
            new_feature.setGeometry(geometry)
            selected_features.append(new_feature)

        provider.addFeatures(selected_features)
        output_layer.updateExtents()
        return output_layer

    def _clip_layer_to_overlay(self, input_path, overlay_layer, output_path):
        """Clip a vector file to an overlay layer and write the result."""
        source_layer = QgsVectorLayer(input_path, os.path.basename(input_path), "ogr")
        if not source_layer.isValid():
            raise TurkeyAutoMapError(
                "Geofabrik katmanı yüklenemedi: {0}".format(os.path.basename(input_path))
            )

        processing.run(
            "native:clip",
            {
                "INPUT": source_layer,
                "OVERLAY": overlay_layer,
                "OUTPUT": output_path,
            },
        )

    def _buffer_layer(self, layer, distance):
        """Create a dissolved buffer layer for contextual water features."""
        result = processing.run(
            "native:buffer",
            {
                "INPUT": layer,
                "DISTANCE": distance,
                "SEGMENTS": 8,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )
        return result["OUTPUT"]

    def _create_memory_layer_like(self, source_layer, name):
        """Create an empty memory layer with the source geometry, CRS, and fields."""
        memory_uri = "{0}?crs={1}".format(
            QgsWkbTypes.displayString(source_layer.wkbType()),
            source_layer.crs().authid(),
        )
        memory_layer = QgsVectorLayer(memory_uri, name, "memory")
        provider = memory_layer.dataProvider()
        provider.addAttributes(source_layer.fields())
        memory_layer.updateFields()
        return memory_layer

    def _combined_geometry(self, layer):
        """Return one geometry containing all features from a vector layer."""
        geometries = [feature.geometry() for feature in layer.getFeatures()]
        if not geometries:
            raise TurkeyAutoMapError("İl sınırı geometrisi boş.")

        combined = geometries[0]
        for geometry in geometries[1:]:
            combined = combined.combine(geometry)
        return combined

    def _write_vector_layer(self, layer, path, layer_name):
        """Persist a vector layer to GeoPackage for loading after task completion."""
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = "UTF-8"
        transform_context = QgsProject.instance().transformContext()
        result = QgsVectorFileWriter.writeAsVectorFormatV2(
            layer,
            path,
            transform_context,
            options,
        )
        error_code = result[0] if isinstance(result, tuple) else result
        if error_code != QgsVectorFileWriter.NoError:
            raise TurkeyAutoMapError(
                "Katman GeoPackage olarak yazılamadı: {0}".format(path)
            )

    def _requested_focus_district_name(self):
        """Return the district name needed for focus, clipping, or highlight."""
        if (
            self.options.get("district_focus")
            or self.options.get("road_scope") == "district"
        ):
            return self.options.get("district_name", "").strip()
        if self.options.get("highlight_district"):
            return self.options.get("highlight_district_name", "").strip()
        return ""

    def _check_cancelled(self):
        """Raise a controlled exception when the task is cancelled."""
        if self.isCanceled():
            raise TurkeyAutoMapError("İşlem kullanıcı tarafından iptal edildi.")

    def _safe_name(self, value):
        """Return a filesystem-safe ASCII-ish name for generated outputs."""
        normalized = self._normalize_name(value)
        return re.sub(r"[^a-z0-9_]+", "_", normalized).strip("_")

    def _normalize_name(self, value):
        """Normalize Turkish and ASCII province names for robust matching."""
        replacements = {
            "ı": "i",
            "İ": "I",
            "ğ": "g",
            "Ğ": "G",
            "ü": "u",
            "Ü": "U",
            "ş": "s",
            "Ş": "S",
            "ö": "o",
            "Ö": "O",
            "ç": "c",
            "Ç": "C",
        }
        text = str(value).strip()
        for source, target in replacements.items():
            text = text.replace(source, target)
        text = unicodedata.normalize("NFKD", text)
        text = "".join(char for char in text if not unicodedata.combining(char))
        return text.lower()


class TurkeyAutoMap(QObject):
    """QGIS plugin entry point and GUI coordinator."""

    def __init__(self, iface):
        """Store QGIS interface references and plugin paths."""
        super().__init__()
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dialog = None
        self.action = None
        self.task = None

    def initGui(self):
        """Create toolbar and menu actions for the plugin."""
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.action = QAction(QIcon(icon_path), "TurkeyAutoMap", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(PLUGIN_MENU, self.action)

    def unload(self):
        """Remove plugin actions from the QGIS GUI."""
        if self.action is not None:
            self.iface.removePluginVectorMenu(PLUGIN_MENU, self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Show the plugin dialog and initialize it if needed."""
        if self.dialog is None:
            self.dialog = TurkeyAutoMapDialog(self.iface.mainWindow())
            self._populate_provinces()
            self.dialog.createButton.clicked.connect(self.create_map)
            self.dialog.clearCacheButton.clicked.connect(self.clear_cache)
            self.dialog.saveButton.clicked.connect(self.save_project)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _populate_provinces(self):
        """Fill the province combo box with alphabetically sorted Turkish names."""
        self.dialog.provinceComboBox.clear()
        for label, gadm_name in PROVINCES:
            self.dialog.provinceComboBox.addItem(label, gadm_name)

    def create_map(self):
        """Start a background task for the selected province."""
        if self.task is not None:
            QMessageBox.information(
                self.dialog,
                "TurkeyAutoMap",
                "Devam eden bir işlem var. Lütfen tamamlanmasını bekleyin.",
            )
            return

        province_label = self.dialog.provinceComboBox.currentText()
        province_gadm_name = self.dialog.provinceComboBox.currentData()
        options = self._collect_options()
        if (
            (
                options.get("district_focus")
                or options.get("road_scope") == "district"
            )
            and not options.get("district_name")
        ):
            QMessageBox.warning(
                self.dialog,
                "TurkeyAutoMap",
                "İlçe odak modu veya ilçe yolları için odak ilçe adını yazmalısınız.",
            )
            return
        if (
            options.get("highlight_district")
            and not options.get("highlight_district_name")
        ):
            QMessageBox.warning(
                self.dialog,
                "TurkeyAutoMap",
                "Sadece ilçe vurgulama için vurgulanacak ilçe adını yazmalısınız.",
            )
            return

        self.dialog.progressBar.setValue(0)
        self.dialog.statusLabel.setText("Hazırlanıyor...")
        self.dialog.set_busy(True)

        self.task = MapBuildTask(
            province_label,
            province_gadm_name,
            self.plugin_dir,
            options,
        )
        self.task.status_changed.connect(self.dialog.statusLabel.setText)
        self.task.progressChanged.connect(self._on_task_progress)
        self.task.taskCompleted.connect(self._on_task_completed)
        self.task.taskTerminated.connect(self._on_task_terminated)
        QgsApplication.taskManager().addTask(self.task)

    def _collect_options(self):
        """Read map generation options from the dialog widgets."""
        theme_label = self.dialog.themeComboBox.currentText()
        return {
            "theme": THEME_KEYS_BY_LABEL.get(theme_label, "professional"),
            "palette": PALETTE_KEYS_BY_LABEL.get(
                self.dialog.paletteComboBox.currentText(),
                "vivid",
            ),
            "paper_size": self.dialog.paperSizeComboBox.currentText(),
            "orientation": self.dialog.orientationComboBox.currentText(),
            "road_scope": self._road_scope_from_label(
                self.dialog.roadScopeComboBox.currentText()
            ),
            "district_color": self.dialog.districtColorCheckBox.isChecked(),
            "province_highlight": self.dialog.provinceHighlightCheckBox.isChecked(),
            "dynamic_legend": self.dialog.dynamicLegendCheckBox.isChecked(),
            "district_focus": self.dialog.districtFocusCheckBox.isChecked(),
            "district_name": self.dialog.districtFocusLineEdit.text().strip(),
            "highlight_district": self.dialog.highlightDistrictCheckBox.isChecked(),
            "highlight_district_name": (
                self.dialog.highlightDistrictLineEdit.text().strip()
            ),
            "highlight_color": HIGHLIGHT_COLORS_BY_LABEL.get(
                self.dialog.highlightColorComboBox.currentText(),
                "auto",
            ),
            "show_neighbors": self.dialog.showNeighborsCheckBox.isChecked(),
            "neighbor_style": self._neighbor_style_from_label(
                self.dialog.neighborStyleComboBox.currentText()
            ),
            "neighbor_labels": self.dialog.neighborLabelsCheckBox.isChecked(),
            "show_places": self.dialog.showPlacesCheckBox.isChecked(),
            "place_labels": self.dialog.placeLabelsCheckBox.isChecked(),
            "show_major_waterways": self.dialog.showMajorWaterwaysCheckBox.isChecked(),
            "show_minor_waterways": self.dialog.showMinorWaterwaysCheckBox.isChecked(),
            "show_lakes": self.dialog.showLakesCheckBox.isChecked(),
            "show_reservoirs": self.dialog.showReservoirsCheckBox.isChecked(),
            "show_sea_context": self.dialog.showSeaContextCheckBox.isChecked(),
            "water_labels": self.dialog.waterLabelsCheckBox.isChecked(),
            "basemap": BASEMAPS_BY_LABEL.get(
                self.dialog.basemapComboBox.currentText()
            ),
            "inset_map": self.dialog.insetMapCheckBox.isChecked(),
            "locator_mode": self.dialog.locatorModeComboBox.currentText(),
        }

    def _road_scope_from_label(self, label):
        """Map the road scope combo text to an internal option value."""
        if label == "Odak ilçe yolları":
            return "district"
        if label == "Yol ağı yok":
            return "none"
        return "province"

    def _neighbor_style_from_label(self, label):
        """Map neighboring province style text to an internal option value."""
        if label == "Dolgulu sınır":
            return "filled"
        return "outline"

    def clear_cache(self):
        """Delete generated outputs after removing open plugin layers."""
        cache_dir = stable_cache_dir()
        generated_dir = os.path.join(cache_dir, "generated")
        try:
            self._remove_plugin_layers_from_project()
            if os.path.isdir(generated_dir):
                shutil.rmtree(generated_dir)
            os.makedirs(cache_dir, exist_ok=True)
            self.dialog.progressBar.setValue(0)
            self.dialog.statusLabel.setText(
                "Geçici harita çıktıları temizlendi. İndirilen zip dosyaları korundu."
            )
            self.iface.messageBar().pushInfo(
                PLUGIN_NAME,
                "Geçici çıktılar temizlendi; GADM/Geofabrik zip dosyaları korundu.",
            )
        except PermissionError:
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)
            QMessageBox.warning(
                self.dialog,
                "TurkeyAutoMap",
                "Bazı dosyalar QGIS tarafından kullanılıyor. Katmanları projeden "
                "kaldırıp QGIS'i yeniden başlattıktan sonra tekrar deneyin.",
            )
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Critical)
            QMessageBox.critical(
                self.dialog,
                "TurkeyAutoMap",
                "Önbellek temizlenirken hata oluştu.",
            )

    def _remove_plugin_layers_from_project(self):
        """Remove TurkeyAutoMap generated layers so Windows releases GeoPackage locks."""
        cache_dir = os.path.normcase(os.path.abspath(stable_cache_dir()))
        project = QgsProject.instance()
        remove_ids = []
        plugin_group_names = {
            "Merkezler",
            "Ulaşım",
            "Akarsular",
            "İdari Sınırlar",
            "Su Alanları",
            "Altlık Harita",
        }

        for layer_id, layer in project.mapLayers().items():
            source = layer.source() if hasattr(layer, "source") else ""
            source_path = source.split("|", 1)[0]
            layer_name = layer.name() if hasattr(layer, "name") else ""
            if source_path.startswith("type=xyz") and layer_name.startswith("Altlık Harita"):
                remove_ids.append(layer_id)
                continue

            normalized_source = os.path.normcase(os.path.abspath(source_path))
            if normalized_source.startswith(cache_dir) or self._is_plugin_layer_name(layer_name):
                remove_ids.append(layer_id)
        if remove_ids:
            project.removeMapLayers(remove_ids)
        self._remove_plugin_groups(project.layerTreeRoot(), plugin_group_names)

    def _is_plugin_layer_name(self, layer_name):
        """Return True for layer names generated by TurkeyAutoMap."""
        markers = (
            " İl Sınırı",
            " İlçe Sınırları",
            " İlçe Odağı",
            " Komşu İlleri",
            " Yol Ağı",
            " İl ve İlçe Merkezleri",
            " Büyük Akarsular",
            " Küçük Akarsular",
            " Göller",
            " Baraj ve Rezervuarlar",
            " Deniz ve Kıyı Bağlamı",
            "Altlık Harita -",
            "Türkiye İl Konum Haritası",
        )
        return any(marker in layer_name for marker in markers)

    def _remove_plugin_groups(self, group, group_names):
        """Remove empty or plugin-named layer tree groups recursively."""
        for child in list(group.children()):
            if hasattr(child, "children"):
                self._remove_plugin_groups(child, group_names)
                if child.name() in group_names:
                    group.removeChildNode(child)

    def _add_layers_to_tree_grouped(self, root, groups):
        """Add visible layers to the layer tree in compact thematic groups."""
        for group_name, layers in groups:
            valid_layers = [layer for layer in layers if layer is not None]
            if not valid_layers:
                continue
            if len(valid_layers) == 1 and group_name in ("Merkezler", "Ulaşım"):
                root.addLayer(valid_layers[0])
                continue
            group = root.addGroup(group_name)
            for layer in valid_layers:
                group.addLayer(layer)

    def save_project(self):
        """Save the current QGIS project as a .qgz file."""
        path, _ = QFileDialog.getSaveFileName(
            self.dialog,
            "QGIS projesini kaydet",
            os.path.expanduser("~/turkey_auto_map.qgz"),
            SAVE_FILTER,
        )
        if not path:
            return
        if not path.lower().endswith(".qgz"):
            path += ".qgz"

        try:
            if QgsProject.instance().write(path):
                self.dialog.statusLabel.setText("Proje kaydedildi: {0}".format(path))
                self.iface.messageBar().pushSuccess(PLUGIN_NAME, "Proje kaydedildi.")
            else:
                raise TurkeyAutoMapError("QGIS proje dosyası yazılamadı.")
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Critical)
            QMessageBox.critical(
                self.dialog,
                "TurkeyAutoMap",
                "Proje kaydedilirken hata oluştu.",
            )

    def _on_task_progress(self, progress):
        """Update the progress bar from the task progress signal."""
        self.dialog.progressBar.setValue(int(progress))

    def _load_optional_output_layer(self, path, name):
        """Load an optional generated layer if the output file exists."""
        if path and os.path.exists(path):
            layer = QgsVectorLayer(path, name, "ogr")
            if layer.isValid() and layer.featureCount() == 0:
                return None
            return layer
        return None

    def _create_basemap_layer(self, basemap):
        """Create an optional XYZ basemap layer compatible with QGIS/QMS sources."""
        if not basemap:
            return None

        for source in self._basemap_xyz_sources(basemap["url"]):
            layer = QgsRasterLayer(source, basemap["name"], "wms")
            if layer.isValid():
                QgsMessageLog.logMessage(
                    "Altlık harita eklendi: {0}".format(basemap["name"]),
                    LOG_TAG,
                    Qgis.Info,
                )
                return layer

        QgsMessageLog.logMessage(
            "Altlık harita eklenemedi: {0}".format(basemap["name"]),
            LOG_TAG,
            Qgis.Warning,
        )
        return None

    def _basemap_xyz_sources(self, url):
        """Return several QGIS XYZ URI variants for maximum compatibility."""
        encoded_query_url = urllib.parse.quote(url, safe=":/{}")
        fully_encoded_url = urllib.parse.quote(url, safe="")
        return [
            "type=xyz&url={0}&zmin=0&zmax=20&crs=EPSG3857".format(
                encoded_query_url
            ),
            "type=xyz&url={0}&zmin=0&zmax=20&crs=EPSG3857".format(
                fully_encoded_url
            ),
            "type=xyz&url={0}&zmin=0&zmax=20&crs=EPSG3857".format(url),
        ]

    def _on_task_completed(self):
        """Load generated layers, style them, and zoom to the province."""
        try:
            task = self.task
            if task is None:
                return

            boundary_layer = QgsVectorLayer(
                task.boundary_output,
                BOUNDARY_LAYER_NAME.format(province=task.province_label),
                "ogr",
            )
            districts_layer = QgsVectorLayer(
                task.districts_output,
                DISTRICTS_LAYER_NAME.format(province=task.province_label),
                "ogr",
            )
            neighbors_layer = self._load_optional_output_layer(
                task.neighbors_output,
                NEIGHBORS_LAYER_NAME.format(province=task.province_label),
            )
            turkey_locator_layer = QgsVectorLayer(
                task.turkey_locator_output,
                TURKEY_LOCATOR_LAYER_NAME,
                "ogr",
            )
            focus_layer = None
            if task.focus_district_output:
                focus_layer = QgsVectorLayer(
                    task.focus_district_output,
                    FOCUS_DISTRICT_LAYER_NAME.format(
                        district=task.focus_district_name
                        or task.options.get("district_name", "")
                    ),
                    "ogr",
                )
            roads_layer = self._load_optional_output_layer(
                task.roads_output,
                ROADS_LAYER_NAME.format(province=task.province_label),
            )
            places_layer = None
            if task.places_output and os.path.exists(task.places_output):
                places_layer = QgsVectorLayer(
                    task.places_output,
                    PLACES_LAYER_NAME.format(province=task.province_label),
                    "ogr",
                )
                if places_layer.isValid() and places_layer.featureCount() == 0:
                    places_layer = None
            major_waterways_layer = self._load_optional_output_layer(
                task.major_waterways_output,
                MAJOR_WATERWAYS_LAYER_NAME.format(province=task.province_label),
            )
            minor_waterways_layer = self._load_optional_output_layer(
                task.minor_waterways_output,
                MINOR_WATERWAYS_LAYER_NAME.format(province=task.province_label),
            )
            lakes_layer = self._load_optional_output_layer(
                task.lakes_output,
                LAKES_LAYER_NAME.format(province=task.province_label),
            )
            reservoirs_layer = self._load_optional_output_layer(
                task.reservoirs_output,
                RESERVOIRS_LAYER_NAME.format(province=task.province_label),
            )
            sea_context_layer = self._load_optional_output_layer(
                task.sea_context_output,
                SEA_CONTEXT_LAYER_NAME.format(province=task.province_label),
            )
            if not boundary_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan il sınırı katmanı yüklenemedi.")
            if not districts_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan ilçe sınırı katmanı yüklenemedi.")
            if neighbors_layer is not None and not neighbors_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan komşu iller katmanı yüklenemedi.")
            if not turkey_locator_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan Türkiye locator katmanı yüklenemedi.")
            if focus_layer is not None and not focus_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan odak ilçe katmanı yüklenemedi.")
            if roads_layer is not None and not roads_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan yol katmanı yüklenemedi.")
            if places_layer is not None and not places_layer.isValid():
                raise TurkeyAutoMapError("Oluşturulan yerleşim merkezi katmanı yüklenemedi.")
            optional_layers = [
                major_waterways_layer,
                minor_waterways_layer,
                lakes_layer,
                reservoirs_layer,
                sea_context_layer,
            ]
            if any(layer is not None and not layer.isValid() for layer in optional_layers):
                raise TurkeyAutoMapError("Oluşturulan su bağlamı katmanlarından biri yüklenemedi.")

            theme = self._theme(task.options.get("theme"))
            if sea_context_layer is not None:
                self._style_water_areas(sea_context_layer, theme, "sea")
            if lakes_layer is not None:
                self._style_water_areas(lakes_layer, theme, "lake")
            if reservoirs_layer is not None:
                self._style_water_areas(reservoirs_layer, theme, "reservoir")
            if neighbors_layer is not None:
                self._style_neighbors(
                    neighbors_layer,
                    theme,
                    task.options.get("neighbor_style", "outline"),
                )
            if neighbors_layer is not None and task.options.get("neighbor_labels", False):
                self._enable_neighbor_labels(neighbors_layer, theme)
            self._style_districts(
                districts_layer,
                theme,
                task.options.get("district_color", False),
                task.options.get("palette", "vivid"),
            )
            if focus_layer is not None:
                self._style_focus_district(
                    focus_layer,
                    theme,
                    task.options.get("highlight_color", "auto"),
                )
            self._style_boundary(
                boundary_layer,
                theme,
                task.options.get("province_highlight", True),
            )
            self._style_turkey_locator(turkey_locator_layer, theme)
            if major_waterways_layer is not None:
                self._style_waterways(major_waterways_layer, theme, "major")
            if minor_waterways_layer is not None:
                self._style_waterways(minor_waterways_layer, theme, "minor")
            if roads_layer is not None:
                self._style_roads(roads_layer, task.options.get("theme"))
            if places_layer is not None:
                self._style_places(
                    places_layer,
                    theme,
                    task.options.get("place_labels", False),
                )
            if task.options.get("water_labels", False):
                for water_layer in optional_layers:
                    if water_layer is not None:
                        self._enable_named_labels(
                            water_layer,
                            theme,
                            point_size=7,
                            color="#1d4ed8",
                        )
            project = QgsProject.instance()
            root = project.layerTreeRoot()
            basemap_layer = self._create_basemap_layer(task.options.get("basemap"))
            if basemap_layer is not None:
                project.addMapLayer(basemap_layer, False)
            for layer in [sea_context_layer, lakes_layer, reservoirs_layer]:
                if layer is not None:
                    project.addMapLayer(layer, False)
            if neighbors_layer is not None:
                project.addMapLayer(neighbors_layer, False)
            project.addMapLayer(districts_layer, False)
            if focus_layer is not None:
                project.addMapLayer(focus_layer, False)
            for layer in [major_waterways_layer, minor_waterways_layer]:
                if layer is not None:
                    project.addMapLayer(layer, False)
            if roads_layer is not None:
                project.addMapLayer(roads_layer, False)
            if places_layer is not None:
                project.addMapLayer(places_layer, False)
            project.addMapLayer(boundary_layer, False)
            project.addMapLayer(turkey_locator_layer, False)
            self._add_layers_to_tree_grouped(
                root,
                [
                    (
                        "Merkezler",
                        [places_layer],
                    ),
                    (
                        "Ulaşım",
                        [roads_layer],
                    ),
                    (
                        "Akarsular",
                        [major_waterways_layer, minor_waterways_layer],
                    ),
                    (
                        "İdari Sınırlar",
                        [focus_layer, boundary_layer, districts_layer, neighbors_layer],
                    ),
                    (
                        "Su Alanları",
                        [reservoirs_layer, lakes_layer, sea_context_layer],
                    ),
                    (
                        "Altlık Harita",
                        [basemap_layer],
                    ),
                ],
            )

            canvas = self.iface.mapCanvas()
            focus_extent_layer = (
                focus_layer
                if focus_layer is not None and task.options.get("district_focus")
                else boundary_layer
            )
            canvas.setExtent(self._transformed_extent(focus_extent_layer))
            canvas.refresh()
            try:
                self._create_professional_layout(
                    task.province_label,
                    boundary_layer,
                    districts_layer,
                    neighbors_layer,
                    turkey_locator_layer,
                    roads_layer,
                    focus_layer,
                    places_layer,
                    major_waterways_layer,
                    minor_waterways_layer,
                    lakes_layer,
                    reservoirs_layer,
                    sea_context_layer,
                    task.options,
                )
            except Exception:  # pylint: disable=broad-except
                QgsMessageLog.logMessage(
                    traceback.format_exc(),
                    LOG_TAG,
                    Qgis.Critical,
                )
                self.iface.messageBar().pushWarning(
                    PLUGIN_NAME,
                    "Katmanlar eklendi; layout oluşturulurken hata oluştu.",
                )

            message = READY_MESSAGE.format(province=task.province_label)
            self.dialog.statusLabel.setText(message)
            self.dialog.progressBar.setValue(100)
            self.iface.messageBar().pushSuccess(PLUGIN_NAME, message)
            self.iface.mainWindow().statusBar().showMessage(message)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Critical)
            QMessageBox.critical(
                self.dialog,
                "TurkeyAutoMap",
                "Katmanlar haritaya eklenirken hata oluştu.",
            )
            self.dialog.progressBar.setValue(0)
        finally:
            self.dialog.set_busy(False)
            self.task = None

    def _on_task_terminated(self):
        """Show task errors and reset the dialog state."""
        task = self.task
        error = task.error if task is not None else None
        message = str(error) if error else "İşlem tamamlanamadı."

        if isinstance(error, ProvinceNotFoundError):
            QMessageBox.warning(self.dialog, "TurkeyAutoMap", message)
        else:
            QMessageBox.critical(self.dialog, "TurkeyAutoMap", message)

        self.dialog.statusLabel.setText(message)
        self.dialog.progressBar.setValue(0)
        self.dialog.set_busy(False)
        self.task = None

    def _style_boundary(self, layer, theme, highlighted=True):
        """Apply transparent fill and black outline styling to province layer."""
        symbol = QgsFillSymbol.createSimple(
            {
                "style": "no",
                "outline_color": theme["boundary"],
                "outline_width": "1.25" if highlighted else "0.55",
                "outline_width_unit": "MM",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    def _style_districts(self, layer, theme, use_district_colors, palette_key):
        """Apply subtle dashed line styling to district boundaries."""
        if use_district_colors and DISTRICT_NAME_FIELD in [
            field.name() for field in layer.fields()
        ]:
            categories = []
            palette = DISTRICT_PALETTES.get(
                palette_key,
                theme.get("district_palette", DISTRICT_PALETTES["vivid"]),
            )
            field_index = layer.fields().indexFromName(DISTRICT_NAME_FIELD)
            for index, district_name in enumerate(sorted(layer.uniqueValues(field_index))):
                color = QColor(palette[index % len(palette)])
                color.setAlpha(150)
                symbol = QgsFillSymbol.createSimple(
                    {
                        "color": "{0},{1},{2},{3}".format(
                            color.red(),
                            color.green(),
                            color.blue(),
                            color.alpha(),
                        ),
                        "outline_color": theme["district_outline"],
                        "outline_style": "dash",
                        "outline_width": "0.22",
                        "outline_width_unit": "MM",
                    }
                )
                try:
                    symbol.setColor(color)
                except Exception:  # pylint: disable=broad-except
                    pass
                categories.append(
                    QgsRendererCategory(str(district_name), symbol, str(district_name))
                )
            layer.setRenderer(
                QgsCategorizedSymbolRenderer(DISTRICT_NAME_FIELD, categories)
            )
        else:
            symbol = QgsFillSymbol.createSimple(
                {
                    "style": "no",
                    "outline_color": "55,65,81,230",
                    "outline_style": "dash",
                    "outline_width": "0.32",
                    "outline_width_unit": "MM",
                }
            )
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        try:
            self._enable_district_labels(layer, theme)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)
        layer.triggerRepaint()

    def _style_neighbors(self, layer, theme, neighbor_style="outline"):
        """Apply muted contextual styling to neighboring provinces."""
        fill_color = (
            theme.get("neighbor_fill", "236,239,241,110")
            if neighbor_style == "filled"
            else "255,255,255,0"
        )
        symbol = QgsFillSymbol.createSimple(
            {
                "color": fill_color,
                "outline_color": theme.get("neighbor_outline", "60,60,60,210"),
                "outline_width": "0.34",
                "outline_width_unit": "MM",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    def _style_water_areas(self, layer, theme, water_type):
        """Apply quiet blue styling to lakes, reservoirs, dams, and sea context."""
        styles = {
            "lake": ("147,197,253,105", "59,130,246,170", "0.18"),
            "reservoir": ("125,211,252,105", "14,116,144,175", "0.20"),
            "sea": ("191,219,254,35", "96,165,250,120", "0.10"),
        }
        fill, outline, width = styles.get(water_type, styles["lake"])
        symbol = QgsFillSymbol.createSimple(
            {
                "color": fill,
                "outline_color": outline,
                "outline_width": width,
                "outline_width_unit": "MM",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    def _style_waterways(self, layer, theme, size_class):
        """Apply blue line styling to rivers and streams."""
        color = "#0047ff" if size_class == "major" else "#38bdf8"
        width = "1.55" if size_class == "major" else "0.75"
        symbol = QgsLineSymbol.createSimple(
            {
                "color": color,
                "width": width,
                "width_unit": "Pixel",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    def _style_places(self, layer, theme, labels_enabled=False):
        """Apply point styling and labels to province and district centers."""
        categories = []
        for value, label, color, size in [
            ("city", "İl Merkezi", theme.get("focus", "#d000ff"), 3.6),
            ("town", "İlçe Merkezi", "#ffffff", 2.6),
        ]:
            outline_color = (
                "#111827" if value == "city" else theme.get("focus", "#d000ff")
            )
            symbol = QgsMarkerSymbol.createSimple(
                {
                    "name": "star" if value == "city" else "circle",
                    "color": color,
                    "outline_color": outline_color,
                    "outline_width": "0.40",
                    "outline_width_unit": "MM",
                    "size": str(size),
                    "size_unit": "MM",
                }
            )
            categories.append(QgsRendererCategory(value, symbol, label))

        renderer = QgsCategorizedSymbolRenderer(OSM_CLASS_FIELD, categories)
        layer.setRenderer(renderer)
        if labels_enabled:
            try:
                self._enable_named_labels(layer, theme, point_size=8)
            except Exception:  # pylint: disable=broad-except
                QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)
        layer.triggerRepaint()

    def _style_focus_district(self, layer, theme, highlight_color="auto"):
        """Apply prominent styling to the selected focus district."""
        focus_color = self._highlight_color(theme, highlight_color)
        symbol = QgsFillSymbol.createSimple(
            {
                "color": self._rgba_from_hex(focus_color, 32),
                "outline_color": focus_color,
                "outline_width": "1.45",
                "outline_width_unit": "MM",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        try:
            self._enable_district_labels(layer, theme, point_size=10)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)
        layer.triggerRepaint()

    def _highlight_color(self, theme, requested_color):
        """Return a clear district highlight color for the active theme."""
        if requested_color and requested_color != "auto":
            return requested_color
        return theme.get("focus", "#d000ff")

    def _rgba_from_hex(self, color_hex, alpha):
        """Convert a hex color to a QGIS rgba string."""
        color = QColor(color_hex)
        if not color.isValid():
            color = QColor("#d000ff")
        return "{0},{1},{2},{3}".format(
            color.red(),
            color.green(),
            color.blue(),
            alpha,
        )

    def _style_turkey_locator(self, layer, theme):
        """Apply muted style to all-province locator layer."""
        symbol = QgsFillSymbol.createSimple(
            {
                "color": "245,245,245,100",
                "outline_color": theme["neighbor_outline"],
                "outline_width": "0.12",
                "outline_width_unit": "MM",
            }
        )
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()

    def _enable_district_labels(self, layer, theme, point_size=7):
        """Enable compact district name labels with a white buffer."""
        if DISTRICT_NAME_FIELD not in [field.name() for field in layer.fields()]:
            return

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", point_size))
        text_format.setSize(point_size)
        text_format.setColor(QColor(theme["label"]))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.0)
        buffer_settings.setColor(QColor(theme["label_buffer"]))
        text_format.setBuffer(buffer_settings)

        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = DISTRICT_NAME_FIELD
        label_settings.placement = self._label_over_point_placement()
        label_settings.setFormat(text_format)

        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)

    def _enable_named_labels(self, layer, theme, point_size=8, color=None):
        """Enable labels from the standard OSM name field."""
        if OSM_NAME_FIELD not in [field.name() for field in layer.fields()]:
            return

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", point_size, QFont.Bold))
        text_format.setSize(point_size)
        text_format.setColor(QColor(color or theme["label"]))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.15)
        buffer_settings.setColor(QColor(theme["label_buffer"]))
        text_format.setBuffer(buffer_settings)

        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = OSM_NAME_FIELD
        label_settings.placement = self._label_over_point_placement()
        label_settings.setFormat(text_format)

        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)

    def _enable_neighbor_labels(self, layer, theme, point_size=8):
        """Enable optional labels for neighboring province names."""
        if GADM_NAME_FIELD not in [field.name() for field in layer.fields()]:
            return

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", point_size))
        text_format.setSize(point_size)
        text_format.setColor(QColor(theme["muted"]))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.2)
        buffer_settings.setColor(QColor(theme["label_buffer"]))
        text_format.setBuffer(buffer_settings)

        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = GADM_NAME_FIELD
        label_settings.placement = self._label_over_point_placement()
        label_settings.setFormat(text_format)

        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)

    def _label_over_point_placement(self):
        """Return the polygon label placement enum for both older and newer QGIS."""
        try:
            return Qgis.LabelPlacement.OverPoint
        except AttributeError:
            return QgsPalLayerSettings.OverPoint

    def _style_roads(self, layer, theme_key):
        """Apply categorized styling based on the OSM fclass road field."""
        road_styles = self._road_styles_for_theme(theme_key)
        categories = []
        for value, label, color, width in road_styles:
            if value == "__other__":
                continue
            symbol = QgsLineSymbol.createSimple(
                {
                    "color": color,
                    "width": str(width + 0.45),
                    "width_unit": "Pixel",
                }
            )
            category_value = "" if value == "__other__" else value
            category = QgsRendererCategory(category_value, symbol, label)
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(ROAD_CLASS_FIELD, categories)
        default_symbol = QgsLineSymbol.createSimple(
            {
                "color": QColor("#d9d9d9").name(),
                "width": "0.5",
                "width_unit": "Pixel",
            }
        )
        renderer.setSourceSymbol(default_symbol)
        renderer.setClassAttribute(ROAD_CLASS_FIELD)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def _road_styles_for_theme(self, theme_key):
        """Return road styles adjusted for the active visual theme."""
        if theme_key == "dark":
            return [
                ("motorway", "Motorway", "#ff4d4d", 3.0),
                ("primary", "Primary", "#ffb86b", 2.0),
                ("secondary", "Secondary", "#facc15", 1.5),
                ("tertiary", "Tertiary", "#cbd5e1", 1.0),
            ]
        if theme_key == "blueprint":
            return [
                ("motorway", "Motorway", "#063d75", 3.0),
                ("primary", "Primary", "#0f75bc", 2.0),
                ("secondary", "Secondary", "#4aa3df", 1.5),
                ("tertiary", "Tertiary", "#79bde8", 1.0),
            ]
        if theme_key == "retro":
            return [
                ("motorway", "Motorway", "#9b2226", 3.0),
                ("primary", "Primary", "#bb7a2a", 2.0),
                ("secondary", "Secondary", "#c9a227", 1.5),
                ("tertiary", "Tertiary", "#7a6a56", 1.0),
            ]
        if theme_key == "minimal":
            return [
                ("motorway", "Motorway", "#111827", 2.6),
                ("primary", "Primary", "#4b5563", 1.8),
                ("secondary", "Secondary", "#9ca3af", 1.3),
                ("tertiary", "Tertiary", "#d1d5db", 0.9),
            ]
        if theme_key == "topo":
            return [
                ("motorway", "Motorway", "#b91c1c", 2.8),
                ("primary", "Primary", "#d97706", 1.9),
                ("secondary", "Secondary", "#ca8a04", 1.4),
                ("tertiary", "Tertiary", "#607d3b", 1.0),
            ]
        if theme_key == "municipal":
            return [
                ("motorway", "Motorway", "#c1121f", 3.0),
                ("primary", "Primary", "#f77f00", 2.0),
                ("secondary", "Secondary", "#fcbf49", 1.5),
                ("tertiary", "Tertiary", "#6b7280", 1.0),
            ]
        if theme_key == "contrast":
            return [
                ("motorway", "Motorway", "#000000", 3.2),
                ("primary", "Primary", "#333333", 2.2),
                ("secondary", "Secondary", "#666666", 1.6),
                ("tertiary", "Tertiary", "#999999", 1.1),
            ]
        return ROAD_STYLES

    def _create_professional_layout(
        self,
        province,
        boundary_layer,
        districts_layer,
        neighbors_layer,
        turkey_locator_layer,
        roads_layer,
        focus_layer,
        places_layer,
        major_waterways_layer,
        minor_waterways_layer,
        lakes_layer,
        reservoirs_layer,
        sea_context_layer,
        options,
    ):
        """Create a print layout with title, map, legend, scale bar, and north arrow."""
        project = QgsProject.instance()
        layout_name = LAYOUT_NAME.format(province=province)
        theme = self._theme(options.get("theme"))
        manager = project.layoutManager()

        existing = manager.layoutByName(layout_name)
        if existing is not None:
            manager.removeLayout(existing)

        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layout_name)
        page_size = options.get("paper_size", "A4")
        orientation = options.get("orientation", "Yatay")
        page_width, page_height = self._layout_page_dimensions(page_size, orientation)
        try:
            layout.pageCollection().page(0).setPageSize(
                page_size,
                self._layout_orientation(orientation),
            )
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(
                "Sayfa boyutu ayarlanamadı; varsayılan sayfa kullanılıyor.",
                LOG_TAG,
                Qgis.Warning,
            )
        manager.addLayout(layout)
        self._set_layout_page_background(layout, theme)

        title_text = "{0} İli Lokasyon Haritası".format(province)
        if options.get("district_focus") and focus_layer is not None:
            title_text = "{0} ilçesi ({1}) Lokasyon Haritası".format(
                self._layer_first_attribute(focus_layer, DISTRICT_NAME_FIELD)
                or options.get("district_name", ""),
                province,
            )

        self._add_layout_label(
            layout,
            title_text,
            12,
            8,
            page_width - 96,
            10,
            16,
            QColor(theme["title"]),
            bold=True,
        )

        margin = 12.0
        top = 24.0
        bottom = 10.0
        side_panel_width = 70.0 if page_width >= 297.0 else 58.0
        gutter = 8.0
        map_width = page_width - (margin * 2.0) - side_panel_width - gutter
        map_height = page_height - top - bottom
        side_x = margin + map_width + gutter

        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(margin, top, map_width, map_height)
        map_layers = []
        if places_layer is not None:
            map_layers.append(places_layer)
        if roads_layer is not None:
            map_layers.append(roads_layer)
        for layer in [major_waterways_layer, minor_waterways_layer]:
            if layer is not None:
                map_layers.append(layer)
        if focus_layer is not None:
            map_layers.append(focus_layer)
        map_layers.extend([boundary_layer, districts_layer])
        if neighbors_layer is not None:
            map_layers.append(neighbors_layer)
        for layer in [reservoirs_layer, lakes_layer, sea_context_layer]:
            if layer is not None:
                map_layers.append(layer)
        self._configure_layout_map_layers(map_item, map_layers)
        extent_layer = (
            focus_layer
            if focus_layer is not None and options.get("district_focus")
            else boundary_layer
        )
        extent = self._transformed_extent(extent_layer)
        extent.scale(1.15)
        map_item.setExtent(extent)
        map_item.setFrameEnabled(True)
        map_item.setFrameStrokeColor(QColor(theme["map_frame"]))
        map_item.setFrameStrokeWidth(
            QgsLayoutMeasurement(0.25, self._layout_millimeters_unit())
        )
        map_item.attemptMove(QgsLayoutPoint(margin, top, self._layout_millimeters_unit()))
        map_item.attemptResize(QgsLayoutSize(map_width, map_height, self._layout_millimeters_unit()))
        layout.addLayoutItem(map_item)

        locator_mode = options.get("locator_mode", "Otomatik")
        locator_focus_layer = (
            focus_layer
            if focus_layer is not None
            and (
                options.get("district_focus")
                or self._locator_mode_is_district(locator_mode)
            )
            else None
        )
        locator_should_show = (
            options.get("inset_map", True)
            and self._locator_enabled(locator_mode)
            and (
                locator_focus_layer is not None
                or self._locator_mode_is_province(locator_mode)
                or locator_mode == "Otomatik"
            )
        )
        locator_height = min(52.0, map_height * 0.25) if locator_should_show else 0.0
        legend_y = top + locator_height + (11.0 if locator_should_show else 0.0)
        legend_height = max(
            42.0,
            map_height - locator_height - (11.0 if locator_should_show else 0.0),
        )

        if locator_should_show:
            self._add_locator_map(
                layout=layout,
                boundary_layer=boundary_layer,
                districts_layer=districts_layer,
                focus_layer=locator_focus_layer,
                turkey_locator_layer=turkey_locator_layer,
                x_pos=side_x,
                y_pos=top + 7.0,
                width=side_panel_width,
                height=locator_height - 7.0,
                theme=theme,
                locator_mode=locator_mode,
            )

        self._add_editable_legend(
            layout,
            map_item,
            ([places_layer] if places_layer is not None else [])
            + ([roads_layer] if roads_layer is not None else [])
            + ([major_waterways_layer] if major_waterways_layer is not None else [])
            + ([minor_waterways_layer] if minor_waterways_layer is not None else [])
            + ([focus_layer] if focus_layer is not None else [])
            + [boundary_layer, districts_layer]
            + ([neighbors_layer] if neighbors_layer is not None else [])
            + ([reservoirs_layer] if reservoirs_layer is not None else [])
            + ([lakes_layer] if lakes_layer is not None else [])
            + ([sea_context_layer] if sea_context_layer is not None else []),
            options.get("dynamic_legend", True),
            side_x,
            legend_y,
            side_panel_width,
            legend_height,
        )

        scale_bar = QgsLayoutItemScaleBar(layout)
        scale_bar.setStyle("Line Ticks Middle")
        scale_bar.setLinkedMap(map_item)
        scale_bar.setUnits(self._distance_kilometers_unit())
        scale_bar.setUnitLabel("km")
        try:
            scale_bar.setMapUnitsPerScaleBarUnit(1000)
        except Exception:  # pylint: disable=broad-except
            pass
        scale_bar.setNumberOfSegments(3)
        scale_bar.setNumberOfSegmentsLeft(0)
        scale_bar.setHeight(2.2)
        scale_bar.setLineWidth(0.25)
        try:
            scale_bar.setFont(QFont("Arial", 7))
        except Exception:  # pylint: disable=broad-except
            pass
        scale_bar.applyDefaultSize()
        scale_bar.attemptResize(QgsLayoutSize(62, 10, self._layout_millimeters_unit()))
        scale_bar.attemptMove(
            QgsLayoutPoint(margin + 6, top + map_height - 12, self._layout_millimeters_unit())
        )
        layout.addLayoutItem(scale_bar)

        north_arrow_path = self._north_arrow_path()
        if north_arrow_path:
            north_arrow = QgsLayoutItemPicture(layout)
            north_arrow.setLinkedMap(map_item)
            north_arrow.setPicturePath(north_arrow_path)
            north_arrow.attemptMove(
                QgsLayoutPoint(
                    margin + map_width - 25,
                    top + 6,
                    self._layout_millimeters_unit(),
                )
            )
            north_arrow.attemptResize(
                QgsLayoutSize(14, 14, self._layout_millimeters_unit())
            )
            layout.addLayoutItem(north_arrow)
        else:
            north_arrow_label = QgsLayoutItemLabel(layout)
            north_arrow_label.setText("K\n↑")
            north_arrow_label.setFont(QFont("Arial", 10, QFont.Bold))
            north_arrow_label.setHAlign(Qt.AlignCenter)
            north_arrow_label.attemptMove(
                QgsLayoutPoint(
                    margin + map_width - 25,
                    top + 6,
                    self._layout_millimeters_unit(),
                )
            )
            north_arrow_label.attemptResize(
                QgsLayoutSize(14, 14, self._layout_millimeters_unit())
            )
            layout.addLayoutItem(north_arrow_label)

    def _add_layout_label(
        self,
        layout,
        text,
        x_pos,
        y_pos,
        width,
        height,
        point_size,
        color,
        bold=False,
    ):
        """Add a consistently styled label to a layout."""
        label = QgsLayoutItemLabel(layout)
        label.setText(text)
        self._set_layout_label_format(label, point_size, color, bold)
        label.setHAlign(Qt.AlignLeft)
        label.setVAlign(Qt.AlignVCenter)
        label.attemptMove(QgsLayoutPoint(x_pos, y_pos, self._layout_millimeters_unit()))
        label.attemptResize(QgsLayoutSize(width, height, self._layout_millimeters_unit()))
        layout.addLayoutItem(label)
        return label

    def _configure_layout_map_layers(self, map_item, layers):
        """Set initial map layers while allowing later project layer changes."""
        try:
            map_item.setKeepLayerSet(False)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)

    def _add_editable_legend(
        self,
        layout,
        map_item,
        layers,
        dynamic_legend,
        x_pos,
        y_pos,
        width,
        height,
    ):
        """Add a native editable QGIS legend with a controlled layer list."""
        legend = QgsLayoutItemLegend(layout)
        legend.setTitle("Açıklamalar")
        legend.setLinkedMap(map_item)
        try:
            legend.setLegendFilterByMapEnabled(True)
        except AttributeError:
            pass

        try:
            legend.setAutoUpdateModel(True)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)

        try:
            legend.setStyleFont(QgsLegendStyle.Title, QFont("Arial", 11, QFont.Bold))
            legend.setStyleFont(QgsLegendStyle.Group, QFont("Arial", 8, QFont.Bold))
            legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont("Arial", 7))
        except Exception:  # pylint: disable=broad-except
            pass

        legend.attemptMove(QgsLayoutPoint(x_pos, y_pos, self._layout_millimeters_unit()))
        legend.attemptResize(QgsLayoutSize(width, height, self._layout_millimeters_unit()))
        layout.addLayoutItem(legend)
        return legend

    def _add_locator_map(
        self,
        layout,
        boundary_layer,
        districts_layer,
        focus_layer,
        turkey_locator_layer,
        x_pos,
        y_pos,
        width,
        height,
        theme,
        locator_mode,
    ):
        """Add a locator map for province-in-country or district-in-province context."""
        show_province = self._locator_mode_is_province(locator_mode) or (
            locator_mode == "Otomatik" and focus_layer is None
        )
        title = "İlin Türkiye Konumu" if show_province else "İlçe Konumu"
        self._add_layout_label(
            layout,
            title,
            x_pos,
            y_pos - 7,
            width,
            6,
            8,
            QColor(theme["title"]),
            bold=True,
        )
        inset = QgsLayoutItemMap(layout)
        inset.setRect(x_pos, y_pos, width, height)
        if show_province:
            inset.setLayers([boundary_layer, turkey_locator_layer])
            extent = self._transformed_extent(turkey_locator_layer)
            extent.scale(1.05)
        else:
            inset.setLayers([focus_layer, districts_layer, boundary_layer])
            extent = self._transformed_extent(boundary_layer)
            extent.scale(1.12)
        inset.setExtent(extent)
        inset.setFrameEnabled(True)
        inset.setFrameStrokeColor(QColor(theme["map_frame"]))
        inset.setFrameStrokeWidth(
            QgsLayoutMeasurement(0.25, self._layout_millimeters_unit())
        )
        inset.attemptMove(QgsLayoutPoint(x_pos, y_pos, self._layout_millimeters_unit()))
        inset.attemptResize(QgsLayoutSize(width, height, self._layout_millimeters_unit()))
        layout.addLayoutItem(inset)

    def _locator_mode_is_province(self, locator_mode):
        """Return True when locator should show the province inside Turkey."""
        return locator_mode == "İli Türkiye içinde göster"

    def _locator_mode_is_district(self, locator_mode):
        """Return True when locator should show the district inside the province."""
        return locator_mode == "İlçeyi il içinde göster"

    def _locator_enabled(self, locator_mode):
        """Return True when the locator map should be added."""
        return locator_mode != "Konum haritası yok"

    def _theme(self, theme_key):
        """Return a visual theme dictionary with a safe fallback."""
        return THEMES.get(theme_key or "professional", THEMES["professional"])

    def _transformed_extent(self, layer):
        """Return a layer extent transformed to the current project CRS."""
        destination_crs = QgsProject.instance().crs()
        source_crs = layer.crs()
        extent = layer.extent()
        if not source_crs.isValid() or source_crs == destination_crs:
            return extent

        transform = QgsCoordinateTransform(
            source_crs,
            destination_crs,
            QgsProject.instance(),
        )
        return transform.transformBoundingBox(extent)

    def _layer_first_attribute(self, layer, field_name):
        """Read the first attribute from a loaded vector layer."""
        if layer is None:
            return ""
        for feature in layer.getFeatures(QgsFeatureRequest()):
            return str(feature[field_name])
        return ""

    def _set_layout_page_background(self, layout, theme):
        """Apply theme background color to the first layout page when supported."""
        try:
            page = layout.pageCollection().page(0)
            symbol = QgsFillSymbol.createSimple(
                {
                    "color": theme["page_bg"],
                    "outline_style": "no",
                }
            )
            page.setPageStyleSymbol(symbol)
        except Exception:  # pylint: disable=broad-except
            QgsMessageLog.logMessage(traceback.format_exc(), LOG_TAG, Qgis.Warning)

    def _distance_kilometers_unit(self):
        """Return kilometer distance unit enum for QGIS 3.16 through 3.44+."""
        try:
            return Qgis.DistanceUnit.Kilometers
        except AttributeError:
            return QgsUnitTypes.DistanceKilometers

    def _layout_millimeters_unit(self):
        """Return millimeter layout unit enum for QGIS 3.16 through 3.44+."""
        try:
            return Qgis.LayoutUnit.Millimeters
        except AttributeError:
            return QgsUnitTypes.LayoutMillimeters

    def _layout_page_dimensions(self, page_size, orientation):
        """Return layout page dimensions in millimeters."""
        width, height = PAGE_SIZES_MM.get(page_size, PAGE_SIZES_MM["A4"])
        if orientation == "Dikey":
            return min(width, height), max(width, height)
        return max(width, height), min(width, height)

    def _layout_orientation(self, orientation):
        """Return QGIS page orientation enum."""
        if orientation == "Dikey":
            return QgsLayoutItemPage.Portrait
        return QgsLayoutItemPage.Landscape

    def _set_layout_label_format(self, label, point_size, color, bold=False):
        """Set layout label font using the modern API with an older API fallback."""
        font = QFont("Arial", point_size, QFont.Bold if bold else QFont.Normal)
        text_format = QgsTextFormat()
        text_format.setFont(font)
        text_format.setSize(point_size)
        text_format.setColor(color)
        try:
            label.setTextFormat(text_format)
        except AttributeError:
            label.setFont(font)
            label.setFontColor(color)

    def _north_arrow_path(self):
        """Return an available QGIS north arrow SVG path."""
        preferred_names = (
            "NorthArrow_04.svg",
            "NorthArrow_03.svg",
            "NorthArrow_02.svg",
            "NorthArrow_01.svg",
        )
        for svg_root in QgsApplication.svgPaths():
            for root, _, files in os.walk(svg_root):
                for preferred_name in preferred_names:
                    if preferred_name in files:
                        return os.path.join(root, preferred_name)
        return ""
