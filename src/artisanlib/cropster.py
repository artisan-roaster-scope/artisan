#
# ABOUT
# Cropster XLS Roast Profile importer for Artisan

import time as libtime
import xlrd # type: ignore
import logging
from typing import Final, Union, List, Set, Sequence, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # pylint: disable=unused-import
    from artisanlib.atypes import ProfileData # pylint: disable=unused-import

try:
    from PyQt6.QtCore import QDateTime, Qt # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import QApplication # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import QDateTime, Qt # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import QApplication # type: ignore # @UnusedImport @Reimport  @UnresolvedImport

from artisanlib.util import encodeLocal


_log: Final[logging.Logger] = logging.getLogger(__name__)

# returns a dict containing all profile information contained in the given Cropster XLS file
def extractProfileCropsterXLS(file:str, aw:'ApplicationWindow') -> 'ProfileData':

    def takeClosest(num:float, collection:List[float]) -> float:
        return min(collection, key=lambda x:abs(x-num))

    res:ProfileData = ProfileData() # the interpreted data set

    book = xlrd.open_workbook(file)

    sheet_names:List[str] = book.sheet_names()

    id_tag_trans:List[str] = [
        'Id-Tag',  # EN
        'ID-Tag',  # DE
        'Etiqueta de identificaci\u00f3n', # ES
        "N\u00b0 d'identification",        # FR
        'Codice ID',   # IT
        'ID-Tag',      # PT
        'ID-\u0442ег', # RU
        'ID-Tag',      # KO
        'ID-\u30bf\u30b0',      # JP
        'ID\uff0d\u6807\u7b7e', # CN simplified
        '\u7de8\u865f\u0020\u002d\u0020\u6a19\u7c64'] # CN traditional

    date_trans:List[str] = [
        'Date',  # EN
        'Datum', # DE
        'Fecha', # ES
        'Date',  # FR
        'Data',  # IT, PT
        '\u0414\u0430\u0442\u0430', # RU
        '\ub0a0\uc9dc', # KO
        '\u65e5\u4ed8', # JP
        '\u65e5\u671f', # CN simplified
        '\u65e5\u671f', # CN traditional
    ]

    sensory_score_tag_trans = [ # 16
        'Sensorial score',  # EN
        'Sensorisches Ergebnis', # DE
        'Resultados del análisis sensorial', # ES
        'Note sensorielle', # FR
        'Punteggio sensoriale', # IT
        'Pontuação sensorial',  # PT
        '\u041e\u0446\u0435\u043d\u043a\u0430\u0020\u0432\u043a\u0443\u0441\u043e\u0432\u044b\u0445\u0020\u043a\u0430\u0447\u0435\u0441\u0442\u0432', # RU
        '\uc13c\uc11c\ub9ac\u0020\uc810\uc218', # KO
        '\u77e5\u899a\u30b9\u30b3\u30a2', # JP
        '\u611f\u5b98\u7279\u5f81\u5206\u6570', # CN simplified
        '\u611f\u5b98\u7279\u5fb5\u5206\u6578', # CN traditional
    ]

    # list of Artisan tags for integers associated to tuple of (fixed) column nr (or Null) and list of tag translations
    int_tag_labels_trans = [
        ('whole_color', 26, [
            'Roast value',              # EN
            'Röstwert',                 # DE
            'Nivel de tueste',          # ES
            'Couleur de torréfaction',  # FR
            'Grado di tostatura',       # IT
            'Grau de torra',            # PT
            '\u0421\u0442\u0435\u043f\u0435\u043d\u044c\u0020\u043e\u0431\u0436\u0430\u0440\u043a\u0438', # RU
            '\ub85c\uc2a4\ud2b8\u0020\uac12', # KO
            '\u7119\u714e\u6570\u5024', # JP
            '\u70d8\u7119\u8272\u503c', # CN Simplified
            '\u70d8\u7119\u8272\u503c', # CN Traditional
            ]),
        ('ground_color', 27, [
            'Roast value 2',             # EN
            'Röstwert 2',                # DE
            'Nivel de tueste 2',         # ES
            'Couleur de torréfaction 2', # FR
            'Grado di tostatura 2',      # IT
            'Grau de torra 2',           # PT
            '\u0421\u0442\u0435\u043f\u0435\u043d\u044c\u0020\u043e\u0431\u0436\u0430\u0440\u043a\u0438\u0020\u0032', # RU
            '\ub85c\uc2a4\ud2b8\u0020\uac12\u0020\u0032', # KO
            '\u30ed\u30fc\u30b9\u30c8\u5024\uff12', # JP
            '\u70d8\u7119\u8272\u503c\u0020\u0032', # CN Simplified
            '\u70d8\u7119\u8272\u503c\u0020\u0032', # CN Traditional
            ])]

    # list of Artisan tags for strings associated to tuple of (fixed) column nr (or Null) and list of tag translations
    string_tag_labels_trans = [
        ('beans', 1, [
            'Lot name',                 # EN
            'Chargenname',              # DE
            'Nombre del lote',          # ES
            'Nom du lot',               # FR
            'Nome lotto',               # IT
            'Nome do lote',             # PT
            '\u0418\u043c\u044f\u0020\u043b\u043e\u0442\u0430', # RU
            'Lot \uc774\ub984',         # KO
            '\u30ed\u30c3\u30c8\u540d', # JP
            '\u6279\u6b21\u540d\u79f0', # CN Simplified
            '\u6279\u6b21\u540d\u7a31', # CN Traditional
            ]),
        ('title', 2, [
            'Profile',         # EN
            'Profil',          # DE, FR
            'Perfil',          # ES, pT
            'Profilo',         # IT
            '\u041f\u0440\u043e\u0444\u0438\u043b\u044c', # RU
            '\ud504\ub85c\ud30c\uc77c',                   # KO
            '\u30d7\u30ed\u30d5\u30a1\u30a4\u30eb',       # JP
            '\u66f2\u7ebf\u6863\u6848',                   # CN Simplified
            '\u66f2\u7dda\u6a94\u6848',                   # CN Traditional
            ]),
        ('roastertype', 3,[
            'Machine',            # EN, FR
            'Maschine',           # DE
            'Tostador',           # ES
            'Macchina',           # IT
            'M\u00e1quina',       # PT
            '\u041c\u0430\u0448\u0438\u043d\u0430', # RU
            '\uba38\uc2e0',       # KO
            '\u6a5f\u68b0',       # JP
            '\u70d8\u7119\u673a', # CN Simplified
            '\u70d8\u7119\u6a5f', # CN Traditional
            ]),
        ('operator', 4, [
            'Roast technician',       # EN
            'R\u00f6sttechniker',     # DE
            'T\u00e9cnico de tueste', # ES
            'Torr\u00e9facteur',      # FR
            'Addetto alla tostatura', # IT
            'Mestre de torra',        # PT
            '\u041e\u0431\u0436\u0430\u0440\u0449\u0438\u043a', # RU
            '\ub85c\uc2a4\ud130',     # KO
            '\u30ed\u30fc\u30b9\u30c8\u30c6\u30af\u30cb\u30b7\u30e3\u30f3', # JP
            '\u70d8\u7119\u5e08', # CN Simplified
            '\u70d8\u7119\u5e2b', # CN Traditional
            ]),
        ('cuppingnotes', None, [
            'Sensorial notes',                              # EN
            'Sensorische Notizen',                          # DE
            'Anotaciones sobre el an\u00e1lisis sensorial', # ES
            'Commentaires sensoriels',                      # FR
            'Note sensoriali',                              # IT
            'Observa\u00e7\u00f5es sensoriais',             # PT
            '\u041f\u0440\u0438\u043c\u0435\u0447\u0430\u043d\u0438\u044f\u0020\u043a\u0020\u0430\u043d\u0430\u043b\u0438\u0437\u0443\u0020\u0432\u043a\u0443\u0441\u043e\u0432\u044b\u0445\u0020\u0445\u0430\u0440\u0430\u043a\u0442\u0435\u0440\u0438\u0441\u0442\u0438\u043a', # RU
            '\uc13c\uc11c\ub9ac\u0020\uba54\ubaa8',         # KO
            '\u77e5\u899a\u30e1\u30e2',                     # JP
            '\u611f\u5b98\u7279\u5f81\u9644\u6ce8',         # CN Simplified
            '\u611f\u5b98\u7279\u5fb5\u9644\u8a3b',         # CN Traditional
            ]),
        ('roastingnotes', None, [
            'Roasting notes',                                # EN
            'R\u00f6st-Notizen',                             # DE
            'Anotaciones sobre el tostado',                  # ES
            'Commentaires de torr\u00e9faction',             # FR
            'Note sulla tostatura',                          # IT
            'Observa\u00e7\u00f5es da torrefa\u00e7\u00e3o', # PT
            '\u041f\u0440\u0438\u043c\u0435\u0447\u0430\u043d\u0438\u044f\u0020\u043a\u0020\u043e\u0431\u0436\u0430\u0440\u043a\u0435', # RU
            '\ub85c\uc2a4\ud305\u0020\uba54\ubaa8',          # KO
            '\u30ed\u30fc\u30b9\u30c6\u30a3\u30f3\u30b0\u30ce\u30fc\u30c8', # JP
            '\u70d8\u7119\u7b14\u8bb0',                      # CN Simplified
            '\u70d8\u7119\u7b46\u8a18',                      # CN Traditional
            ])
    ]

    ambient_temp_trans = [
        'Ambient temp.', # EN
        'Raumtemp.',     # DE
        'Temperatura ambiente', # ES
        'Temp. ambiante', # FR, IT, PT
        '\u0422\u0435\u043c\u043f\u002e\u0020\u043e\u043a\u0440\u0443\u0436\u0430\u044e\u0449\u0435\u0433\u043e\u0020\u0432\u043e\u0437\u0434\u0443\u0445\u0430', # RU
        '\uc8fc\ubcc0\u0020\uc628\ub3c4', # KO
        '\u30a2\u30f3\u30d3\u30a8\u30f3\u30c8\u6e29\u5ea6', # JP
        '\u5ba4\u5185\u6e29\u5ea6', # CN Simplified
        '\u5ba4\u5167\u6eab\u5ea6', # CN Traditional
    ]
    start_weight_trans = [
        'Start weight',  # EN
        'Startgewicht',  # DE
        'Peso inicial',  # ES, PT
        'Poids initial', # FR
        'Peso iniziale', # IT
        '\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u044b\u0439\u0020\u0432\u0435\u0441', # RU
        '\uc2dc\uc791\u0020\ubb34\uac8c', # KO
        '\u958b\u59cb\u91cd\u91cf', # JP
        '\u5f00\u59cb\u91cd\u91cf', # CN Simplified
        '\u958b\u59cb\u91cd\u91cf', # CN Traditional
    ]
    start_weight_unit_trans = [
        'Start weight unit',        # EN
        'Einheit Startgewicht',     # DE
        'Unidad de peso inicial',   # ES
        'Unit\u00e9 poids initial', # FR
        'Unit\u00e0 peso iniziale', # IT
        'Unidade do peso inicial',  # PT
        '\u0415\u0434\u0438\u043d\u0438\u0446\u0430\u0020\u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u044f\u0020\u043d\u0430\u0447\u0430\u043b\u044c\u043d\u043e\u0433\u043e\u0020\u0432\u0435\u0441\u0430', # RU
        '\uc2dc\uc791\u0020\ubb34\uac8c\u0020\ub2e8\uc704', # KO
        '\u958b\u59cb\u91cd\u91cf\u30e6\u30cb\u30c3\u30c8', # JP
        '\u5f00\u59cb\u91cd\u91cf\u5355\u4f4d', # CN Simplified
        '\u958b\u59cb\u91cd\u91cf\u55ae\u4f4d', # CN Traditional
    ]
    end_weight_trans = [
        'End weight',  # EN
        'Endgewicht',  # DE
        'Peso final',  # ES, PT
        'Poids final', # FR
        'Peso finale', # IT
        '\u041a\u043e\u043d\u0435\u0447\u043d\u044b\u0439\u0020\u0432\u0435\u0441', # RU
        '\uc885\ub8cc\u0020\ubb34\uac8c', # KO
        '\u958b\u59cb\u91cd\u91cf', # JP
        '\u7ed3\u675f\u91cd\u91cf', # CN Simplified
        '\u7d50\u675f\u91cd\u91cf', # CN Traditional
    ]
    end_weight_unit_trans = [
        'End weight unit',        # EN
        'Einheit Endgewicht',     # DE
        'Unidad de peso final',   # ES
        'Unit\u00e9 poids final', # FR
        'Unit\u00e0 peso finale', # IT
        'Unidade de peso final',  # PT
        '\u0415\u0434\u0438\u043d\u0438\u0446\u0430\u0020\u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u044f\u0020\u043a\u043e\u043d\u0435\u0447\u043d\u043e\u0433\u043e\u0020\u0432\u0435\u0441\u0430', # RU
        '\uc885\ub8cc\u0020\ubb34\uac8c\u0020\ub2e8\uc704', # KO
        '\u958b\u59cb\u91cd\u91cf\u30e6\u30cb\u30c3\u30c8', # JP
        '\u7ed3\u675f\u91cd\u91cf\u5355\u4f4d', # CN Simplified
        '\u7d50\u675f\u91cd\u91cf\u55ae\u4f4d', # CN Traditional
    ]

    turning_point_trans = [
        'Turning point', # EN
        'Wendepunkt', # DE
        'Temperatura de fondo', # ES
        'Point de balance', # FR
        'Punto di flesso', # IT
        'Temperatura de fundo', # PT
        '\u041f\u043e\u0432\u043e\u0440\u043e\u0442\u043d\u0430\u044f\u0020\u0442\u043e\u0447\u043a\u0430', # RU
        '\ud130\ub2dd\u0020\ud3ec\uc778\ud2b8', # KO
        '\u30bf\u30fc\u30cb\u30f3\u30b0\u30dd\u30a4\u30f3\u30c8', # JP
        '\u56de\u6e29\u70b9', # CN Simplified
        '\u56de\u6e29\u9ede', # CN Traditional
    ]

    color_change_trans = [
        'Color change', # EN
        'Farb\u00e4nderung', # DE
        'Cambio de color', # ES
        'Changement de couleur', # FR
        'Cambiamento di colore', # IT
        'Mudan\u00e7a de cor', # PT
        '\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435\u0020\u0446\u0432\u0435\u0442\u0430', # RU
        '\uc0c9\u0020\ubcc0\ud654', # KO
        '\u8272\u306e\u5909\u5316', # JP
        '\u989c\u8272\u53d8\u5316', # CN Simplified
        '\u984f\u8272\u8b8a\u5316', # CN Traditional
    ]
    first_crack_trans = [
        'First crack', # EN
        '1. Crack', # DE
        'Primer crac', # ES
        'Premier crack', # FR
        'Primo Crack', # IT
        'Primeiro crack', # PT
        '\u041f\u0435\u0440\u0432\u044b\u0439\u0020\u0442\u0440\u0435\u0441\u043a', # RU
        '\u0031\ucc28\u0020\ud06c\ub799', # KO
        '\uff11\u30cf\u30bc', # JP
        '\u4e00\u7206', # CN Simplified, Traditional
    ]
    second_crack_trans = [
        'Second crack', # EN, FR
        '2. Crack', # DE
        'Segundo crac', # ES
        'Secondo Crack', # IT
        'Segundo crack', # PT
        '\u0412\u0442\u043e\u0440\u043e\u0439\u0020\u0442\u0440\u0435\u0441\u043a', # RU
        '\u0032\ucc28\u0020\ud06c\ub799', # KO
        '\uff12\u30cf\u30bc', # JP
        '\u4e8c\u7206', # CN Simplified, Traditional
    ]
    gas_trans = [
        'Gas', # EN, DE, ES, IT
        'Gaz', # FR
        'G\u00e1s', # PT
        '\u0413\u0430\u0437', # RU
        '\uac00\uc2a4', # KO
        '\u30ac\u30b9', # JP
        '\u706b\u529b', # CN Timplified, Traditional
    ]
    airflow_trans = [
        'Airflow', # EN, DE
        'Flujo de aire', # ES
        "Arriv\u00e9e d'air", # FR
        "Flusso d'aria", # IT
        'Fluxo de ar', # PT
        '\u0412\u043e\u0437\u0434\u0443\u0448\u043d\u044b\u0439\u0020\u043f\u043e\u0442\u043e\u043a', # RU
        '\uacf5\uae30\u0020\ud750\ub984', # KO
        '\u7a7a\u6c17\u306e\u6d41\u308c', # JP
        '\u98ce\u95e8', # CN Simplified
        '\u98a8\u9580', # CN Traditional
    ]
    comment_trans = [
        'Comment', # EN
        'Kommentar', # DE
        'Comentar', # ES
        'Commentaire', # FR
        'Commento', # IT
        'Coment\u00e1rio', # PT
        '\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439', # RU
        '\ucf54\uba58\ud2b8', # KO
        '\u30b3\u30e1\u30f3\u30c8', # JP
        '\u5907\u6ce8', # CN Simplified
        '\u5099\u8a3b', # CN Traditional
    ]

    # standard curves
    curve_bt_trans = [
        'Curve - Bean temp.', # EN
        'Curve - Bean temperature', # EN new
        'Kurve - Bohnentemp.', # DE
        'Kurve - Bohnentemperatur', # DE new
        'Curva - Temp. del grano', # ES
        'Curva  Temperatura del grano', # ES new
        'Courbe Temp. grain', # FR
        'Courbe Temp\u00e9rature des grains', # FR new
        'Curva - Temp. chicco', # IT
        'Curva - Temperatura del chicco', # IT new
        'Curva - Temp. do gr\u00e3o', # PT
        'Curva - Temperatura do gr\u00e3o', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0437\u0435\u0440\u0435\u043d', # RU
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430\u0020\u0437\u0435\u0440\u0435\u043d', # RU new
        '\ucee4\ube0c\u0020\u002d\u0020\ube48\u0020\uc628\ub3c4', # KO
        '\ucee4\ube0c\u0020\u002d\u0020\ube48(Bean)\u0020\uc628\ub3c4', # KO new
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u8c46\u306e\u6e29\u5ea6\u3002', # JP
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u8c46\u306e\u6e29\u5ea6', # JP new
        '\u66f2\u7ebf\u0020\u002d\u0020\u8c46\u6e29', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u8c46\u6eab', # CH Traditional
    ]
    curve_et_trans = [ # note that we map Exhaust to ET and not Env. Temp. as it is available more often; Env. Temp. is mapped to an extra device curve if available
        'Curve - Exhaust temp.', # EN
        'Curve - Exhaust temperature', # EN new
        'Kurve - Ablufttemp.', # DE
        'Kurve - Ablufttemperatur', # DE new
        'Curva - Temp. de salida', # ES (potentially wrong)
        'Curva  Temperatura de salida', # ES new (potentially wrong)
        'Courbe Temp. \u00e9chappement', # FR
        'Courbe Temp\u00e9rature \u00e9chappement', # FR new
        'Curva - Temp. fumi', # IT
        'Curva - Temperatura dei fumi', # IT new
        'Curva - Temp. de exaust\u00e3o', # PT
        'Curva - Temperatura de exaust\u00e3o', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u043d\u0430\u0020\u0432\u044b\u0445\u043e\u0434\u0435', # RU
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430\u0020\u043d\u0430\u0020\u0432\u044b\u0445\u043e\u0434\u0435', # RU new
        '\ucee4\ube0c\u0020\u002d\u0020\ubc30\uae30\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u6392\u6c17\u6e29\u5ea6\u3002', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u6392\u98ce\u6e29', # CN Simplified, Traditional
    ]

    # extra temperature curves (C-F conversion applicable)

    curve_env_temp_trans = [
        'Curve - Env. temp.', # EN
        'Curve - Env. temperature', # EN new
        'Kurve - Umgebungstemp.', # DE
        'Kurve - Umgebungstemperatur', # DE new
        'Curva - Temp. ambiente', # ES
        'Curva  Temperatura ambiente', # ES new
        'Courbe Temp. env.', # FR
        'Courbe Temp\u00e9rature environnementale', # FR new
        'Curva - Temp. aria in tamburo', # IT
        'Curva - Temperatura aria in tamburo', # IT new
        'Curva - Temp. ambiente', # PT
        'Curva - Temperatura ambiente', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u043e\u043a\u0440\u0443\u0436\u0435\u043d\u0438\u044f', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uc8fc\ubcc0\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u5468\u56f2\u6e29\u5ea6', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u7089\u6e29', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u7210\u6eab', # CN Traditional
    ]
    curve_burner_temp_trans = [
        'Curve - Burner temp.', # EN
        'Curve - Burner temperature', # EN new
        'Kurve - Brennertemp.', # DE
        'Kurve - Brennertemperatur', # DE new
        'Curva - Temp. del quemador', # ES
        'Curva  Temperatura del quemador', # ES new
        'Courbe Temp. br\u00fbleur', # FR
        'Courbe Temp\u00e9rature du br\u00fbleur', # FR new
        'Curva - Temp. bruciatore', # IT
        'Curva - Temperatura bruciatore', # IT new
        'Curva - Temp. do queimador', # PT
        'Curva - Temperatura do Queimado', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0433\u043e\u0440\u0435\u043b\u043a\u0438', # RU
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430\u0020\u0433\u043e\u0440\u0435\u043b\u043a\u0438', # RU new
        '\ucee4\ube0c\u0020\u002d\u0020\ubc84\ub108\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30d0\u30fc\u30ca\u30fc\u6e29\u5ea6', # JP
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30d0\u30fc\u30ca\u30fc\u306e\u6e29\u5ea6', # JP new
        '\u66f2\u7ebf\u0020\u002d\u0020\u71c3\u70df\u5668\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u71c3\u7159\u5668\u6eab\u5ea6', # CN Traditional
    ]
    curve_other_temp_trans = [
        'Curve - Other temp.', # EN
        'Curve - Other temperature', # EN new
        'Kurve - Andere Temp.', # DE
        'Kurve - Andere Temperatur', # DE new
        'Curva - Otras temperaturas', # ES
        'Curva  Otras temperaturas', # ES new
        'Courbe Temp. autre', # FR
        'Courbe Temp\u00e9rature autre', # FR new
        'Curva - Altra temp.', # IT
        'Curva - Altra temperatura', # IT new
        'Curva - Outra temp.', # PT
        'Curva - Outra temperatura', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0414\u0440\u0443\u0433\u0430\u044f\u0020\u0442\u0435\u043c\u043f.', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uae30\ud0c0\u0020\uc628\ub3c4\u002e', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u4ed6\u306e\u6e29\u5ea6', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u5176\u5b83\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u5176\u5b83\u6eab\u5ea6', # CN Traditional
    ]
    curve_stack_temp_trans = [
        'Curve - Stack temp.', # EN
        'Curve - Stack temperatur', # EN new
        'Kurve - Schornsteintemp.', # DE
        'Kurve - Schornsteintemperatur', # DE new
        'Curva - Temp. del tiro', # ES
        'Curva  Temperatura del tiro', # ES new
        'Courbe Temp. broche', # FR
        'Courbe Temp\u00e9rature broche', # FR new
        'Curva - Temp. camino', # IT
        'Curva - Temperatura del camino', # IT new
        'Curva - Temp. do escoamento de', # PT
        'Curva - Temperatura do escoamento de', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0432\u0020\u0434\u044b\u043c\u043e\u0432\u043e\u0439\u0020\u0442\u0440\u0443\u0431\u0435', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uc2a4\ud0dd\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30b9\u30bf\u30c3\u30af\u6e29\u5ea6', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u70df\u56f1\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u7159\u56ea\u6eab\u5ea6', # CN Traditional
    ]
    curve_return_temp_trans = [
        'Curve - Return temp.', # EN
        'Curve - Return temperature', # EN new
        'Kurve - R\u00fccklauftemp.', # DE
        'Kurve - R\u00fccklauftemperatur', # DE new
        'Curva - Temp. de retorno', # ES
        'Curva  Temperatura de retorno', # ES new
        'Courbe Temp. retour', # FR
        "Courbe Temp\u00e9rature d'entr\u00e9e", # FR new
        'Curva - Temp. di ritorno', # IT
        'Curva - Temperatura di ritorno', # IT new
        'Curva - Temperatura de Retorno', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0432\u043e\u0437\u0432\u0440\u0430\u0442\u0430', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\ubc30\uae30\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u623b\u308a\u6e29\u5ea6\u3002', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u7a7a\u6c14\u56de\u7089\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u7a7a\u6c23\u56de\u7210\u6eab\u5ea6', # CN Traditional
    ]
    curve_inlet_temp_trans = [
        'Curve - Inlet temp.', # EN
        'Curve - Inlet temperature', # EN new
        'Kurve - Einlasstemp.', # DE
        'Kurve - Einlasstemperatur', # DE new
        'Curva - Temp. de entrada', # ES
        'Curva  Temperatura de entrada', # ES
        'Courbe Temp. entr\u00e9e', # FR
        'Curva - Temp. in ingresso', # IT
        'Curva - Temperatura in ingresso', # IT new
        'Curva - Temp. do ar de entrada', # PT
        'Curva - Temperatura de entrada', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u043d\u0430\u0020\u0432\u0445\u043e\u0434\u0435', # RU
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430\u0020\u043d\u0430\u0020\u0432\u0445\u043e\u0434\u0435', # RU new
        '\ucee4\ube0c\u0020\u002d\u0020\ud761\uae30\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u5438\u6c17\u53e3\u6e29\u5ea6', # JP
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u5438\u6c17\u6e29\u5ea6', # JP new
        '\u66f2\u7ebf\u0020\u002d\u0020\u8fdb\u98ce\u6e29', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u9032\u98a8\u6eab', # CN Traditional
        '\u66f2\u7dda\u0020\u002d\u0020\u9032\u98a8\u6eab\u5ea6', # CN Traditional new
    ]
    curve_afterburner_temp_trans = [
        'Curve - Afterburner temp.', # EN
        'Curve - Afterburner temperature', # EN new
        'Kurve - Nachbrennertemp.', # DE
        'Kurve - Nachbrennertemperatur', # DE new
        'Curva - Temp. del posquemador', # ES
        'Curva  Temperatura del posquemador', # ES new
        'Courbe Temp. post-combustion', # FR
        'Courbe Temp\u00e9rature post-combustion', # FR new
        'Curva - Temp. bruciafumi', # IT
        'Curva - Temperatura bruciafumi', # IT
        'Curva - Temp. p\u00f3s-combust\u00e3o', # PT
        'Curva - Temperatura p\u00f3s-combust\u00e3o', # PT new
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0432\u0020\u0444\u043e\u0440\u0441\u0430\u0436\u043d\u043e\u0439\u0020\u043a\u0430\u043c\u0435', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uc560\ud504\ud130\ubc84\ub108\u0020\uc628\ub3c4', # KO
        '\ucee4\ube0c\u0020\u002d\u0020\ubc84\ub108\u0020\uc628\ub3c4', # KO new
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30a2\u30d5\u30bf\u30fc\u30d0\u30fc\u30ca\u30fc\u6e29\u5ea6\u3002', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u540e\u7f6e\u71c3\u70df\u5668\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u5f8c\u7f6e\u71c3\u7159\u5668\u6eab\u5ea6', # CN Traditional
    ]
    curve_drum_temp_trans = [
        'Curve - Drum temp.', # EN
        'Curve - Drum temperature', # EN new
        'Kurve - Trommeltemp.', # DE
        'Kurve - Trommeltemperatur', # DE new
        'Curva - Temp. del Tambor', # ES
        'Curva  Temperatura del Tambor', # ES new
        'Courbe Temp. tambour', # FR
        'Courbe Temp\u00e9rature tambour', # FR new
        'Curva - Temp. tamburo', # IT
        'Curva - Temperatura tamburo', # IT new
        'Curva - Temperatura do Tambor', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020\u0431\u0430\u0440\u0430\u0431\u0430\u043d\u0430', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\ub4dc\ub7fc\u0020\uc628\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30c9\u30e9\u30e0\u6e29\u5ea6\u3002', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u9505\u7089\u6e29\u5ea6', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u934b\u7210\u6eab\u5ea6', # CN Traditional
    ]



    # extra non-temperature curves (no temperature conversion)


    curve_gas_control_trans = [
        'Curve - Gas control', # EN
        'Kurve - Gas-Kontrolle', # DE
        'Curva - Control del gas', # ES
        'Curva  Control del gas', # ES new
        'Courbe R\u00e9gulation du d\u00e9bit de g', # FR
        'Curva - Controllo gas', # IT
        'Curva - Controle de g\u00e1s', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435\u0020\u0433\u0430\u0437\u043e\u043c', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uac00\uc2a4\u0020\uc81c\uc5b4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30ac\u30b9\u30b3\u30f3\u30c8\u30ed\u30fc\u30eb', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u706b\u529b\u63a7\u5236', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u706b\u529b\u63a7\u5236', # CN Traditional
    ]
    curve_drum_speed_trans = [
        'Curve - Drum speed', # EN
        'Kurve - Trommelgeschw.', # DE
        'Curva - Velocidad del tambor', # ES
        'Curva  Velocidad del tambor', # ES new
        'Courbe Vitesse du tambour', # FR
        'Curva - Velocit\u00e0 tamburo', # IT
        'Curva - Velocidade do tambor', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0421\u043a\u043e\u0440\u043e\u0441\u0442\u044c\u0020\u0431\u0430\u0440\u0430\u0431\u0430\u043d\u0430', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\ub4dc\ub7fc\u0020\uc18d\ub3c4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30c9\u30e9\u30e0\u30b9\u30d4\u30fc\u30c9', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u8f6c\u901f', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u8f49\u901f', # CN Traditional
    ]
    curve_airflow_trans = [
        'Curve - Airflow', # EN
        'Kurve - Airflow', # DE
        'Curva - Flujo de aire', # ES
        'Curva  Flujo de aire', # ES new
        "Courbe Arriv\u00e9e d'air", # FR
        "Courbe Flux d'air", # FR new
        "Curva - Flusso d'aria", # IT
        'Curva - Fluxo de ar', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0412\u043e\u0437\u0434\u0443\u0448\u043d\u044b\u0439\u0020\u043f\u043e\u0442\u043e\u043a', # RU
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u0020\u0432\u043e\u0437\u0434\u0443\u0448\u043d\u043e\u0433\u043e\u0020\u043f\u043e', # RU new
        '\ucee4\ube0c\u0020\u002d\u0020\uacf5\uae30\u0020\ud750\ub984', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u7a7a\u6c17\u306e\u6d41\u308c', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u98ce\u95e8', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u98a8\u9580', # CN Traditional
    ]
    curve_gas_trans = [
        'Curve - Gas', # EN
        'Kurve - Gas', # DE
        'Curva - Gas', # ES
        'Curva  Gas', # ES new
        'Courbe Gaz', # FR
        'Curva - Gas', # IT
        'Curva - G\u00e1s', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0413\u0430\u0437', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\uac00\uc2a4', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30ac\u30b9', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u706b\u529b', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u706b\u529b', # CN Traditional
    ]
