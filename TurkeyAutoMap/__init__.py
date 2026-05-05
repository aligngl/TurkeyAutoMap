"""TurkeyAutoMap QGIS plugin package.

Kurulum:
1. Bu klasoru QGIS profilinizdeki python/plugins dizinine kopyalayin.
2. QGIS'i yeniden baslatin.
3. Eklentiler > Eklentileri Yonet ve Kur ekranindan TurkeyAutoMap'i etkinlestirin.
"""


def classFactory(iface):
    """Return the plugin class instance for QGIS."""
    from .turkey_auto_map import TurkeyAutoMap

    return TurkeyAutoMap(iface)
