
import json
from pathlib import Path

def repair_catalog():
    master_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Atmos/data/musichris_master_catalog.json")
    comic_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/Musichris_Comic/data/catalog.json")
    
    if not master_path.exists():
        print("❌ No se encontró el catálogo maestro en Musichris_Atmos.")
        return
    
    with open(master_path, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
        
    with open(comic_path, 'r', encoding='utf-8') as f:
        comic_data = json.load(f)
    
    # Crear mapa de títulos a contextos del maestro
    master_map = {item['title']: item['context'] for item in master_data if 'title' in item and 'context' in item}
    
    repaired_count = 0
    for item in comic_data:
        title = item.get('title')
        if title in master_map:
            old_focus = item.get('context', {}).get('focus', '')
            new_context = master_map[title]
            
            # Solo actualizar si el foco actual parece técnico (contiene BPM, tempo, pads, etc.)
            tech_keywords = ['BPM', 'tempo', 'Pads', 'Guitarra', 'eco', 'vibra', 'gritos', 'estilo']
            is_technical = any(kw.lower() in old_focus.lower() for kw in tech_keywords)
            
            if is_technical or not old_focus:
                item['context'] = new_context
                repaired_count += 1
                # print(f"✅ Reparado: {title}")
    
    with open(comic_path, 'w', encoding='utf-8') as f:
        json.dump(comic_data, f, indent=4, ensure_ascii=False)
    
    print(f"✨ Reparación completada. Se restauró el contexto bíblico en {repaired_count} canciones.")

if __name__ == "__main__":
    repair_catalog()