#    curve_gas_comments_trans = [
#        "Curve - Gas comments", # EN
#        "Kurve - Kommentare Gas", # DE
#        "Curva - Comentarios sobre el gas", # ES
#        "Courbe Commentaires de type Gaz", # FR
#        "Curva - Commenti sul Gas", # IT
#        "Curva - Coment\u00e1rios do g\u00e1s", # PT
#        "\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438\u0020\u043f\u043e\u0020\u043f\u043e\u0432\u043e\u0434\u0443",  # RU
#        "\ucee4\ube0c\u0020\u002d\u0020\uac00\uc2a4\u0020\ucf54\uba58\ud2b8", # KO
#        "\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30ac\u30b9\u306b\u3064\u3044\u3066\u306e\u30b3\u30e1\u30f3\u30c8", # JP
#        "\u66f2\u7ebf\u0020\u002d\u0020\u706b\u529b\u5907\u6ce8", # CN Simplified
#        "\u66f2\u7dda\u0020\u002d\u0020\u706b\u529b\u5099\u8a3b", # CN Traditional
#    ]
    curve_drum_pressure_trans = [
        'Curve - Drum pressure', # EN
        'Kurve - Trommeldruck', # DE
        'Curva - Presi\u00f3n del tambor', # ES
        'Curva  Presi\u00f3n del tambor', # ES new
        'Courbe Pression du tambour', # FR
        'Curva - Pressione tamburo', # IT
        'Curva - Press\u00e3o do tambor', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0414\u0430\u0432\u043b\u0435\u043d\u0438\u0435\u0020\u0432\u0020\u0431\u0430\u0440\u0430\u0431\u0430\u043d\u0435', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\ub4dc\ub7fc\u0020\uc555\ub825', # KO
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u30c9\u30e9\u30e0\u5727\u529b', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u7089\u538b', # CN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u7210\u58d3', # CN Traditional
    ]
    curve_airflow_control_trans = [
        'Curve - Airflow control', # EN
        'Kurve - Airflow-Steuerung', # DE
        'Curva - Regulaci\u00f3n del caudal de aire', # ES
        'Curva  Regulaci\u00f3n del caudal de', # ES new
        'Courbe Contr\u00f4le de la ventilati', # FR
        "Courbe Gestion flux d'air", # FR new
        "Curva - Controllo del flusso d'", # IT: "Curva - Controllo del flusso d'aria"
        'Curva - Controllo del flusso d', # IT new
        'Curva - Controle de fluxo de ar', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c\u0020\u0432\u043e\u0437\u0434\u0443\u0448\u043d\u043e\u0433\u043e\u0020\u043f\u043e', # RU
        '\ucee4\ube0c\u0020\u002d\u0020\u0041\u0069\u0072\u0066\u006c\u006f\u0077\u0020\u0063\u006f\u006e\u0074\u0072\u006f\u006c', # KO
        '\ucee4\ube0c\u0020\u002d\u0020\uacf5\uae30\ud750\ub984\u0020\uc81c\uc5b4', # KO new
        '\u30ab\u30fc\u30d6\u0020\u002d\u0020\u7a7a\u6c17\u306e\u6d41\u308c\u306e\u7ba1\u7406', # JP
        '\u66f2\u7ebf\u0020\u002d\u0020\u98ce\u95e8\u63a7\u5236', # SN Simplified
        '\u66f2\u7dda\u0020\u002d\u0020\u0041\u0069\u0072\u0066\u006c\u006f\u0077\u0020\u0063\u006f\u006e\u0074\u0072\u006f\u006c', # SN Traditional
        '\u66f2\u7dda\u0020\u002d\u0020\u98a8\u9580\u63a7\u5236', # SN Traditional
    ]
    curve_fan_speed_trans = [
        'Curve - fanSpeed', # EN
        'Kurve - fanSpeed', # DE
        'Curva - Velocidad del ventilador', # ES
        'Curva  Velocidad del ventilador', # ES new
        'Courbe fanSpeed', # FR
        'Curva - fanSpeed', # IT, ES
        'Curva - fanSpeed', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f - fanSpeed', # RU
        '\ucee4\ube0c - fanSpeed', # KO
        '\u30ab\u30fc\u30d6 - fanSpeed', # JP
        '\u66f2\u7ebf - fanSpeed', # CN Simplified
        '\u66f2\u7dda - fanSpeed', # CN Traditional
    ]

    # Drum speed control
    curve_drum_speed_control_trans = [
        'Curve - drumSpeedControl', # EN
        'Kurve - drumSpeedControl', # DE
        'Curva  drumSpeedControl', # ES
        'Courbe drumSpeedControl', # FR
        'Curva - drumSpeedControl', # IT
        'Curva - drumSpeedControl', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f - drumSpeedControl', # RU
        '\ucee4\ube0c - drumSpeedControl', # KO
        '\u30ab\u30fc\u30d6 - drumSpeedControl', # JP
        '\u66f2\u7ebf - drumSpeedControl', # CN Simplified
        '\u66f2\u7dda - drumSpeedControl', # CN Traditional
    ]

    # Set temperature
    curve_set_temperature_control_trans = [
        'Curve - setTemperatureControl', # EN
        'Kurve - setTemperatureControl', # DE
        'Curva  setTemperatureControl', # ES
        'Courbe setTemperatureControl', # FR
        'Curva - setTemperatureControl', # IT
        'Curva - setTemperatureControl', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f - setTemperatureControl', # RU
        '\ucee4\ube0c - setTemperatureControl', # KO
        '\u30ab\u30fc\u30d6 - setTemperatureControl', # JP
        '\u66f2\u7ebf - setTemperatureControl', # CN Simplified
        '\u66f2\u7dda - setTemperatureControl', # CN Traditional
    ]

    curve_custom_trans = [
        'Curve - custom', # EN
        'Kurve - custom', # DE
        'Curva  custom', # ES
        'Courbe custom', # FR
        'Curva - custom', # IT
        'Curva - custom', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f - custom', # RU
        '\ucee4\ube0c - custom', # KO
        '\u30ab\u30fc\u30d6 - custom', # JP
        '\u66f2\u7ebf - custom', # CN Simplified
        '\u66f2\u7dda - custom', # CN Traditional
    ]

    # just guessing
    curve_custom_control_trans = [
        'Curve - custom control', # EN
        'Curve - customControl', # EN2
        'Kurve - custom-Steuerung', # DE
        'Kurve - custom Steuerung', # DE2
        'Kurve - customControl', # DE3
        'Curva  customControl', # ES
        'Courbe customControl', # FR
        'Curva - customControl', # IT
        'Curva - customControl', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f - customControl', # RU
        '\ucee4\ube0c - customContrl', # KO
        '\u30ab\u30fc\u30d6 - customControl', # JP
        '\u66f2\u7ebf - customControl', # CN Simplified
        '\u66f2\u7dda - customControl', # CN Traditional
    ]



