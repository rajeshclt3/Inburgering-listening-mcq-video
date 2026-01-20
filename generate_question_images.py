import os, re, argparse
from PIL import Image, ImageDraw, ImageFont

# ========= CONFIG =========
parser = argparse.ArgumentParser()
parser.add_argument("--input", default="/data/input.txt", help="Input file with audio scripts/questions")
parser.add_argument("--output", default="/data/output_images", help="Output directory for question images")
parser.add_argument("--scenes", default="/data/scenes", help="Path to scenes folder")
args = parser.parse_args()

INPUT_FILE = args.input
OUTPUT_DIR = args.output
SCENES_DIR = args.scenes

# ========= FONT CONFIGURATION =========
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"



TEXT_COLOR        = (0, 0, 0)
HIGHLIGHT_COLOR   = (0, 150, 0)
ANSWER_TEXT_COLOR = (255, 255, 255)
BOUND_COLOR       = (255, 165, 0)   # full-frame orange border

CANVAS_SIZE  = (1100, 600)
IMAGE_SIZE   = (400, 220)
QUESTION_BOX = (40, 260, 480, 300)
OPTIONS_X, OPTIONS_Y, OPTION_GAP = 550, 80, 80

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ========= LOG =========
def log(msg): print(f"[DEBUG] {msg}")


# ========= TEXT HELPERS =========
def wrap_text(draw, text, font, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        test_line = (line + " " + word).strip()
        w = draw.textbbox((0,0), test_line, font=font)[2]
        if w <= max_width: line = test_line
        else: lines.append(line); line = word
    if line: lines.append(line)
    return lines

def draw_wrapped_text(draw, text, x, y, font, fill, max_width, line_spacing=8):
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, fill=fill, font=font)
        y += font.size + line_spacing
    return y


# ========= PARSER =========
def parse_input_file(filename):
    with open(filename, "r", encoding="utf-8") as f: content = f.read()
    blocks = re.findall(r"### AUDIO_SCRIPT_(\d+) ###(.*?)### QUESTIONS_\1 ###", content, re.S)
    data=[]
    for (sid, block) in blocks:
        qblock = re.search(rf"### QUESTIONS_{sid} ###(.*?)(?=(### AUDIO_SCRIPT_|$))", content, re.S)
        qblock = qblock.group(1).strip() if qblock else ""
        qmatch = re.findall(
            r"Q\d+:\s*(.*?)\nA\.\s*(.*?)\nB\.\s*(.*?)\nC\.\s*(.*?)\n(?:D\.\s*(.*?)\n)?ANSWER:\s*([A-D])",
            qblock, re.S)
        qlist=[]
        for i,q in enumerate(qmatch,1):
            qlist.append({
                "id":i,
                "q":q[0].strip(),
                "A":q[1].strip(),"B":q[2].strip(),"C":q[3].strip(),
                "D":q[4].strip() if q[4] else "",
                "answer":q[5].strip()
            })
        data.append({
            "script_id":int(sid),
            "audio_text":block.strip(),
            "questions":qlist
        })
    return data


# ========= DRAW HELPERS =========
def draw_scene_image(base, scene_img_path):
    """Paste top-left small image."""
    draw = ImageDraw.Draw(base)
    img_x, img_y = 40, 20
    if os.path.exists(scene_img_path):
        scene = Image.open(scene_img_path).convert("RGB").resize(IMAGE_SIZE)
        base.paste(scene, (img_x, img_y))
    else:
        draw.rectangle((img_x,img_y,img_x+IMAGE_SIZE[0],img_y+IMAGE_SIZE[1]),
                       fill=(220,220,220))
        draw.text((img_x+40,img_y+100),"Image\nmissing",(80,0,0))


def draw_playing_icon(draw, x, y):
    """Draw circular icon representing audio playing state."""
    r = 45
    # Outer circle
    draw.ellipse([x-r, y-r, x+r, y+r], outline=BOUND_COLOR, width=6)
    # Pause bars to indicate 'playing'
    draw.rectangle([x-15, y-25, x-5, y+25], fill=BOUND_COLOR)
    draw.rectangle([x+5,  y-25, x+15, y+25], fill=BOUND_COLOR)


def draw_full_border(draw):
    draw.rectangle([(0,0),(CANVAS_SIZE[0]-1,CANVAS_SIZE[1]-1)], outline=BOUND_COLOR, width=5)


# ========= QUESTION IMAGE =========
def create_question_card(scene_img_path, q, output_path, highlight_answer=False):
    log(f"Creating {output_path}")
    base = Image.new("RGB", CANVAS_SIZE, (255,255,255))
    draw = ImageDraw.Draw(base)
    fQ = ImageFont.truetype(FONT_PATH, 26)
    fO = ImageFont.truetype(FONT_PATH, 24)

    draw_scene_image(base, scene_img_path)

    # Question text
    qx,qy,w,_ = QUESTION_BOX
    draw_wrapped_text(draw, q["q"], qx, qy, fQ, TEXT_COLOR, w)

    # Options
    oy = OPTIONS_Y
    for opt in ['A','B','C','D']:
        if not q[opt]: continue
        opt_text=f"{opt}. {q[opt]}"
        for ln in wrap_text(draw,opt_text,fO,500):
            if highlight_answer and opt==q['answer']:
                tw = draw.textbbox((0,0),ln,font=fO)[2]
                th = draw.textbbox((0,0),ln,font=fO)[3]
                draw.rectangle([(OPTIONS_X-10,oy-4),(OPTIONS_X+tw+10,oy+th+4)],
                               fill=HIGHLIGHT_COLOR)
                draw.text((OPTIONS_X,oy),ln,fill=ANSWER_TEXT_COLOR,font=fO)
            else:
                draw.text((OPTIONS_X,oy),ln,fill=TEXT_COLOR,font=fO)
            oy += fO.size + 8
        oy += 15

    draw_full_border(draw)
    base.save(output_path)
    log(f" Saved {output_path}")


# ========= AUDIO SCENE IMAGE =========
def create_audio_scene_image(scene_img_path, sid, output_path_play):
    """Create one clean audio-playing image per scene."""
    log(f"Creating audio-playing scene: {output_path_play}")
    base = Image.new("RGB", CANVAS_SIZE, (255,255,255))
    draw = ImageDraw.Draw(base)

    # Scene image + icon + border
    draw_scene_image(base, scene_img_path)
    draw_playing_icon(draw, 900, 120)
    draw_full_border(draw)

    base.save(output_path_play)
    log(f" Saved {output_path_play}")


# ========= MAIN =========
if __name__=="__main__":
    log("=== KNM Exam Image Generator (Final v5: Single Playing Scene) ===")
    data = parse_input_file(INPUT_FILE)
    for sec in data:
        sid = sec["script_id"]
        scene = os.path.join(SCENES_DIR, f"scene_{sid:02d}.png")

        # Single narration image (playing state only)
        audio_play = os.path.join(OUTPUT_DIR, f"script_{sid:02d}.png")
        create_audio_scene_image(scene, sid, audio_play)

        # Question & Answer images
        for q in sec["questions"]:
            qid=q["id"]
            q_img = os.path.join(OUTPUT_DIR, f"script_{sid:02d}_q{qid:02d}.png")
            a_img = os.path.join(OUTPUT_DIR, f"script_{sid:02d}_q{qid:02d}_answer.png")
            create_question_card(scene,q,q_img,False)
            create_question_card(scene,q,a_img,True)
    log("All narration, question, and answer images generated successfully!")
