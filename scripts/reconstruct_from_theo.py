
import json
import csv
from pathlib import Path
import re


def normalize_title(title):
    # Remover v1, v2, Atmos, Soul, puntos finales y espacios
    t = re.sub(r'\s+(v\d+|Atmos.*|Soul.*)$', '', title, flags=re.IGNORECASE)
    t = t.strip().strip('.')
    return t.upper()

# Mapeo manual para los que no están en headers_theo.txt
MANUAL_THEO_BRIDGE = {
    "LA TIERRA TEMBLÓ": {"verse": "Salmos 18:7", "focus": "La tierra fue conmovida y tembló; se conmovieron los cimientos de los montes."},
    "NADA ME APARTARÁ": {"verse": "Romanos 8:38-39", "focus": "Por lo cual estoy seguro de que ni la muerte, ni la vida... nos podrá separar del amor de Dios."},
    "REGRESA LA VIDA": {"verse": "Ezequiel 37:4-5", "focus": "Profetiza sobre estos huesos... He aquí, yo hago entrar espíritu en vosotros, y viviréis."},
    "UN CAMINO EN EL MAR": {"verse": "Isaías 43:16", "focus": "El que abre camino en el mar, y senda en las aguas impetuosas."},
    "GRACIA SIN CONDICIÓN": {"verse": "Efesios 2:8-9", "focus": "Porque por gracia sois salvos por medio de la fe... es don de Dios."},
    "BONDAD INAGOTABLE": {"verse": "Salmos 23:6", "focus": "Ciertamente el bien y la misericordia me seguirán todos los días de mi vida."},
    "MI ETERNA SALVACIÓN": {"verse": "Salmos 27:1", "focus": "Jehová es mi luz y mi salvación; ¿de quién temeré?"},
    "OPORTUNO SOCORRO": {"verse": "Hebreos 4:16", "focus": "Acerquémonos, pues, confiadamente... para alcanzar misericordia y hallar gracia para el oportuno socorro."},
    "MISERICORDIA ES LA RESPUESTA": {"verse": "Lamentaciones 3:22-23", "focus": "Por la misericordia de Jehová no hemos sido consumidos... nuevas son cada mañana."},
    "EL REGRESO DEL HIJO": {"verse": "Lucas 15:20", "focus": "Y cuando aún estaba lejos, lo vio su padre, y fue movido a misericordia, y corrió, y se echó sobre su cuello, y le besó."},
    "GOZO EN EL CIELO": {"verse": "Lucas 15:7", "focus": "Os digo que así habrá más gozo en el cielo por un pecador que se arrepiente."},
    "GRACIA MAJESTUOSA": {"verse": "2 Corintios 12:9", "focus": "Bástate mi gracia; porque mi poder se perfecciona en la debilidad."},
    "GRAN GOZO AL MUNDO": {"verse": "Lucas 2:10", "focus": "Pero el ángel les dijo: No temáis; porque he aquí os doy nuevas de gran gozo, que será para todo el pueblo."},
    "REY DE CADA MAÑANA": {"verse": "Salmos 5:3", "focus": "Oh Jehová, de mañana oirás mi voz; de mañana me presentaré delante de ti, y esperaré."},
    "EN PAZ ME ACOSTARÉ": {"verse": "Salmos 4:8", "focus": "En paz me acostaré, y asimismo dormiré; porque solo tú, Jehová, me haces vivir confiado."},
    "SOBRE LAS AGUAS": {"verse": "Mateo 14:29", "focus": "Y descendiendo Pedro de la barca, andaba sobre las aguas para ir a Jesús."},
    "VOZ DE JEHOVÁ": {"verse": "Salmos 29:3-4", "focus": "Voz de Jehová sobre las aguas... La voz de Jehová es poderosa; la voz de Jehová es majestuosa."},
    "¿QUIEN MÁS?": {"verse": "Salmos 73:25", "focus": "¿A quién tengo yo en los cielos sino a ti? Y fuera de ti nada deseo en la tierra."},
    "LA TORRE MAS ALTA": {"verse": "Proverbios 18:10", "focus": "Torre fuerte es el nombre de Jehová; a él correrá el justo, y será levantado."},
    "A DONDE HUIRÉ": {"verse": "Salmos 139:7", "focus": "¿A dónde me iré de tu Espíritu? ¿Y a dónde huiré de tu presencia?"},
    "A DONDE HUIRE": {"verse": "Salmos 139:7", "focus": "¿A dónde me iré de tu Espíritu? ¿Y a dónde huiré de tu presencia?"},
    "AQUÍ SIGO": {"verse": "Salmos 138:8", "focus": "Jehová cumplirá su propósito en mí; tu misericordia, oh Jehová, es para siempre."},
    "EN TÍ CONFÍO": {"verse": "Salmos 56:3", "focus": "En el día que temo, yo en ti confío."},
    "TU BAJASTE": {"verse": "Filipenses 2:7-8", "focus": "Se despojó a sí mismo, tomando forma de siervo, hecho semejante a los hombres."},
    "PELEA POR MÍ": {"verse": "Éxodo 14:14", "focus": "Jehová peleará por vosotros, y vosotros estaréis tranquilos."},
    "LEVÁNTATE": {"verse": "Salmos 68:1", "focus": "Levántese Dios, sean esparcidos sus enemigos, y huyan de su presencia los que le aborrecen."},
    "¿QUE ES EL HOMBRE?": {"verse": "Salmos 8:4", "focus": "¿Qué es el hombre, para que tengas de él memoria, y el hijo del hombre, para que lo visites?"},
    "ROCA Y ESCUDO": {"verse": "Salmos 144:1", "focus": "Bendito sea Jehová, mi roca, quien adiestra mis manos para la batalla, y mis dedos para la guerra."}
}