####

    extra_temp_curve_trans = \
        curve_env_temp_trans + \
        curve_burner_temp_trans + \
        curve_other_temp_trans + \
        curve_stack_temp_trans + \
        curve_return_temp_trans + \
        curve_inlet_temp_trans + \
        curve_afterburner_temp_trans + \
        curve_drum_temp_trans + \
        curve_set_temperature_control_trans

    extra_nontemp_curve_trans = \
        curve_gas_control_trans + \
        curve_drum_speed_trans + \
        curve_airflow_trans + \
        curve_gas_trans + \
        curve_drum_pressure_trans + \
        curve_airflow_control_trans + \
        curve_fan_speed_trans + \
        curve_drum_speed_control_trans + \
        curve_custom_trans
        #curve_gas_comments_trans


    curve_prefixa = [
        # Curve + Temp
        'Curva - Temp.', # ES (potentially wrong)
        'Courbe Temp.', # FR
        'Curva - Temp.', # IT
        'Curva - Temp.', # PT
        '\u041a\u0440\u0438\u0432\u0430\u044f\u0020\u002d\u0020\u0422\u0435\u043c\u043f\u002e\u0020', # RU
        # just Curve
        'Curve -', # EN
        'Kurve -', # DE
        'Curva -', # ES, IT, PT
        'Courbe', # FR
        '\u041a\u0440\u0438\u0432\u0430\u044f -', # RU
        '\ucee4\ube0c -', # KO
        '\u30ab\u30fc\u30d6 -', # JP
        '\u66f2\u7ebf -', # CN Simplified
        '\u66f2\u7dda -', # CN Traditional
    ]

    curve_postfixa = [
        'temp.', # EN
        'temperature', # EN new
        'temp.', # DE
        '\u0020\uc628\ub3c4', # KO
        '\u6e29\u5ea6\u3002', # JP
        '\u6e29\u5ea6', # CN Simplified & Tranitional
    ]

