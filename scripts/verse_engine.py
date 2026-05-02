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
    t = text.replace(":", "\\:").replace("'", "\u2019").replace(",", "\\,")
    t = t.replace('"', '').replace('=', '\\=')
    return t

# Configuración Maestra
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "black-forest-labs/FLUX.1-schnell"
client = InferenceClient(provider="hf-inference", api_key=HF_TOKEN)

STYLE_PROMPT = (
    ", cinematic film style, epic realism, volumetric lighting, 8k resolution, "
    "highly detailed, first century biblical setting, professional movie concept art, "
    "historically accurate simple linen clothing, 9:16 vertical composition"
)
NEGATIVE_PROMPT = (
    "crown, king crown, diadem, tiara, royal headpiece, "
    "modern objects, soap dispensers, jewelry on men, earrings on men, modern accessories, "
    "sunglasses, romantic kiss, seductive pose, revealing clothing, electricity, neon, plastic, "
    "glass bottle, glass flask, glass jar, decanter, glass pump bottles, "
    "computers, phones, distorted faces, blurry, "
    "modern architecture, tattoos, watches, cars, oil painting, "
    "classical art, renaissance painting, da vinci style, brush strokes, canvas texture, "
    "sketch, drawing, flat colors, low resolution"
)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def get_font(size):
    """Carga la fuente DejaVu instalada vía apt-get."""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        # Fallback para desarrollo local (macOS)
        try:
            return ImageFont.truetype("/System/Library/Fonts/Supplemental/Verdana Bold.ttf", size)
        except:
            return ImageFont.load_default()

def generate_image_hf_direct(prompt, retries=3):
    """Genera imagen usando FLUX.1-schnell con reintentos y logs."""
    if not HF_TOKEN:
        print("  ❌ ERROR: HF_TOKEN no configurado en el entorno.")
        return None
        
    for i in range(retries):
        try:
            print(f"  🖼️ Generando imagen (Verse Mode - Intento {i+1})...")
            # Usamos el cliente con timeout explícito
            image = client.text_to_image(
                prompt,
                model=MODEL_ID,
            )
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            print(f"  ✅ Imagen generada con éxito (Intento {i+1})")
            return img_byte_arr.getvalue()
        except Exception as e:
            print(f"  ⚠️ Intento {i+1} falló: {str(e)}")
            time.sleep(10)
    return None

