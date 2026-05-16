import json
import urllib.request
import ssl
from pathlib import Path
import subprocess
import sys

# Asegurarse de que pandas y openpyxl estén instalados
try:
    import pandas as pd
except ImportError:
    print("📦 Instalando dependencias necesarias (pandas, openpyxl)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
    import pandas as pd

SHEET_EXCEL_URL = "https://docs.google.com/spreadsheets/d/1oTVSF7CjrCtnk3pHdBIRE8gzhE9zKDM5NJFyWV-qsJs/export?format=xlsx"
JSON_PATH = "/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Comic/data/catalog.json"

def update_verses_from_sheet():
    print("📥 Descargando base de datos bíblica desde Google Sheets (Hoja 4)...")
    
    try:
        # Descargar y leer específicamente la 'Hoja 4'
        df = pd.read_excel(SHEET_EXCEL_URL, sheet_name='Hoja 4')
    except Exception as e:
        print(f"❌ Error al descargar el Excel: {e}")
        return

    # Crear un diccionario para búsqueda rápida de Versículos por Título
    verse_db = {}
    for index, row in df.iterrows():
        title = str(row.get('Título', '')).strip()
        verse = str(row.get('Verso Bíblico / Pasaje', '')).strip()
        focus = str(row.get('Temática Central', '')).strip()
        
        if title and title.lower() != 'nan' and verse and verse.lower() != 'nan':
            # Clave en minúsculas para evitar problemas de mayúsculas
            verse_db[title.lower()] = {
                "verse": verse,
                "focus": focus
            }

    print(f"✅ Se encontraron {len(verse_db)} canciones con versículos en la 'Hoja 4'.")

    # Cargar el catálogo local
    if not Path(JSON_PATH).exists():
        print("❌ Error: No se encontró catalog.json")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    updated_count = 0

    # Actualizar catálogo
    for song in catalog:
        title_lower = song.get('title', '').strip().lower()
        
        if title_lower in verse_db:
            new_verse = verse_db[title_lower]['verse']
            new_focus = verse_db[title_lower]['focus']
            
            # Solo actualizar si es necesario
            current_context = song.get('context', {})
            if current_context.get('verse') != new_verse or current_context.get('focus') != new_focus:
                song['context'] = {
                    "verse": new_verse,
                    "focus": new_focus
                }
                updated_count += 1
                print(f"🔄 Actualizado: {song['title']} -> {new_verse}")

    # Guardar cambios
    if updated_count > 0:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=4, ensure_ascii=False)
        print(f"🎉 ¡Éxito! Se actualizaron {updated_count} canciones en catalog.json.")
    else:
        print("⚡ El catálogo ya estaba completamente actualizado con las citas bíblicas.")

if __name__ == "__main__":
    update_verses_from_sheet()