##########

    # extract general profile information
    general_sh = book.sheet_by_index(0)
    if general_sh.nrows >= 1:
        row1 = general_sh.row(1)
        general_data = dict(zip([x.value for x in general_sh.row(0)],row1))

        res['samplinginterval'] = 1.0

        try:
            id_tag_value = None
            # try to find the "Id-Tag" value
            # 1. test the column name in all known translations
            for tag in id_tag_trans:
                if tag in general_data:
                    id_tag_value = general_data[tag].value
                    break
            # 2. take the first value of row1
            if id_tag_value is None and len(row1)>0:
                id_tag_value = row1[0].value
            if id_tag_value is not None:
                batch_prefix = id_tag_value.rstrip('0123456789')
                batch_number = int(id_tag_value[len(batch_prefix):])
                res['roastbatchprefix'] = batch_prefix
                res['roastbatchnr'] = batch_number
        except Exception: # pylint: disable=broad-except
            pass

        for (itag,ipos,itrans) in int_tag_labels_trans:
            value = None
            try:
                # 1. test the column name in all known translations
                for tr in itrans:
                    if tr in general_data:
                        value = general_data[tr].value
                        break
                # 2. take the ipos column value of row1
                if value is None and ipos is not None and len(row1)>ipos:
                    value = row1[ipos].value
                if value is not None:
                    res[itag] = int(round(float(value))) # type: ignore # mypy cannot check generic labels accessing the res of type TypedDict
            except Exception: # pylint: disable=broad-except
                pass

        for (tag,pos,trans) in string_tag_labels_trans:
            value = None
            try:
                # 1. test the column name in all known translations
                for tr in trans:
                    if tr in general_data:
                        value = general_data[tr].value
                        break
                # 2. take the pos column value of row1
                if value is None and pos is not None and len(row1)>pos:
                    value = row1[pos].value
                if value is not None:
                    res[tag] = encodeLocal(value) # type: ignore # mypy cannot check generic labels accessing the res of type TypedDict
            except Exception: # pylint: disable=broad-except
                pass

        try:
            date_tag_value:Optional[float] = None
            # try to find the "Date" value
            # 1. test the column name in all known translations
            for tag in date_trans:
                if tag in general_data and general_data[tag].ctype is xlrd.XL_CELL_DATE:
                    date_tag_value = float(general_data[tag].value)
                    break
            # 2. take the first value of row1
            if date_tag_value is None:
                date_tag_value = float(row1[7].value)
            if date_tag_value is not None:
                date_tuple = xlrd.xldate_as_tuple(date_tag_value, book.datemode)
                date = QDateTime(*date_tuple)
                if date.isValid():
                    roastdate:Optional[str] = encodeLocal(date.date().toString())
                    if roastdate is not None:
                        res['roastdate'] = roastdate
                    roastisodate:Optional[str] = encodeLocal(date.date().toString(Qt.DateFormat.ISODate))
                    if roastisodate is not None:
                        res['roastisodate'] = roastisodate
                    roasttime:Optional[str] = encodeLocal(date.time().toString())
                    if roasttime is not None:
                        res['roasttime'] = roasttime
                    res['roastepoch'] = int(date.toSecsSinceEpoch())
                    res['roasttzoffset'] = libtime.timezone
        except Exception: # pylint: disable=broad-except
            pass

        try:
            ambient_tag_value = None
            # try to find the "Ambient temp." value
            # test the column name in all known translations
            for tag in ambient_temp_trans:
                if tag in general_data:
                    ambient_tag_value = general_data[tag].value
                    break
