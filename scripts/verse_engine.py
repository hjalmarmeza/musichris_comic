import os
import sys
import requests
import json
import time
import subprocess
import re
import io
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from io import BytesIO
from zhipuai import ZhipuAI
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN MAESTRA (Skill Flow v3.7) ---
load_dotenv()
ZHIPU_API_KEY = os.getenv("API_ZHIPU_AI")
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
FAL_AI_API_KEY = os.getenv("FALTA_AI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Ruta de fuente robusta para GitHub Actions
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not Path(FONT_PATH).exists():
    FONT_PATH = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf"

# Ley de Integridad Visual: Cero elementos modernos
STYLE_PROMPT = (
    ", high-drama biblical cinematography, epic storytelling, dramatic chiaroscuro lighting, "
    "ancient first-century linen tunic and sandals, no modern clothing, "
    "sacred symbolism, movie concept art, masterpiece, ultra-detailed 8k, "
    "vertical 9:16, solemn and powerful atmosphere"
)

NEGATIVE_PROMPT = (
    "glasses, sunglasses, spectacles, eyewear, modern clothes, jewelry, wristwatch, "
    "zippers, buttons, electronics, romantic, physical intimacy, smiling, looking at camera, "
    "distorted faces, blurry, 3d render, cartoon, digital art style"
)

def get_font(size):
    try: return ImageFont.truetype(FONT_PATH, size)
    except: return ImageFont.load_default()

# --- MOTORES DE IA ---
def generate_image_zhipu(prompt):
    if not ZHIPU_API_KEY: return None
    try:
        client = ZhipuAI(api_key=ZHIPU_API_KEY)
        response = client.images.generations(model="cogview-3", prompt=f"{prompt}. Avoid: {NEGATIVE_PROMPT}")
        return requests.get(response.data[0].url).content
    except: return None

def generate_image_deepinfra(prompt):
    if not DEEPINFRA_API_KEY: return None
    url = "https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-schnell"
    headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"}
    try:
        res = requests.post(url, headers=headers, json={"prompt": f"{prompt}. Avoid: {NEGATIVE_PROMPT}"}, timeout=60)
        if res.status_code == 200:
            import base64
            return base64.b64decode(res.json()['images'][0].split(",")[-1])
    except: return None

def generate_image_hf(prompt):
    if not HF_TOKEN: return None
    client = InferenceClient(api_key=HF_TOKEN)
    try:
        image = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
            negative_prompt=NEGATIVE_PROMPT
        )
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except: return None

