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
import platform

def safe_ffmpeg_text(text):
    """Escapa caracteres especiales para filtros drawtext de FFmpeg en Linux."""
    if not text: return ""
    # Reemplazos críticos para evitar que FFmpeg rompa el filtro
    t = text.replace(":", "\\:").replace("'", "\u2019").replace(",", "\\,")
    t = t.replace('"', '').replace('=', '\\=')
    return t

# Configuración Maestra
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "black-forest-labs/FLUX.1-schnell"
client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)

STYLE_PROMPT = (
    ", clean digital comic book art style, bold outlines, cel shading, "
    "vivid colors, first century biblical setting, professional illustration, "
    "historically accurate clothing, 9:16 vertical composition"
)
NEGATIVE_PROMPT = (
    "crown, king crown, diadem, tiara, royal headpiece, "
    "modern objects, soap dispensers, jewelry on men, earrings on men, modern accessories, "
    "sunglasses, romantic kiss, seductive pose, revealing clothing, electricity, neon, plastic, "
    "glass bottle, glass flask, glass jar, decanter, glass pump bottles, "
    "computers, phones, distorted faces, blurry, "
    "modern architecture, tattoos, watches, cars, oil painting, photorealistic"
)

# Fuente instalada vía apt-get en el workflow (fonts-dejavu-core)
# Ruta confirmada en Ubuntu/GitHub Actions: /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font(size):
    """Carga la fuente DejaVu instalada vía apt-get. Ruta fija y confirmada."""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception as e:
        print(f"⚠️ ERROR: No se encontró {FONT_PATH}. Asegúrate de instalar fonts-dejavu-core en el workflow.")
        raise e  # Falla explícitamente para no producir texto invisible