#            if ambient_tag_value is None and len(row1)>27:  # dangerous as not available in newer 2025 exports!?
#                ambient_tag_value = row1[27]
            if ambient_tag_value is not None:
                res['ambientTemp'] = float(ambient_tag_value)
        except Exception: # pylint: disable=broad-except
            pass

        try:
            sensory_tag_value = None
            # try to find the "cupping score" value
            # test the column name in all known translations
            for tag in sensory_score_tag_trans:
                if tag in general_data:
                    sensory_tag_value = general_data[tag].value
                    break
#            if sensory_tag_value is None and len(row1)>16:
#                sensory_tag_value = row1[16]
            if sensory_tag_value is not None:
                score:float = float(sensory_tag_value)
                correction:float = 0
                valid_score:float
                # cupping scores outside of the Artisan range 0-100 are achieved by setting the cupping correction value accordingly
                if score < 0:
                    correction = score
                    valid_score = 0
                if score > 0:
                    correction = score - 100
                    valid_score = 100
                else:
                    correction = 0
                    valid_score = score
                res['flavorlabels'] = aw.qmc.flavorlabels
                res['flavors_total_correction'] = correction
                res['flavors'] = [valid_score/10]*len(aw.qmc.flavorlabels)
        except Exception: # pylint: disable=broad-except
            pass

        try:
            start_weight_tag_value = None
            start_weight_unit_tag_value = None
            end_weight_tag_value = None
            end_weight_unit_tag_value = None

            # try to find the "Start weight" value
            # test the column name in all known translations
            for tag in start_weight_trans:
                if tag in general_data:
                    start_weight_tag_value = general_data[tag].value
                    break