def reconstruct_from_theo():
    theo_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Soul/headers_theo.txt")
    master_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/PROYECTOS_FINALIZADOS/Musichris_Atmos/data/musichris_master_catalog.json")
    comic_path = Path("/Users/hjalmarmeza/Downloads/Antigravity/Musichris_Comic/data/catalog.json")
    
    # 1. Cargar desde theo file
    theo_map = {}
    if theo_path.exists():
        with open(theo_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) < 5: continue
                title = normalize_title(row[1])
                verse = row[2].strip()
                focus = f"{row[3].strip()} {row[4].strip()}".strip()
                if title:
                    theo_map[title] = {"verse": verse, "focus": focus}

    # 2. Integrar Manual Bridge
    for title, context in MANUAL_THEO_BRIDGE.items():
        norm_title = normalize_title(title)
        if norm_title not in theo_map:
            theo_map[norm_title] = context

    print(f"📖 Base teológica robusta: {len(theo_map)} entradas mapeadas.")

    def fix_catalog(path, label):
        if not path.exists(): return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fixed_count = 0
        for item in data:
            orig_title = item.get('title', '')
            base_title = normalize_title(orig_title)
            
            if base_title in theo_map:
                new_context = theo_map[base_title]
                current_verse = item.get('context', {}).get('verse', '')
                
                # Actualizamos si es Salmos 23:1 (alucinación por defecto) o si es diferente
                if current_verse == "Salmos 23:1" or current_verse != new_context['verse']:
                    # Excepción: Si el título realmente es sobre el pastor, dejarlo
                    if "PASTOR" in base_title and new_context['verse'] == "Salmos 23:1":
                        continue
                        
                    item['context'] = new_context
                    fixed_count += 1
        
        if fixed_count > 0:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✅ {label}: Corregidas {fixed_count} entradas.")
        else:
            print(f"ℹ️ {label}: Nada que corregir.")

    fix_catalog(master_path, "Catálogo Maestro")
    fix_catalog(comic_path, "Catálogo Cómic")

if __name__ == "__main__":
    reconstruct_from_theo()

if __name__ == "__main__":
    reconstruct_from_theo()
