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

# --- CONFIGURACIÓN MAESTRA ---
load_dotenv()
ZHIPU_API_KEY = os.getenv("API_ZHIPU_AI")
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
FAL_AI_API_KEY = os.getenv("FALTA_AI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not Path(FONT_PATH).exists():
    FONT_PATH = "/System/Library/Fonts/Supplemental/Verdana Bold.ttf" # Fallback Mac

STYLE_PROMPT = (
    ", cinematic film style, epic realism, volumetric lighting, 8k resolution, "
    "highly detailed, first century biblical setting, professional movie concept art, "
    "historically accurate, 9:16 vertical composition, solemn and sacred atmosphere"
)

NEGATIVE_PROMPT = (
    "romantic, physical intimacy, head-to-head, touching faces, modern objects, "
    "jewelry on men, crown, glasses, blurry, low resolution, distorted faces"
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
        image = client.text_to_image(prompt, model="stabilityai/stable-diffusion-xl-base-1.0")
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except: return None

# --- MOTOR DE PRODUCCIÓN ---
class MusiChrisVerseEngine:
    def __init__(self):
        self.base_dir = Path(os.getcwd()).absolute()
        self.assets_dir = self.base_dir / "assets/panels"
        self.temp_dir = self.base_dir / "temp"
        self.renders_dir = self.base_dir / "renders"
        self.public_dir = self.base_dir / "public"
        for d in [self.assets_dir, self.temp_dir, self.renders_dir]: d.mkdir(parents=True, exist_ok=True)

    def generate_image_swarm(self, prompt):
        full_prompt = prompt + STYLE_PROMPT
        for name, func in [("Zhipu", generate_image_zhipu), ("DeepInfra", generate_image_deepinfra), ("HF", generate_image_hf)]:
            print(f"  🔍 SUPERVISOR: Intentando con {name}...")
            data = func(full_prompt)
            if data: return data
        return None

    def forge_panels(self, story_data, character_bible="", story_context=""):
        """Forja exactamente 4 paneles con consistencia total."""
        print(f"🎨 Forjando secuencia de paneles...")
        panel_vids = []
        
        # ASEGURAR 4 PANELES (Si la IA mandó menos, repetimos el último)
        safe_story = list(story_data)
        while len(safe_story) < 4: safe_story.append(safe_story[-1])
        
        for i, item in enumerate(safe_story[:4]):
            prompt = f"Theme: {story_context}. Characters: {character_bible}. Scene: {item['prompt']}"
            print(f"🎨 Panel {i+1}/4...")
            img_data = self.generate_image_swarm(prompt)
            
            if not img_data: raise Exception(f"Fallo en Panel {i+1}")
            
            # Procesamiento de Imagen a Video (Vertical 9:16)
            img = Image.open(io.BytesIO(img_data)).convert('RGB')
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            p_img = self.temp_dir / f"p_{i}.jpg"
            img.save(p_img, quality=95)
            
            p_vid = self.assets_dir / f"p_{i}.mp4"
            zoom = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,zoompan=z='min(zoom+0.0006,1.2)':d=300:s=1080x1920:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(p_img), "-vf", f"{zoom},fade=t=in:st=0:d=1", "-t", "10", "-c:v", "libx264", str(p_vid)], check=True)
            panel_vids.append(str(p_vid))
        return panel_vids

    def generate_text_screen(self, text, idx):
        out = self.temp_dir / f"text_{idx}.mp4"
        overlay = Image.new('RGBA', (1080, 1920), (0,0,0,255))
        draw = ImageDraw.Draw(overlay)
        font = get_font(60)
        lines = [text[i:i+25] for i in range(0, len(text), 25)]
        y = (1920 - (len(lines)*100))/2
        for line in lines:
            draw.text((540, y), line, font=font, fill=(255, 215, 0), anchor="mm")
            y += 100
        ov_p = self.temp_dir / f"ov_{idx}.png"
        overlay.save(ov_p)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=5", "-i", str(ov_p), "-filter_complex", "overlay,fade=t=in:st=0:d=1,fade=t=out:st=4:d=1", "-t", "5", "-c:v", "libx264", str(out)], check=True)
        return str(out)

    def assemble_video(self, panel_vids, black_texts, title, audio_url):
        """Ensamblado Final del Video."""
        print("🎬 Ensamblando Video Final...")
        intro = self.temp_dir / "intro.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=#1a0a00:s=1080x1920:d=8", "-vf", f"drawtext=text='{title}':fontcolor=gold:fontsize=80:x=(w-text_w)/2:y=(h-text_h)/2", "-c:v", "libx264", str(intro)], check=True)
        
        t1 = self.generate_text_screen(black_texts[0], 1)
        t2 = self.generate_text_screen(black_texts[1], 2)
        
        # Secuencia: Intro + P1 + P2 + T1 + P3 + P4 + T2 + Outro
        seq = [str(intro), panel_vids[0], panel_vids[1], t1, panel_vids[2], panel_vids[3], t2]
        
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
        
        final = self.renders_dir / "final_video.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(temp_v), "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)], check=True)
        return str(final)