#            if start_weight_tag_value is None and len(row1)>9:
#                start_weight_tag_value = row1[9]
            # try to find the "Start weight unit" value
            # test the column name in all known translations
            for tag in start_weight_unit_trans:
                if tag in general_data:
                    start_weight_unit_tag_value = general_data[tag].value
                    break
#            if start_weight_unit_tag_value is None and len(row1)>10:
#                start_weight_unit_tag_value = row1[10]
            # try to find the "End weight" value
            # test the column name in all known translations
            for tag in end_weight_trans:
                if tag in general_data:
                    end_weight_tag_value = general_data[tag].value
                    break
#            if end_weight_tag_value is None and len(row1)>11:
#                end_weight_tag_value = row1[11]
            # try to find the "End weight unit" value
            # test the column name in all known translations
            for tag in end_weight_unit_trans:
                if tag in general_data:
                    end_weight_unit_tag_value = general_data[tag].value
                    break
#            if end_weight_unit_tag_value is None and len(row1)>12:
#                end_weight_unit_tag_value = row1[12]

            if start_weight_tag_value is not None and end_weight_tag_value is not None:
                cropster_weight_units = ['G','KG','LBS','OZ']
                artisan_weight_units = ['g','Kg','lb','oz']
                weight:List[Union[float,str]] = [0,0,artisan_weight_units[0]]
                try:
                    if end_weight_unit_tag_value is not None:
                        idx = cropster_weight_units.index(end_weight_unit_tag_value)
                        weight[2] = artisan_weight_units[idx]
                except Exception: # pylint: disable=broad-except
                    pass
                try:
                    if start_weight_unit_tag_value:
                        idx = cropster_weight_units.index(start_weight_unit_tag_value)
                        weight[2] = artisan_weight_units[idx]
                except Exception: # pylint: disable=broad-except
                    pass
                try:
                    if start_weight_tag_value is not None:
                        weight[0] = start_weight_tag_value
                except Exception: # pylint: disable=broad-except
                    pass
                try:
                    if end_weight_tag_value is not None:
                        weight[1] = end_weight_tag_value
                except Exception: # pylint: disable=broad-except
                    pass
                res['weight'] = weight
        except Exception: # pylint: disable=broad-except
            pass

    res['timex'] = []
    res['temp1'] = []
    res['temp2'] = []
    # BT:
    BT_idx = None
    ET_idx = None
    charge_idx:int
    try:
        for i,sn in enumerate(sheet_names):
            if sn in curve_bt_trans:
                BT_idx = i
                BT_sh = book.sheet_by_index(BT_idx)
                if BT_sh.ncols >= 1:
                    time = BT_sh.col(0)
                    temp = BT_sh.col(1)
                    if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                        if 'FAHRENHEIT' in str(temp[0].value):
                            res['mode'] = 'F'
                        else:
                            res['mode'] = 'C'
                        res['timex'] = [float(t.value) for t in time[1:]]
                        res['temp2'] = [float(t.value) for t in temp[1:]]
                        res['temp1'] = [-1]*len(res['timex'])
                        charge_idx = 0
                        try:
                            charge_idx = res['timex'].index(0)
                        except Exception: # pylint: disable=broad-except
                            pass
                        res['timeindex'] = [charge_idx,0,0,0,0,0,max(0,len(res['timex'])-1),0]
                break
    except Exception: # pylint: disable=broad-except
        pass

    # ET
    try:
        for et_trans in [curve_env_temp_trans,curve_et_trans,curve_return_temp_trans,curve_inlet_temp_trans,curve_burner_temp_trans]:
            for i,sn in enumerate(sheet_names):
                if sn in et_trans:
                    ET_idx = i
                    ET_sh = book.sheet_by_index(ET_idx)
                    if ET_sh.ncols >= 1:
                        time = ET_sh.col(0)
                        temp = ET_sh.col(1)
                        if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                            if 'FAHRENHEIT' in str(temp[0].value):
                                res['mode'] = 'F'
                            else:
                                res['mode'] = 'C'
                            res['temp1'] = [float(t.value) for t in temp[1:]]
                            if len(res['timex']) != len(res['temp1']):
                                res['timex'] = [float(t.value) for t in time[1:]]
                            if 'temp2' not in res or len(res['temp2']) != len(res['timex']):
                                res['temp2'] = [-1]*len(res['timex'])
                            charge_idx = 0
                            try:
                                charge_idx = res['timex'].index(0)
                            except Exception: # pylint: disable=broad-except
                                pass
                            res['timeindex'] = [charge_idx,0,0,0,0,0,max(0,len(res['timex'])-1),0]
                    break
            if ET_idx is not None:
                break
    except Exception: # pylint: disable=broad-except
        pass

    ordered_sheet_names:Sequence[Optional[str]]

    use_existing_extra_curve_names_and_visibility:bool = False # if True the curve names of the current setup are reused as far as possible

    # we resort the channels to better fit the IMF setups
    if aw.qmc.roastertype_setup.startswith('IMF'):
        # re-order sheets to realiz the standard IMF config order of extra devices
        imf_sheets = [
            curve_burner_temp_trans, curve_set_temperature_control_trans,
            curve_custom_control_trans, curve_custom_trans,
            curve_drum_speed_control_trans, curve_drum_speed_trans,
            curve_airflow_control_trans, curve_airflow_trans]
        # IMF curves not found will be set to None generating an empty curve
        idx = 0
        ordered_sheet_names = []
        assigned_idx:Set[int] = set()
        if BT_idx is not None:
            assigned_idx.add(BT_idx)
        if ET_idx is not None:
            assigned_idx.add(ET_idx)
        for imf_sheet in imf_sheets:
            # find a sn in sheet_names that matches
            found:bool = False
            for i, sn in enumerate(sheet_names):
                if i not in assigned_idx and sn.strip() in imf_sheet:
                    assigned_idx.add(i)
                    ordered_sheet_names.append(sn)
                    found = True
                    break
            if not found:
                ordered_sheet_names.append(None)
        # add remaining sheet names
        for i, sn in enumerate(sheet_names):
            if i not in assigned_idx:
                assigned_idx.add(i)
                ordered_sheet_names.append(sn)
        use_existing_extra_curve_names_and_visibility = True
    else:
        ordered_sheet_names = sheet_names

    # sheet names to indexes in the original table order (note the ordered_sheet_names now are in a different order!)
    sheet_idx:Dict[str,int] = {n:i for i,n in enumerate(sheet_names)}


    # set extra lcd/curve visibility from current setup as default
    res['extraLCDvisibility1'] = aw.extraLCDvisibility1
    res['extraLCDvisibility2'] = aw.extraLCDvisibility2
    res['extraCurveVisibility1'] = aw.extraCurveVisibility1
    res['extraCurveVisibility2'] = aw.extraCurveVisibility2

    # extra temperature curves (only if ET or BT and its corresponding timex was already parsed successfully)
    if len(res['timex']) > 0:
        channel = 1 # toggle between channel 1 and 2 to be filled with extra temperature curve data
        for sno in ordered_sheet_names[:(2 * aw.nLCDS)]:  # Artisan supports a maximum of aw.nLCDS=10 extra devices for now (= 2x aw.nLCDS extra curves)
            snn:Optional[str] = (None if sno is None else sno.strip())
            if snn is None or snn in extra_temp_curve_trans:
                temp_curve = True
            elif snn in extra_nontemp_curve_trans:
                temp_curve = False
            else:
                continue
            try:
                if 'extradevices' not in res:
                    res['extradevices'] = []
                if 'extraname1' not in res:
                    res['extraname1'] = []
                if 'extraname2' not in res:
                    res['extraname2'] = []
                if 'extratimex' not in res:
                    res['extratimex'] = []
                if 'extratemp1' not in res:
                    res['extratemp1'] = []
                if 'extratemp2' not in res:
                    res['extratemp2'] = []
                if 'extramathexpression1' not in res:
                    res['extramathexpression1'] = []
                if 'extramathexpression2' not in res:
                    res['extramathexpression2'] = []
                if 'extraNoneTempHint1' not in res:
                    res['extraNoneTempHint1'] = []
                if 'extraNoneTempHint2' not in res:
                    res['extraNoneTempHint2'] = []

                # add empty curve for snn == None
                if snn is None:
                    if channel == 1:
                        channel = 2
                        # we add an empty first extra channel if needed
                        res['extradevices'].append(25) # Virtual Device
                        if use_existing_extra_curve_names_and_visibility and len(aw.qmc.extraname1)>len(res['extraname1']):
                            res['extraname1'].append(aw.qmc.extraname1[len(res['extraname1'])])
                        else:
                            # we turn all empt extra LCDs/curves OFF by default
                            if len(res['extraLCDvisibility1'])>len(res['extraname1']):
                                res['extraLCDvisibility1'][len(res['extraname1'])] = False
                                res['extraCurveVisibility1'][len(res['extraname1'])] = False
                            res['extraname1'].append('Extra 1')
                        res['extratemp1'].append([-1]*len(res['timex']))
                        res['extraNoneTempHint1'].append(True)
                        res['extramathexpression1'].append('')
                    else:
                        channel = 1
                        # we add an empty second extra channel if needed
                        if use_existing_extra_curve_names_and_visibility and len(aw.qmc.extraname2)>len(res['extraname2']):
                            res['extraname2'].append(aw.qmc.extraname2[len(res['extraname2'])])
                        else:
                            # we turn all empt extra LCDs/curves OFF by default
                            if len(res['extraLCDvisibility2'])>len(res['extraname2']):
                                res['extraLCDvisibility2'][len(res['extraname2'])] = False
                                res['extraCurveVisibility2'][len(res['extraname2'])] = False
                            res['extraname2'].append('Extra 2')
                        res['extratemp2'].append([-1]*len(res['timex']))
                        res['extraNoneTempHint2'].append(True)
                        res['extramathexpression2'].append('')
                else:

                    CT_idx = sheet_idx[snn]
                    CT_sh = book.sheet_by_index(CT_idx)
                    if CT_sh.ncols >= 1:
                        time = CT_sh.col(0)
                        temp = CT_sh.col(1)
                        if len(time) > 0 and len(temp) > 0 and len(time) == len(temp):
                            extra_curve_name = snn
                            # we split of the "Curve -" prefix
                            for px in curve_prefixa:
                                if extra_curve_name.startswith(px):
                                    sp = extra_curve_name.split(px)
                                    extra_curve_name = sp[1] if len(sp) > 1 else sp[0]
                                    extra_curve_name = extra_curve_name.strip()
                                    break

                            # we split of also the "temp." postfix
                            for px in curve_postfixa:
                                if extra_curve_name.endswith(px):
                                    extra_curve_name = extra_curve_name.split(px)[0].strip()
                                    break
                            if channel == 1:
                                channel = 2
                                if temp_curve:
                                    # apply temp conversion
                                    res['extraNoneTempHint1'].append(False)
                                else:
                                    # no temp conversion
                                    res['extraNoneTempHint1'].append(True)
                                res['extradevices'].append(25) # Virtual Device
                                if use_existing_extra_curve_names_and_visibility and len(aw.qmc.extraname1)>len(res['extraname1']):
                                    res['extraname1'].append(aw.qmc.extraname1[len(res['extraname1'])])
                                else:
                                    # we turn all extra LCDs/curves ON by default
                                    if len(res['extraLCDvisibility1'])>len(res['extraname1']):
                                        res['extraLCDvisibility1'][len(res['extraname1'])] = True
                                        res['extraCurveVisibility1'][len(res['extraname1'])] = True
                                    name1:Optional[str] = encodeLocal(extra_curve_name)
                                    if name1 is None:
                                        name1 = 'extra1'
                                    res['extraname1'].append(name1)
                                res['extratimex'].append([float(t.value) for t in time[1:]])
                                res['extratemp1'].append([float(t.value) for t in temp[1:]])
                                res['extramathexpression1'].append('')
                            elif (len(time) -1) == len(res['extratimex'][-1]): # only if time lengths is same as of channel 1
                                channel = 1
                                if temp_curve:
                                    # apply temp conversion
                                    res['extraNoneTempHint2'].append(False)
                                else:
                                    # no temp conversion
                                    res['extraNoneTempHint2'].append(True)
                                if use_existing_extra_curve_names_and_visibility and len(aw.qmc.extraname2)>len(res['extraname2']):
                                    res['extraname2'].append(aw.qmc.extraname2[len(res['extraname2'])])
                                else:
                                    # we turn all extra LCDs/curves ON by default
                                    if len(res['extraLCDvisibility2'])>len(res['extraname2']):
                                        res['extraLCDvisibility2'][len(res['extraname2'])] = True
                                        res['extraCurveVisibility2'][len(res['extraname2'])] = True
                                    name2:Optional[str] = encodeLocal(extra_curve_name)
                                    if name2 is None:
                                        name2 = 'extra2'
                                    res['extraname2'].append(name2)
                                res['extratemp2'].append([float(t.value) for t in temp[1:]])
                                res['extramathexpression2'].append('')
            except Exception: # pylint: disable=broad-except
                pass
        if 'extratemp1' in res and 'extratemp2' in res and 'extraNoneTempHint2' in res and 'extramathexpression2' in res and 'extraname1' in res and 'extraname2' in res and len(res['extraname1']) != len(res['extraname2']):
            # we add an empty second extra channel if needed
            if use_existing_extra_curve_names_and_visibility and len(aw.qmc.extraname2)>len(res['extraname2']):
                res['extraname2'].append(aw.qmc.extraname2[len(res['extraname2'])])
            else:
                # we turn all empty extra LCDs/curves OFF by default
                if len(res['extraLCDvisibility2'])>len(res['extraname2']):
                    res['extraLCDvisibility2'][len(res['extraname2'])] = False
                    res['extraCurveVisibility2'][len(res['extraname2'])] = False
                res['extraname2'].append('Extra 2')
            res['extratemp2'].append([-1]*len(res['extratemp1'][-1]))
            res['extraNoneTempHint2'].append(True)
            res['extramathexpression2'].append('')

        # add events
        try:
            COMMENTS_idx = 1
            try:
                sheet_names.index('Comments')
            except Exception: # pylint: disable=broad-except
                pass
            COMMENTS_sh = book.sheet_by_index(COMMENTS_idx)
            gas_event = False # set to True if a Gas event exists
            airflow_event = False # set to True if an Airflow event exists
            specialevents:List[int] = []
            specialeventstype:List[int] = []
            specialeventsvalue:List[float] = []
            specialeventsStrings:List[str] = []
            if COMMENTS_sh.ncols >= 4:
                for r in range(COMMENTS_sh.nrows):
                    if r>0:
                        try:
                            time = float(COMMENTS_sh.cell(r, 0).value)
                            comment_type = COMMENTS_sh.cell(r, 2).value.strip()
                            if comment_type not in turning_point_trans: # TP is ignored as it is automatically assigned
                                comment_value = COMMENTS_sh.cell(r, 3).value
                                c = takeClosest(time,res['timex'])
                                timex_idx = res['timex'].index(c)
                                if comment_type in color_change_trans:
                                    res['timeindex'][1] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                elif comment_type in first_crack_trans:
                                    res['timeindex'][2] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                elif comment_type == 'First crack end':
                                    res['timeindex'][3] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                elif comment_type in second_crack_trans:
                                    res['timeindex'][4] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                elif comment_type == 'Second crack end':
                                    res['timeindex'][5] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                elif comment_type == 'Duration':
                                    res['timeindex'][6] = max(0,timex_idx) # pyright:ignore[reportTypedDictNotRequiredAccess]
                                else:
                                    specialevents.append(timex_idx)
                                    ae = False
                                    ge = False
                                    if comment_type in airflow_trans:
                                        ae = True
                                        airflow_event = True
                                        specialeventstype.append(0)
                                    elif comment_type in gas_trans:
                                        ge = True
                                        gas_event = True
                                        specialeventstype.append(3)
                                    else:
                                        specialeventstype.append(4)
                                    try:
                                        v = float(comment_value)
                                        v = v/10. + 1
                                        specialeventsvalue.append(v)
                                    except Exception: # pylint: disable=broad-except
                                        specialeventsvalue.append(0)
                                    if not ae and not ge and comment_type not in comment_trans:
                                        event_type_str:Optional[str] = encodeLocal(comment_type)
                                        if event_type_str is None:
                                            event_type_str = 'event'
                                        specialeventsStrings.append(event_type_str)
                                    else:
                                        event_value_str:Optional[str] = encodeLocal(comment_value)
                                        if event_value_str is None:
                                            event_value_str = 'event'
                                        specialeventsStrings.append(event_value_str)
                        except Exception: # pylint: disable=broad-except
                            pass
            if len(specialevents) > 0:
                res['specialevents'] = specialevents
                res['specialeventstype'] = specialeventstype
                res['specialeventsvalue'] = specialeventsvalue
                res['specialeventsStrings'] = specialeventsStrings
                if gas_event or airflow_event:
                    # first set etypes to defaults
                    res['etypes'] = [QApplication.translate('ComboBox', 'Air'),
                                     QApplication.translate('ComboBox', 'Drum'),
                                     QApplication.translate('ComboBox', 'Damper'),
                                     QApplication.translate('ComboBox', 'Burner'),
                                     '--']
                    # update
                    if airflow_event:
                        res['etypes'][0] = 'Airflow'
                    if gas_event:
                        res['etypes'][3] = 'Gas'
        except Exception as e: # pylint: disable=broad-except
            _log.debug(e)
    return res
