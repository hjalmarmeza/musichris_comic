
import json
from pathlib import Path
import re

def normalize_title(title):
    # Eliminar v2, Atmos, Atmos v2, etc.
    t = re.sub(r'\s+(v\d+|Atmos.*)$', '', title, flags=re.IGNORECASE)
    return t.strip().upper()

def deep_repair_master():
    master_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Atmos/data/musichris_master_catalog.json")
    
    if not master_path.exists():
        print("❌ No se encontró el catálogo maestro.")
        return
    
    with open(master_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    # 1. Mapear contextos correctos por título base
    # Un contexto es "correcto" si el verso NO es Salmos 23:1 (a menos que sea el Salmo 23 real)
    correct_contexts = {}
    
    for item in catalog:
        title = item['title']
        base_title = normalize_title(title)
        verse = item.get('context', {}).get('verse', '')
        focus = item.get('context', {}).get('focus', '')
        
        # Si el verso no es el default y tiene un foco decente, lo tomamos como referencia para ese grupo
        if verse and verse != "Salmos 23:1" and len(focus) > 10:
            if base_title not in correct_contexts:
                correct_contexts[base_title] = item['context']
    
    # 2. Aplicar corrección
    repaired_count = 0
    for item in catalog:
        title = item['title']
        base_title = normalize_title(title)
        current_verse = item.get('context', {}).get('verse', '')
        
        if current_verse == "Salmos 23:1" and base_title in correct_contexts:
            # Solo corregimos si es una variación (v2, Atmos) o si el título no parece ser del Salmo 23
            if "SALMO 23" not in base_title:
                item['context'] = correct_contexts[base_title]
                repaired_count += 1
                print(f"✅ Corregido: {title} (Ahora es {item['context']['verse']})")
    
    if repaired_count > 0:
        with open(master_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=4, ensure_ascii=False)
        print(f"✨ Éxito: Se corrigieron {repaired_count} entradas en el catálogo maestro.")
    else:
        print("ℹ️ No se encontraron entradas para corregir (o ya están corregidas).")

if __name__ == "__main__":
    deep_repair_master()
