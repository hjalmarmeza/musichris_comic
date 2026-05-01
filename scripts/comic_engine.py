import os
import sys
import requests
import json
import time
import subprocess
import random
import re
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from io import BytesIO
import io
from PIL import Image, ImageDraw, ImageFont, ImageStat

# Configuración Maestra
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
# Usamos un cliente directo para mayor control sobre el negative prompt

STYLE_PROMPT = ", biblical times, ancient Israel, first century setting, historical accuracy, modest humble clothing, professional digital comic art, oil painting texture, cinematic lighting, sharp detail, 4k, vertical composition"
NEGATIVE_PROMPT = "modern objects, soap dispensers, jewelry, earrings, piercings, modern accessories, sunglasses, romantic intimacy, seductive, low cut clothing, electricity, neon, plastic, glass bottles with pumps, computers, phones"

def generate_image_hf_direct(prompt, retries=3):
    """Genera imagen usando SDXL con fuertes guardarraíles negativos."""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": (
                "modern objects, soap dispensers, jewelry, earrings, piercings, modern accessories, "
                "sunglasses, romantic intimacy, seductive, low cut clothing, electricity, neon, plastic, "
                "glass bottles with pumps, computers, phones, extra fingers, distorted faces, blurry, "
                "modern architecture, tattoos, watches, cars"
            ),
            "num_inference_steps": 35,
            "guidance_scale": 8.5
        },
        "options": {"wait_for_model": True}
    }
    
    for i in range(retries):
        try:
            print(f"  🖼️ Generando imagen (SDXL - Intento {i+1})...")
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                img_bytes = response.content
                print(f"  ✅ Imagen generada ({len(img_bytes)//1024}KB)")
                return img_bytes
            elif response.status_code == 503:
                # El modelo se está cargando
                wait_time = 20
                try: wait_time = response.json().get('estimated_time', 20)
                except: pass
                print(f"⏳ El modelo se está cargando, esperando {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ⚠️ Error {response.status_code}: {response.text[:200]}")
                time.sleep(15)
        except Exception as e:
            print(f"  ⚠️ Intento {i+1} falló: {e}")
            time.sleep(15)
    return None