class MusiChrisVerseEngine:
    def __init__(self):
        self.base_dir = Path(os.getcwd()).absolute()
        self.assets_dir = self.base_dir / "assets/panels"
        self.renders_dir = self.base_dir / "renders"
        self.temp_dir = self.base_dir / "temp"
        self.public_dir = self.base_dir / "public"
        
        for d in [self.assets_dir, self.renders_dir, self.temp_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def generate_image_hf(self, prompt, retries=3):
        return generate_image_hf_direct(prompt + STYLE_PROMPT, retries)

    def generate_title_video(self, title):
        """Genera la pantalla inicial (8 SEGUNDOS)."""
        output_video = self.assets_dir / "intro_rendered.mp4"
        input_video = self.public_dir / "video_pantalla_inicio.mp4"
        clean_title = safe_ffmpeg_text(title)
        
        if len(clean_title) > 18:
            words = clean_title.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            drawtext_title = (
                f"drawtext=fontfile='{FONT_PATH}':text='{line1}':fontcolor=gold:fontsize=85:"
                f"x=(w-text_w)/2:y=(h-text_h)/2-60:box=1:boxcolor=black@0.6:boxborderw=20,"
                f"drawtext=fontfile='{FONT_PATH}':text='{line2}':fontcolor=gold:fontsize=85:"
                f"x=(w-text_w)/2:y=(h-text_h)/2+60:box=1:boxcolor=black@0.6:boxborderw=20"
            )
        else:
            drawtext_title = (
                f"drawtext=fontfile='{FONT_PATH}':text='{clean_title}':fontcolor=gold:fontsize=95:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.6:boxborderw=25"
            )
        
        drawtext_brand = (
            f"drawtext=fontfile='{FONT_PATH}':text='@MusiChris Studio':fontcolor=white:fontsize=45:"
            f"x=(w-text_w)/2:y=(h/2)+300:box=1:boxcolor=black@0.4:boxborderw=15"
        )
        
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p,{drawtext_title},{drawtext_brand}"
        
        if input_video.exists():
            cmd = ["ffmpeg", "-y", "-i", str(input_video), "-vf", vf, "-t", "8", "-c:v", "libx264", "-preset", "fast", str(output_video)]
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=#1a0a00:s=1080x1920:r=30:d=8", "-vf", vf, "-c:v", "libx264", "-preset", "fast", str(output_video)]
        subprocess.run(cmd, check=True)
        return str(output_video)

    def generate_black_text_screen(self, text, index):
        """Genera pantalla negra de 5s con texto."""
        output_video = self.temp_dir / f"black_screen_{index}.mp4"
        # Para PIL no necesitamos el escape de FFmpeg
        clean_text = text.replace('"', '').replace("'", "’")
        overlay = Image.new('RGBA', (1080, 1920), (0,0,0,255))
        draw = ImageDraw.Draw(overlay)
        f_main = get_font(65)

        # Word wrap mejorado
        words = clean_text.split()
        lines = []; curr = ""
        for w in words:
            if len(curr + w) < 25: curr += w + " "
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        
        line_h = 110
        curr_y = (1920 - (len(lines) * line_h)) / 2
        for line in lines:
            if not line: continue
            bbox = draw.textbbox((0, 0), line, font=f_main)
            lx = (1080 - (bbox[2] - bbox[0])) / 2
            # Sombra sutil
            draw.text((lx + 3, curr_y + 3), line, font=f_main, fill=(30, 30, 30, 200))
            draw.text((lx, curr_y), line, font=f_main, fill=(255, 215, 0))
            curr_y += line_h
        
        overlay_path = self.temp_dir / f"black_overlay_{index}.png"
        overlay.save(overlay_path)
        
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=5",
            "-i", str(overlay_path),
            "-filter_complex", "[0:v][1:v]overlay=enable='between(t,0,5)',fade=t=in:st=0:d=0.5,fade=t=out:st=4.5:d=0.5",
            "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_video)
        ]
        subprocess.run(cmd, check=True)
        return str(output_video)

    def forge_panels(self, story_panels):
        """Genera 4 paneles de 10s. Si la IA falla, usa fondo atmosférico."""
        panel_vids = []
        for i, p in enumerate(story_panels[:4]):
            print(f"🎨 Panel {i+1}/4 (10s)...")
            img_data = self.generate_image_hf(p.get('prompt') or p.get('image_prompt'))
            
            if img_data:
                img = Image.open(io.BytesIO(img_data)).convert('RGB')
            else:
                print(f"  🌫️ Usando respaldo atmosférico para Panel {i+1}")
                # Crear fondo degradado elegante (Deep Indigo)
                img = Image.new('RGB', (1080, 1920), (10, 10, 25))
                draw = ImageDraw.Draw(img)
                f_back = get_font(50)
                txt = "Caminemos Juntos en Fe"
                bbox = draw.textbbox((0, 0), txt, font=f_back)
                draw.text(((1080-(bbox[2]-bbox[0]))/2, 1700), txt, font=f_back, fill=(100, 100, 150))
            
            w, h = img.size
            aspect = 1080/1920
            if w/h > aspect:
                new_w = int(h * aspect); left = (w - new_w) / 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / aspect); top = (h - new_h) / 2
                img = img.crop((0, top, w, top + new_h))
            
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            panel_img = self.temp_dir / f"panel_{i}.jpg"
            img.save(panel_img, quality=95)
            
            vid_path = self.assets_dir / f"panel_{i}.mp4"
            zoom_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,zoompan=z='min(zoom+0.0006,1.2)':d=300:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(panel_img),
                "-vf", f"{zoom_filter},fade=t=in:st=0:d=1,format=yuv420p",
                "-t", "10", "-c:v", "libx264", "-preset", "fast", str(vid_path)
            ], check=True)
            panel_vids.append(str(vid_path))
        return panel_vids

    def render_motion_comic(self, panel_paths, title, audio_url, output_filename, story_data):
        print(f"🎬 Ensamblando Verse Mode...")
        output_path = self.renders_dir / output_filename
        intro_path = self.generate_title_video(title)
        
        black_texts = story_data.get('black_texts', [])
        # Seguro de vida: Garantizar al menos 2 reflexiones
        if not isinstance(black_texts, list): black_texts = []
        while len(black_texts) < 2:
            fallback = ["Caminemos Juntos en Fe", "@MusiChris Studio"]
            black_texts.append(fallback[len(black_texts)])
            
        black1 = self.generate_black_text_screen(black_texts[0], 1)
        black2 = self.generate_black_text_screen(black_texts[1], 2)
        
        outro_final = self.temp_dir / "outro_branded.mp4"
        outro_source = self.public_dir / "outro.mp4"
        if not outro_source.exists(): outro_source = self.base_dir / "assets/video/outro.mp4"
        
        # Outro de 8 SEGUNDOS con textos específicos
        outro_vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
            f"drawtext=fontfile='{FONT_PATH}':text='@MusiChris Studio':fontcolor=gold:fontsize=80:x=(w-text_w)/2:y=(h/2)+200,"
            f"drawtext=fontfile='{FONT_PATH}':text='Caminemos Juntos En Fe':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=(h/2)+320"
        )
        
        if outro_source.exists():
            subprocess.run(["ffmpeg", "-y", "-i", str(outro_source), "-vf", outro_vf, "-t", "8", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(outro_final)], check=True)
        else:
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=8", "-vf", outro_vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(outro_final)], check=True)

        # Secuencia robusta: Intro (8) + Paneles + Reflexiones + Outro (8)
        seq = [intro_path]
        
        # Añadir paneles 1 y 2 si existen
        p12 = panel_paths[:2]
        seq.extend(p12)
        seq.append(black1)
        
        # Añadir paneles 3 y 4 si existen
        p34 = panel_paths[2:4]
        seq.extend(p34)
        seq.append(black2)
        
        seq.append(str(outro_final))
        
        concat_list = self.temp_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for v in seq:
                nv = self.temp_dir / f"norm_{Path(v).name}"
                subprocess.run(["ffmpeg", "-y", "-i", str(v), "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(nv)], check=True)
                f.write(f"file '{nv.absolute()}'\n")
        
        ts = self.temp_dir / "temp_silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(ts)], check=True)
        
        r = requests.get(audio_url); ap = self.temp_dir / "temp_audio.mp3"
        with open(ap, "wb") as f: f.write(r.content)
        
        subprocess.run(["ffmpeg", "-y", "-i", str(ts), "-i", str(ap), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(output_path)], check=True)
        return str(output_path)

if __name__ == "__main__":
    if len(sys.argv) < 4: sys.exit(1)
    title, desc, url = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        engine = MusiChrisVerseEngine()
        # Mock split para 4 paneles
        sentences = re.split(r'(?<=[.!?])\s+', desc)
        panels = [{"prompt": f"Biblical scene: {s}", "text": s} for s in sentences[:4]]
        paths = engine.forge_panels(panels)
        story_data = {'black_texts': [" ".join([p['text'] for p in panels[:2]]), " ".join([p['text'] for p in panels[2:]])]}
        final = engine.render_motion_comic(paths, title, url, "final_comic.mp4", story_data)
        if os.path.exists(final):
            with open("FORJA_EXITOSA", "w") as f: f.write("DONE")
    except Exception:
        import traceback; traceback.print_exc(); sys.exit(1)
