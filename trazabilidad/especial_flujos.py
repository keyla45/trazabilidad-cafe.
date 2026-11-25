"""Flujos de referencia configurables; no sustituye POE de la planta."""
FLUJOS = {
    'Lavado': ['Recepción y selección','Despulpado','Fermentación','Lavado','Secado','Trilla y clasificación','Tostado','Catación','Empaque'],
    'Natural': ['Recepción y selección','Clasificación de cereza','Secado con fruto','Reposo','Trilla y clasificación','Tostado','Catación','Empaque'],
    'Honey': ['Recepción y selección','Despulpado con mucílago','Secado con mucílago','Reposo','Trilla y clasificación','Tostado','Catación','Empaque'],
    'Anaeróbico': ['Recepción y selección','Preparación y carga de tanque','Fermentación en ambiente controlado','Descarga y verificación','Secado','Trilla y clasificación','Tostado','Catación','Empaque'],
}