class MusiChrisComicEngine:
    def __init__(self):
        self.base_dir = Path(os.getcwd()).absolute()
        self.assets_dir = self.base_dir / "assets/panels"
        self.renders_dir = self.base_dir / "renders"
        self.temp_dir = self.base_dir / "temp"
        self.public_dir = self.base_dir / "public"
        
        print(f"🚀 [INIT] Directorio Base Forzado: {self.base_dir}")
        for d in [self.assets_dir, self.renders_dir, self.temp_dir]:
            d.mkdir(parents=True, exist_ok=True)
            print(f"✅ [INIT] Carpeta verificada/creada: {d}")

    def generate_image_hf(self, prompt, retries=3):
        """Genera imagen con IA y retorna bytes."""
        return generate_image_hf_direct(prompt + STYLE_PROMPT, retries)

    def generate_title_video(self, title):
        """Genera la pantalla inicial usando video_pantalla_inicio.mp4."""
        output_video = self.assets_dir / "intro_rendered.mp4"
        input_video = self.public_dir / "video_pantalla_inicio.mp4"
        
        print(f"🎬 Generando intro premium para: {title}")
        safe_title = title.replace("'", "'\\''").replace('"', '')
        
        if input_video.exists():
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-vf", (
                    f"drawtext=text='{safe_title}':fontcolor=gold:fontsize=80:"
                    "x=(w-text_w)/2:y=(h/2)-100:box=1:boxcolor=black@0.4:boxborderw=15:line_spacing=15,"
                    "drawtext=text='@MusiChris Studio':fontcolor=white:fontsize=45:"
                    "x=(w-text_w)/2:y=(h/2)+80:box=1:boxcolor=black@0.3:boxborderw=10"
                ),
                "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
        else:
            print("⚠️ Video intro no encontrado, usando fallback de color.")
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=#1a0a00:s=1080x1920:r=30:d=6",
                "-vf", (
                    f"drawtext=text='{safe_title}':fontcolor=gold:fontsize=80:"
                    "x=(w-text_w)/2:y=(h/2)-100:box=1:boxcolor=black@0.6:boxborderw=15,"
                    "drawtext=text='@MusiChris Studio':fontcolor=white:fontsize=45:"
                    "x=(w-text_w)/2:y=(h/2)+80:box=1:boxcolor=black@0.5:boxborderw=10"
                ),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
            
        subprocess.run(cmd, check=True)
        return str(output_video)

    def _generate_title_video_unused(self, title):
        """[LEGACY - no usar en cloud] Requiere video_pantalla_inicio.mp4 local."""
        output_video = self.assets_dir / "intro_rendered.mp4"
        input_video = self.public_dir / "video_pantalla_inicio.mp4"
        
        # Preparar Canvas de Texto (Transparente 1080x1920)
        overlay = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        try:
            f_title = ImageFont.truetype(font_path, 80)
            f_brand = ImageFont.truetype(font_path, 50)
        except:
            f_title = f_brand = ImageFont.load_default()

        def draw_premium_text(draw_obj, y, text, font, color, max_width=18):
            words = text.split()
            lines = []
            curr = ""
            for w in words:
                if len(curr + w) < max_width: curr += w + " "
                else:
                    lines.append(curr.strip())
                    curr = w + " "
            lines.append(curr.strip())
            
            curr_y = y
            for line in lines:
                bbox = draw_obj.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                # Sombra Profunda
                draw_obj.text(((1080-w)/2 + 4, curr_y + 4), line, font=font, fill=(0,0,0,220))
                draw_obj.text(((1080-w)/2, curr_y), line, font=font, fill=color)
                curr_y += 95

        # El título va ARRIBA del pergamino (según corrección de usuario)
        draw_premium_text(draw, 650, title.upper(), f_title, (255, 215, 0))
        draw_premium_text(draw, 1050, "MUSICHRIS_STUDIO", f_brand, (255, 255, 255))
        
        overlay_path = self.temp_dir / "intro_overlay.png"
        overlay.save(overlay_path)

        # Filtro de Video Intro (9:16)
        # Forzamos que el video sea el fondo y el overlay el título
        if input_video.exists():
            print(f"🎥 Usando VIDEO INTRO: {input_video.name}")
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-i", str(overlay_path),
                "-filter_complex", 
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]; "
                "[bg][1:v]overlay=enable='between(t,0,3.5)',fade=t=out:st=3.5:d=0.5",
                "-t", "4", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
        else:
            print("⚠️ Video intro no encontrado, usando master_intro_bg.png")
            bg_image = self.public_dir / "master_intro_bg.png"
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-t", "5", "-i", str(bg_image),
                "-i", str(overlay_path),
                "-filter_complex", 
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]; "
                "[bg][1:v]overlay=enable='between(t,0,4.5)',fade=t=out:st=4.5:d=0.5",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
            
        subprocess.run(cmd, check=True)
        
        # Guardar miniatura (Primer frame de la intro)
        thumb_path = self.base_dir / "thumbnail.jpg"
        subprocess.run([
            "ffmpeg", "-y", "-i", str(output_video), "-vframes", "1", str(thumb_path)
        ], check=True)
        
        return str(output_video)

    def analyze_best_corner(self, img, box_w, box_h):
        """Analiza la complejidad visual para decidir si poner el texto a la izq o der"""
        margin = 40
        # Cuadrante Izquierdo Superior vs Derecho Superior
        left_area = img.crop((margin, margin, margin + box_w, margin + box_h))
        right_area = img.crop((1080 - margin - box_w, margin, 1080 - margin, margin + box_h))
        left_stat = ImageStat.Stat(left_area).stddev
        right_stat = ImageStat.Stat(right_area).stddev
        if sum(left_stat) < sum(right_stat): return margin, margin
        else: return 1080 - margin - box_w, margin

    def add_text_to_image(self, img_data, text):
        """Hornea el texto ministerial sobre el panel asegurando legibilidad vertical 9:16."""
        img = Image.open(io.BytesIO(img_data)).convert('RGBA')
        
        # Forzar redimensionado a 1080x1920 con crop antes de añadir texto
        w, h = img.size
        aspect = 1080/1920
        if w/h > aspect: # Imagen ancha
            new_w = int(h * aspect)
            left = (w - new_w) / 2
            img = img.crop((left, 0, left + new_w, h))
        else: # Imagen alta
            new_h = int(w / aspect)
            top = (h - new_h) / 2
            img = img.crop((0, top, w, top + new_h))
        
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        try: font = ImageFont.truetype(font_path, 72) # Aumentado de 48 a 72 para legibilidad
        except: font = ImageFont.load_default()

        # Envolver texto - Ajustado para fuente más grande
        words = text.split(); lines = []; curr = ""
        for w in words:
            if len(curr + w) < 22: curr += w + " " # Menos caracteres por línea por fuente más grande
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        
        line_h = 90; box_w = 0 # Aumentado line_h
        for l in lines:
            bbox = draw.textbbox((0, 0), l, font=font)
            box_w = max(box_w, bbox[2] - bbox[0])
        box_w += 80; box_h = len(lines) * line_h + 60
        
        # Colocar el cuadro de texto en la parte INFERIOR-CENTRAL
        x = (1080 - box_w) / 2
        y = 1920 - box_h - 250 # Subido un poco más para que no se pierda en la UI de YouTube
        
        # Fondo tipo "Narrative Bar" más elegante
        draw.rectangle([x, y, x + box_w, y + box_h], fill=(0,0,0,180), outline=(255, 215, 0), width=5)
        
        curr_y = y + 30
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_x = x + (box_w - line_w) / 2
            # Sombra de texto para máxima legibilidad
            draw.text((line_x + 3, curr_y + 3), line, font=font, fill=(0,0,0,255))
            draw.text((line_x, curr_y), line, font=font, fill=(255, 215, 0)) # Oro Divine
            curr_y += line_h
            
        final_img = Image.alpha_composite(img, overlay)
        output = io.BytesIO()
        final_img.convert('RGB').save(output, format='JPEG', quality=95)
        return output.getvalue()

    def auto_split_story(self, description):
        """Divide una descripción larga en 7 fragmentos (Panel 2 al 8)."""
        sentences = re.split(r'(?<=[.!?])\s+', description)
        panels = []
        # El usuario pidió del 2 al 8 (7 paneles en total)
        for i in range(7):
            idx = i % len(sentences)
            text = sentences[idx]
            
            # Guardarraíles Bíblicos
            guardrails = "biblical times, humble setting, no modern objects."
            if "Jesús" in text or "Jesus" in text:
                guardrails += " Jesus Christ should look like a dignified first-century Jewish man with a beard and humble robe, compassionate expression, NO jewelry, NO modern hair styles."
            if "mujer" in text or "woman" in text:
                guardrails += " Modest biblical clothing, respectful posture."
            if "alabastro" in text or "jar" in text:
                guardrails += " The jar should be a simple ancient clay or stone vessel, NO glass pump bottles."

            prompt = f"Comic panel {i+2}: {text}. {guardrails} Cinematic lighting, high detail."
            panels.append({"prompt": prompt, "text": text, "panel_num": i+2})
        return panels

    def forge_panels(self, story_panels):
        """Genera los paneles de imagen con IA y los convierte en clips de video verticales (9:16)."""
        if isinstance(story_panels, str):
            story_panels = self.auto_split_story(story_panels)
            
        panel_vids = []
        for i, p in enumerate(story_panels):
            print(f"🎨 Forjando Panel {i+1}...")
            img_data = self.generate_image_hf(p['prompt'])
            if not img_data: continue
            
            baked_data = self.add_text_to_image(img_data, p['text'])
            
            panel_img = self.temp_dir / f"panel_{i}.jpg"
            with open(panel_img, "wb") as f: f.write(baked_data)
            
            vid_path = self.assets_dir / f"panel_{i}.mp4"
            
            # Zoompan corregido para verticalidad 9:16
            zoom_filter = (
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
                "zoompan=z='min(zoom+0.0015,1.5)':d=165:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            )
            
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(panel_img),
                "-vf", f"{zoom_filter},fade=t=in:st=0:d=0.5",
                "-t", "5.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(vid_path)
            ], check=True)
            panel_vids.append(str(vid_path))
        return panel_vids

    def generate_lesson_video(self, teaching):
        """Genera la pantalla de enseñanza usando master_teaching_bg.mp4."""
        output_video = self.temp_dir / "lesson_screen.mp4"
        input_video = self.public_dir / "master_teaching_bg.mp4"
        
        # Primero generamos el overlay de texto
        overlay = Image.new('RGBA', (1080, 1920), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        font_path = "/System/Library/Fonts/Helvetica.ttc"
        try: f_main = ImageFont.truetype(font_path, 70)
        except: f_main = ImageFont.load_default()

        def draw_wrapped_centered(y, text, font, color, max_w=22):
            words = text.split(); lines = []; curr = ""
            for w in words:
                if len(curr + w) < max_w: curr += w + " "
                else: lines.append(curr.strip()); curr = w + " "
            lines.append(curr.strip())
            cy = y
            for l in lines:
                bbox = draw.textbbox((0,0), l, font=font)
                w = bbox[2] - bbox[0]
                draw.text(((1080-w)/2 + 4, cy + 4), l, font=font, fill=(0,0,0,255))
                draw.text(((1080-w)/2, cy), l, font=font, fill=color)
                cy += 95

        draw_wrapped_centered(800, teaching, f_main, (255, 215, 0))
        overlay_path = self.temp_dir / "lesson_overlay.png"
        overlay.save(overlay_path)
        
        if input_video.exists():
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-i", str(overlay_path),
                "-filter_complex", 
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]; "
                "[bg][1:v]overlay=enable='between(t,0,7)',fade=t=in:st=0:d=0.5,fade=t=out:st=6.5:d=0.5",
                "-t", "7", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
        else:
            print("⚠️ Video teaching no encontrado, usando fallback de imagen.")
            bg_image = self.public_dir / "master_teaching_bg.png"
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-t", "7", "-i", str(bg_image),
                "-i", str(overlay_path),
                "-filter_complex", 
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg]; "
                "[bg][1:v]overlay=enable='between(t,0,7)',fade=t=in:st=0:d=0.5,fade=t=out:st=6.5:d=0.5",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
            ]
            
        subprocess.run(cmd, check=True)
        return output_video

    def render_motion_comic(self, panel_paths, title, audio_url, output_filename, story_data):
        """Ensambla el comic final con el pipeline vertical corregido y branding premium."""
        print(f"🎬 Ensamblando comic vertical: {title}")
        output_path = self.renders_dir / output_filename
        
        intro_path = self.generate_title_video(title)
        teaching_vid = self.generate_lesson_video(story_data.get('teaching', ''))
        
        # Outro: Logo Animado + Textos Solicitados
        outro_source = self.public_dir / "outro.mp4"
        if not outro_source.exists(): # Intentar en assets/video si no está en public
            outro_source = self.base_dir / "assets/video/outro.mp4"
            
        outro_final = self.temp_dir / "outro_branded.mp4"
        
        if outro_source.exists():
            print(f"🎬 Preparando cierre premium con: {outro_source.name}")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(outro_source),
                "-vf", (
                    "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
                    "drawtext=text='@MusiChris Studio':fontcolor=gold:fontsize=75:"
                    "x=(w-text_w)/2:y=(h/2)+250:box=1:boxcolor=black@0.4:boxborderw=10,"
                    "drawtext=text='Caminemos Juntos En fe':fontcolor=white:fontsize=45:"
                    "x=(w-text_w)/2:y=(h/2)+380:box=1:boxcolor=black@0.4:boxborderw=8"
                ),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(outro_final)
            ], check=True)
        else:
            print("🎬 Generando outro de emergencia (Logo no encontrado)...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=6",
                "-vf", (
                    "drawtext=text='@MusiChris Studio':fontcolor=gold:fontsize=75:"
                    "x=(w-text_w)/2:y=(h/2)+250,"
                    "drawtext=text='Caminemos Juntos En fe':fontcolor=white:fontsize=45:"
                    "x=(w-text_w)/2:y=(h/2)+380"
                ),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(outro_final)
            ], check=True)
        
        print(f"✅ Outro listo en: {outro_final}")
        
        vids = [intro_path] + panel_paths + [str(teaching_vid), str(outro_final)]
        
        # Normalización y Lista de Concatenación
        concat_list = self.temp_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for v in vids:
                norm_v = self.temp_dir / f"norm_{Path(v).name}"
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(v),
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(norm_v)
                ], check=True)
                f.write(f"file '{norm_v.absolute()}'\n")
        
        # 1. Unir videos (Silencioso)
        temp_silent = self.temp_dir / "temp_silent.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy", str(temp_silent)
        ], check=True)
        
        # 2. Mezclar Audio
        r = requests.get(audio_url)
        audio_path = self.temp_dir / "temp_audio.mp3"
        with open(audio_path, "wb") as f: f.write(r.content)
        
        subprocess.run([
            "ffmpeg", "-y", "-i", str(temp_silent),
            "-i", str(audio_path),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0", "-map", "1:a:0", "-shortest",
            str(output_path)
        ], check=True)
        
        return str(output_path)