def generate_image_hf_direct(prompt, retries=3):
    """Genera imagen usando FLUX.1-schnell estilo comic digital bíblico."""
    for i in range(retries):
        try:
            print(f"  🖼️ Generando imagen (Comic Digital - Intento {i+1})...")
            image = client.text_to_image(
                prompt,
                model=MODEL_ID,
                negative_prompt=NEGATIVE_PROMPT,
            )
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            print(f"  ✅ Imagen generada ({len(img_bytes)//1024}KB)")
            return img_bytes
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
        """Genera la pantalla inicial estandarizada para Linux (30fps, yuv420p)."""
        output_video = self.assets_dir / "intro_rendered.mp4"
        input_video = self.public_dir / "video_pantalla_inicio.mp4"
        
        print(f"🎬 Generando intro blindada para: {title}")
        clean_title = safe_ffmpeg_text(title)
        
        if len(clean_title) > 22:
            words = clean_title.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            drawtext_title = (
                f"drawtext=fontfile='{FONT_PATH}':text='{line1}':fontcolor=gold:fontsize=55:"
                f"x=(w-text_w)/2:y=(h/2)-220:box=1:boxcolor=black@0.5:boxborderw=15,"
                f"drawtext=fontfile='{FONT_PATH}':text='{line2}':fontcolor=gold:fontsize=55:"
                f"x=(w-text_w)/2:y=(h/2)-140:box=1:boxcolor=black@0.5:boxborderw=15"
            )
        else:
            drawtext_title = (
                f"drawtext=fontfile='{FONT_PATH}':text='{clean_title}':fontcolor=gold:fontsize=55:"
                f"x=(w-text_w)/2:y=(h/2)-150:box=1:boxcolor=black@0.5:boxborderw=15"
            )
        
        drawtext_brand = (
            f"drawtext=fontfile='{FONT_PATH}':text='@MusiChris Studio':fontcolor=white:fontsize=40:"
            f"x=(w-text_w)/2:y=(h/2)+60:box=1:boxcolor=black@0.4:boxborderw=12"
        )
        
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p,{drawtext_title},{drawtext_brand}"
        
        if input_video.exists():
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-vf", vf, "-t", "6", "-c:v", "libx264", "-preset", "fast", str(output_video)
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=#1a0a00:s=1080x1920:r=30:d=6",
                "-vf", vf, "-c:v", "libx264", "-preset", "fast", str(output_video)
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
        """Hornea el texto completo con caja dinámica y escalado de fuente si es necesario."""
        img = Image.open(io.BytesIO(img_data)).convert('RGBA')
        
        # Redimensionado 9:16
        w, h = img.size
        aspect = 1080/1920
        if w/h > aspect:
            new_w = int(h * aspect)
            left = (w - new_w) / 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / aspect)
            top = (h - new_h) / 2
            img = img.crop((0, top, w, top + new_h))
        
        img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        # Escalado dinámico de fuente: Empezar en 72, bajar hasta 50 si hay mucho texto
        current_font_size = 72
        if len(text) > 150: current_font_size = 60
        if len(text) > 250: current_font_size = 50
        
        font = get_font(current_font_size)
        
        # Envoltura de texto inteligente
        max_chars_per_line = 25 if current_font_size < 60 else 20
        words = text.split(); lines = []; curr = ""
        for w in words:
            if len(curr + w) < max_chars_per_line: curr += w + " "
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        lines = [l for l in lines if l]

        line_h = current_font_size + 20
        box_w = 0
        for l in lines:
            bbox = draw.textbbox((0, 0), l, font=font)
            box_w = max(box_w, bbox[2] - bbox[0])
        
        box_w = min(box_w + 80, 1000)
        box_h = len(lines) * line_h + 60
        
        # Posición: Siempre en la parte inferior, subiendo si la caja es alta
        x = (1080 - box_w) / 2
        y = 1920 - box_h - 220 
        
        # Dibujar caja narrativa dorada
        draw.rectangle([x, y, x + box_w, y + box_h], fill=(0,0,0,190), outline=(255, 215, 0), width=5)
        
        curr_y = y + 30
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lx = x + (box_w - lw) / 2
            draw.text((lx + 3, curr_y + 3), line, font=font, fill=(0,0,0,255))
            draw.text((lx, curr_y), line, font=font, fill=(255, 215, 0))
            curr_y += line_h
            
        final_img = Image.alpha_composite(img, overlay)
        output = io.BytesIO()
        final_img.convert('RGB').save(output, format='JPEG', quality=95)
        return output.getvalue()

    def auto_split_story(self, description):
        """Divide toda la historia en 7 bloques continuos (paneles 2 al 8)."""
        sentences = re.split(r'(?<=[.!?])\s+', description)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        num_panels = 7
        avg = len(sentences) / num_panels
        
        panels = []
        last = 0.0
        for i in range(num_panels):
            # Agrupar oraciones para asegurar continuidad total
            curr = int(last + avg) if i < num_panels - 1 else len(sentences)
            chunk = sentences[int(last):curr]
            panel_text = ' '.join(chunk)
            last = curr
            
            # Si el bloque es muy largo para un solo panel, resumir a las primeras 2 oraciones del bloque
            # Pero solo si el bloque tiene más de 3 oraciones.
            if len(chunk) > 3:
                panel_text = ' '.join(chunk[:2]) + " " + chunk[-1]

            art_style = "clean digital comic book illustration, bold ink outlines, cel shading, vivid colors, biblical first century"
            if any(k in panel_text for k in ["Jesús", "Jesus", "Señor"]):
                art_style += ". Jesus: dignified man, beard, humble brown robe, sandals"
            if any(k in panel_text for k in ["mujer", "pecadora"]):
                art_style += ". Woman: long modest robe, head covered"
            if any(k in panel_text for k in ["alabastro", "frasco", "perfume"]):
                art_style += ". Jar: small ancient clay pot, ceramic"
            if any(k in panel_text for k in ["fariseo", "Simón"]):
                art_style += ". Pharisee: ornate robe, beard, serious"

            prompt = f"{art_style}. Scene: {panel_text}"
            panels.append({"prompt": prompt, "text": panel_text, "panel_num": i+2})
            
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
            
            # Zoompan forzado a 30fps para evitar errores de concatenación en Linux
            zoom_filter = (
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
                "zoompan=z='min(zoom+0.001,1.3)':d=165:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            )
            
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(panel_img),
                "-vf", f"{zoom_filter},fade=t=in:st=0:d=0.5,format=yuv420p",
                "-t", "5.5", "-c:v", "libx264", "-preset", "fast", str(vid_path)
            ], check=True)
            panel_vids.append(str(vid_path))
        return panel_vids

    def generate_lesson_video(self, teaching):
        """Genera la pantalla de enseñanza blindada para Linux."""
        output_video = self.temp_dir / "lesson_screen.mp4"
        input_video = self.public_dir / "master_teaching_bg.mp4"
        
        clean_teaching = safe_ffmpeg_text(teaching)
        
        # Overlay con caja narrativa
        overlay = Image.new('RGBA', (1080, 1920), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        f_main = get_font(70)

        words = clean_teaching.split()
        lines = []
        curr = ""
        for w in words:
            if len(curr + w) < 22: curr += w + " "
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        lines = [l for l in lines if l]
        
        line_h = 90
        box_w = 0
        for l in lines:
            bbox = draw.textbbox((0, 0), l, font=f_main)
            box_w = max(box_w, bbox[2] - bbox[0])
        box_w = min(box_w + 80, 1000)
        box_h = len(lines) * line_h + 60
        
        x = (1080 - box_w) / 2
        y = 1920 - box_h - 300
        
        draw.rectangle([x, y, x + box_w, y + box_h], fill=(0, 0, 0, 200), outline=(255, 215, 0), width=6)
        
        curr_y = y + 30
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=f_main)
            lw = bbox[2] - bbox[0]
            lx = x + (box_w - lw) / 2
            draw.text((lx + 3, curr_y + 3), line, font=f_main, fill=(0, 0, 0, 255))
            draw.text((lx, curr_y), line, font=f_main, fill=(255, 215, 0))
            curr_y += line_h
        
        overlay_path = self.temp_dir / "lesson_overlay.png"
        overlay.save(overlay_path)
        
        # VF Estandarizado: 1080x1920, 30fps, yuv420p
        vf_base = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p"
        
        if input_video.exists():
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-i", str(overlay_path),
                "-filter_complex", 
                f"[0:v]{vf_base}[bg]; [bg][1:v]overlay=enable='between(t,0,7)',fade=t=in:st=0:d=0.5,fade=t=out:st=6.5:d=0.5",
                "-t", "7", "-c:v", "libx264", str(output_video)
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=#0a0a1a:s=1080x1920:r=30:d=7",
                "-i", str(overlay_path),
                "-filter_complex", 
                f"[0:v]{vf_base}[bg]; [bg][1:v]overlay=enable='between(t,0,7)',fade=t=in:st=0:d=0.5,fade=t=out:st=6.5:d=0.5",
                "-t", "7", "-c:v", "libx264", str(output_video)
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