# --- MOTOR DE PRODUCCIÓN VERSE ENGINE ---
class MusiChrisVerseEngine:
    def __init__(self):
        self.base_dir = Path(os.getcwd()).absolute()
        self.assets_dir = self.base_dir / "assets/panels"
        self.video_assets = self.base_dir / "assets/video"
        self.public_dir = self.base_dir / "public"
        self.temp_dir = self.base_dir / "temp"
        for d in [self.assets_dir, self.temp_dir, self.video_assets, self.public_dir]: d.mkdir(parents=True, exist_ok=True)

    def generate_image_swarm(self, prompt):
        # Ley de Integridad #4: Estética WOW. Forzamos la relación con el versículo.
        full_prompt = "SCENE DESCRIPTION: " + prompt + STYLE_PROMPT
        for name, func in [("Zhipu", generate_image_zhipu), ("DeepInfra", generate_image_deepinfra), ("HF", generate_image_hf)]:
            print(f"  🔍 SUPERVISOR: Intentando con {name}...")
            data = func(full_prompt)
            if data: return data
        return None

    def forge_panels(self, story_data, character_bible="", story_context=""):
        print(f"🎨 Forjando 2 paneles bíblicos de alta fidelidad...")
        panel_vids = []
        safe_story = list(story_data)
        while len(safe_story) < 2: safe_story.append(safe_story[-1])
        
        for i, item in enumerate(safe_story[:2]):
            # Blindaje contra lentes y modernidad (Integridad de Personaje)
            prompt = f"STRICTLY NO GLASSES. Biblical context: {story_context}. Characters: {character_bible}. Scene: {item['prompt']}"
            print(f"🎨 Panel {i+1}/2...")
            img_data = self.generate_image_swarm(prompt)
            if not img_data: raise Exception(f"Fallo en Panel {i+1}")
            
            img = Image.open(io.BytesIO(img_data)).convert('RGB')
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            p_img = self.temp_dir / f"p_{i}.jpg"
            img.save(p_img, quality=95)
            if i == 0: img.save(self.base_dir / "panel_0.jpg", quality=95)
            
            p_vid = self.assets_dir / f"p_{i}.mp4"
            zoom = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,zoompan=z='min(zoom+0.0006,1.2)':d=300:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(p_img), "-vf", f"{zoom},fade=t=in:st=0:d=1", "-t", "10", "-c:v", "libx264", str(p_vid)], check=True)
            panel_vids.append(str(p_vid))
        return panel_vids

    def generate_text_screen(self, text, idx, duration=6):
        """Pantalla de texto sagrado (Sin títulos genéricos)."""
        out = self.temp_dir / f"screen_{idx}.mp4"
        overlay = Image.new('RGB', (1080, 1920), (0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Tamaño de fuente dinámico para impacto (Frases Cortas = Más Grandes)
        f_size = 85 if len(text) < 70 else 60
        font = get_font(f_size)
        
        # Word wrap dinámico
        words = text.split()
        lines = []; curr = ""
        limit = 18 if f_size == 85 else 24
        for w in words:
            if len(curr + w) < limit: curr += w + " "
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        
        line_height = f_size + 25
        y = (1920 - (len(lines) * line_height)) / 2
        for line in lines:
            draw.text((540, y), line, font=font, fill=(255, 215, 0), anchor="mm")
            y += line_height
            
        ov_p = self.temp_dir / f"ov_{idx}.png"
        overlay.save(ov_p)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={duration}", "-i", str(ov_p), "-filter_complex", f"overlay,fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1", "-t", str(duration), "-c:v", "libx264", str(out)], check=True)
        return str(out)

    def assemble_video(self, panel_vids, black_texts, title, audio_url):
        """Ensamblado Final (Restauración de Marca Original)."""
        print("🎬 Ensamblando con Identidad MusiChris Studio...")
        
        # 1. RESTAURAR INTRO ANIMADO ORIGINAL
        intro_file = self.public_dir / "video_pantalla_inicio.mp4"
        intro_out = self.temp_dir / "intro_final.mp4"
        # Usar PIL para el overlay del título (evita fallos de fuente con FFMPEG)
        title_overlay = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        td = ImageDraw.Draw(title_overlay)
        tf = get_font(85)
        words = title.split()
        lines = []; curr = ""
        for w in words:
            if len(curr + w) < 18: curr += w + " "
            else: lines.append(curr.strip()); curr = w + " "
        lines.append(curr.strip())
        ty = (1920 - len(lines) * 110) / 2
        for line in lines:
            td.text((540, ty), line, font=tf, fill=(255, 215, 0, 255), anchor="mm")
            ty += 110
        title_overlay_path = self.temp_dir / "title_overlay.png"
        title_overlay.save(title_overlay_path)
        if intro_file.exists():
            print(f"✅ Usando Intro Original: {intro_file.name}")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(intro_file), "-i", str(title_overlay_path),
                "-filter_complex", "[0:v]scale=1080:1920,setsar=1[bg];[bg][1:v]overlay=0:0",
                "-t", "6", "-c:v", "libx264", str(intro_out)
            ], check=True)
        else:
            intro_out = self.generate_text_screen(title, "intro_fallback", duration=6)

        # 2. RESTAURAR OUTRO ANIMADO CON LOGO
        outro_file = self.video_assets / "outro.mp4"
        outro_out = self.temp_dir / "outro_final.mp4"
        if outro_file.exists():
            print(f"✅ Usando Outro Animado Original: {outro_file.name}")
            subprocess.run(["ffmpeg", "-y", "-i", str(outro_file), "-vf", "scale=1080:1920,setsar=1", "-t", "8", "-c:v", "libx264", str(outro_out)], check=True)
        else:
            outro_out = self.generate_text_screen("@MusiChris Studio", "outro_fallback", duration=8)

        # 3. FILTRO DE TEXTOS (Eliminar 'Reflexión 1', etc.)
        safe_texts = []
        for t in black_texts[:2]:
            clean_t = re.sub(r'^(Reflexión|Parte|Título|Reflexion)\s*(\d+|Bíblica)\s*:?\s*', '', t, flags=re.I)
            safe_texts.append(clean_t)
        while len(safe_texts) < 2: safe_texts.append("@MusiChris Studio")
        
        t1 = self.generate_text_screen(safe_texts[0], "t1")
        t2 = self.generate_text_screen(safe_texts[1], "t2")
        
        # Secuencia Maestra: Intro -> P1 -> T1 -> P2 -> T2 -> Outro
        seq = [str(intro_out), panel_vids[0], t1, panel_vids[1], t2, str(outro_out)]
        
        concat_list = self.temp_dir / "list.txt"
        with open(concat_list, "w") as f:
            for v in seq:
                nv = self.temp_dir / f"n_{Path(v).name}"
                subprocess.run(["ffmpeg", "-y", "-i", v, "-vf", "scale=1080:1920,setsar=1,fps=30", "-c:v", "libx264", "-an", str(nv)], check=True)
                f.write(f"file '{nv.absolute()}'\n")
        
        temp_v = self.temp_dir / "temp_v.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(temp_v)], check=True)
        
        audio = self.temp_dir / "audio.mp3"
        with open(audio, "wb") as f: f.write(requests.get(audio_url).content)
        
        final = self.base_dir / "final_verse.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(temp_v), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)], check=True)
        return str(final)
