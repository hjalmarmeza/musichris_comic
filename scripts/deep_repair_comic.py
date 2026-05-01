
import json
from pathlib import Path
import re

def normalize_title(title):
    # Eliminar v2, Atmos, Atmos v2, etc.
    t = re.sub(r'\s+(v\d+|Atmos.*)$', '', title, flags=re.IGNORECASE)
    return t.strip().upper()

def deep_repair_comic():
    master_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Atmos/data/musichris_master_catalog.json")
    comic_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/Musichris_Comic/data/catalog.json")
    
    if not master_path.exists() or not comic_path.exists():
        print("❌ Error en las rutas de catálogo.")
        return
    
    with open(master_path, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
    with open(comic_path, 'r', encoding='utf-8') as f:
        comic_data = json.load(f)
    
    # 1. Crear mapa de contextos maestros (priorizando el que NO sea Salmos 23:1)
    master_map = {}
    for item in master_data:
        base_title = normalize_title(item['title'])
        verse = item.get('context', {}).get('verse', '')
        
        # Si encontramos un verso legítimo, lo guardamos para ese título base
        if verse and verse != "Salmos 23:1":
            master_map[base_title] = item['context']
    
    # 2. Reparar el catálogo de cómic
    repaired_count = 0
    for item in comic_data:
        title = item.get('title', '')
        base_title = normalize_title(title)
        current_verse = item.get('context', {}).get('verse', '')
        
        # Si tiene el default o está vacío, y tenemos un reemplazo en el maestro
        if (current_verse == "Salmos 23:1" or not current_verse) and base_title in master_map:
            if "SALMO 23" not in base_title:
                item['context'] = master_map[base_title]
                repaired_count += 1
                # print(f"✅ Reparado en Cómic: {title} -> {item['context']['verse']}")

    if repaired_count > 0:
        with open(comic_path, 'w', encoding='utf-8') as f:
            json.dump(comic_data, f, indent=4, ensure_ascii=False)
        print(f"✨ Éxito: Se repararon {repaired_count} entradas en el catálogo de Cómic.")
    else:
        print("ℹ️ No se encontraron más errores de Salmos 23:1 en el catálogo de Cómic.")

if __name__ == "__main__":
    deep_repair_comic()