if __name__ == "__main__":
    import sys
    import re
    if len(sys.argv) < 4:
        print("Uso: python comic_engine.py <titulo> <descripcion> <audio_url>")
        sys.exit(1)
        
    title = sys.argv[1]
    description = sys.argv[2]
    audio_url = sys.argv[3]
    
    try:
        engine = MusiChrisComicEngine()
        print(f"🚀 Iniciando forja local para: {title}")
        
        # 1. Generar paneles
        panel_paths = engine.forge_panels(description)
        
        # 2. Renderizar video final
        output_filename = "final_comic.mp4"
        story_data = {
            'teaching': description.split('.')[-1] or description 
        }
        
        final_path = engine.render_motion_comic(panel_paths, title, audio_url, output_filename, story_data)
        
        if os.path.exists(final_path):
            print(f"✨ ¡GLORIA A DIOS! Forja completada en: {final_path}")
            # Crear archivo de éxito para el workflow
            with open("FORJA_EXITOSA", "w") as f: f.write("DONE")
        else:
            print(f"❌ ERROR: El archivo no se encontró en {final_path}")
            sys.exit(1)
            
    except Exception as e:
        import traceback
        print(f"💥 ERROR CRÍTICO EN EL MOTOR:")
        traceback.print_exc()
        sys.exit(1)
