DOMAIN = "bergfex"
CONF_SKI_AREA = "ski_area"
CONF_COUNTRY = "country"
CONF_LANGUAGE = "language"
CONF_DOMAIN = "domain"
COORDINATORS = "coordinators"
BASE_URL = "https://www.bergfex.at"


# Dictionary of countries and their corresponding snow report URL paths
COUNTRIES = {
    "Österreich": "/oesterreich/schneewerte/",
    "Deutschland": "/deutschland/schneewerte/",
    "Schweiz": "/schweiz/schneewerte/",
    "Italien": "/italien/schneewerte/",
    "Frankreich": "/frankreich/schneewerte/",
    "Slowenien": "/slowenien/schneewerte/",
    "Tschechien": "/tschechien/schneewerte/",
    "Polen": "/polen/schneewerte/",
    "Slowakei": "/slowakei/schneewerte/",
}

SUPPORTED_LANGUAGES = {
    "at": {"name": "Deutsch", "domain": "https://www.bergfex.at"},
    "en": {"name": "English", "domain": "https://www.bergfex.com"},
    "fr": {"name": "Français", "domain": "https://www.bergfex.fr"},
    "it": {"name": "Italiano", "domain": "https://it.bergfex.com"},
    "es": {"name": "Español", "domain": "https://www.bergfex.es"},
    "nl": {"name": "Nederlands", "domain": "https://nl.bergfex.com"},
    "se": {"name": "Svenska", "domain": "https://se.bergfex.com"},
    "no": {"name": "Norsk", "domain": "https://no.bergfex.com"},
    "dk": {"name": "Dansk", "domain": "https://dk.bergfex.com"},
    "fi": {"name": "Suomi", "domain": "https://fi.bergfex.com"},
    "hu": {"name": "Magyar", "domain": "https://hu.bergfex.com"},
    "cz": {"name": "Český", "domain": "https://www.bergfex.cz"},
    "sk": {"name": "Slovensky", "domain": "https://www.bergfex.sk"},
    "pl": {"name": "Polski", "domain": "https://www.bergfex.pl"},
    "hr": {"name": "Hrvatski", "domain": "https://hr.bergfex.com"},
    "si": {"name": "Slovenščina", "domain": "https://www.bergfex.si"},
    "ru": {"name": "Русский", "domain": "https://ru.bergfex.com"},
    "ro": {"name": "Română", "domain": "https://ro.bergfex.com"},
}

# Keywords for parsing across different languages
KEYWORDS = {
    "at": {
        "mountain": "Berg",
        "valley": "Tal",
        "snow_depth": "Schneehöhe",
        "snow_condition": "Schneezustand",
        "last_snowfall": "Letzter Schneefall",
        "avalanche": "Lawinenwarnstufe",
        "lifts": "Offene Lifte",
        "pistes": "Offene Pisten",
        "slope_condition": "Pistenzustand",
        "today": "heute",
        "yesterday": "gestern",
        "from": "von",
    },
    "en": {
        "mountain": "Mountain",
        "valley": "Valley",
        "snow_depth": "Snow depth",
        "snow_condition": "Snow condition",
        "last_snowfall": "Last snowfall",
        "avalanche": "Avalanche",
        "lifts": "Open lifts",
        "pistes": "Open pistes",
        "slope_condition": "Slope condition",
        "today": "today",
        "yesterday": "yesterday",
        "from": "of",
    },
    "fr": {
        "mountain": "Montagne",
        "valley": "Vallée",
        "snow_depth": "Hauteur de neige",
        "snow_condition": "Conditions de neige",
        "last_snowfall": "Dernière chute de neige",
        "avalanche": "Risque d'avalanche",
        "lifts": "Remontées ouvertes",
        "pistes": "Pistes ouvertes",
        "slope_condition": "Etat des pistes",
        "today": "aujourd'hui",
        "yesterday": "hier",
        "from": "de",
    },
    "it": {
        "mountain": "Montagna",
        "valley": "Valle",
        "snow_depth": "Altezza neve",
        "snow_condition": "Condizioni neve",
        "last_snowfall": "Ultima nevicata",
        "avalanche": "valanghe",
        "lifts": "Impianti aperti",
        "pistes": "Piste aperte",
        "slope_condition": "Condizioni piste",
        "today": "oggi",
        "yesterday": "ieri",
        "from": "di",
    },
    "es": {
        "mountain": "Montaña",
        "valley": "Valle",
        "snow_depth": "Altura de la nieve",
        "snow_condition": "Estado de la nieve",
        "last_snowfall": "Última nevada",
        "avalanche": "aludes",
        "lifts": "Remontes abiertos",
        "pistes": "Pistas abiertas",
        "slope_condition": "Estado de las pistas",
        "today": "hoy",
        "yesterday": "ayer",
        "from": "de",
    },
    "nl": {
        "mountain": "Berg",
        "valley": "Dal",
        "snow_depth": "Sneeuwhoogte",
        "snow_condition": "Sneeuwconditie",
        "last_snowfall": "Laatste sneeuwval",
        "avalanche": "Lawinegevaar",
        "lifts": "Open liften",
        "pistes": "Open pistes",
        "slope_condition": "Pisteconditie",
        "today": "vandaag",
        "yesterday": "gisteren",
        "from": "van",
    },
    # Add other languages as needed or use a fallback mechanism
}
