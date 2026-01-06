from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import textwrap

# ==========================================
# 캐릭터 설정 (파일 경로 주의!)
# ==========================================
ASSETS = {
    # type: {file, name(표시이름)}
    '김레드': {'file': 'R.PNG', 'name': '김레드'},
    '학생회장': {'file': 'president.png', 'name': '학생회장'},
    '전학생': {'file': 'transfer.png', 'name': '전학생'},
    'default': {'file': 'bg_battle.png', 'name': 'CHALLENGER'}
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        text_input = query_params.get('text', [''])[0].replace('_', ' ')
        img_type = query_params.get('type', ['default'])[0]
        stats_input = query_params.get('stats', ['0:0:0'])[0]

        # 설정 불러오기
        if img_type not in ASSETS: img_type = 'default'
        config = ASSETS[img_type]
        display_name = config.get('name', 'ENEMY') # 표시될 이름
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, config['file'])
        font_path = os.path.join(current_dir, 'font.ttf')

        # ----------------------------------------------------
        # 이미지 로드 (없으면 임시 배경 생성)
        # ----------------------------------------------------
        if os.path.exists(image_path):
            img = Image.open(image_path).convert("RGBA")
            # 배경이 투명한 캐릭터 이미지라면, 뒤에 검은 배경을 깔아줘야 함
            # 여기서는 편의상 그냥 변환만 함 (필요시 배경 합성 로직 추가 가능)
        else:
            # 이미지가 없을 때: 짙은 회색 배경 생성 (검은색 아님)
            img = Image.new('RGB', (1280, 768), color='#202025') 
        
        draw = ImageDraw.Draw(img)

        try:
            font_main = ImageFont.truetype(font_path, 48)
            font_ui = ImageFont.truetype(font_path, 22)
        except:
            font_main = ImageFont.load_default()
            font_ui = ImageFont.load_default()

        # ----------------------------------------------------
        # ★ HUD 그리기 (우측 상단)
        # ----------------------------------------------------
        def draw_hud(aff, rel, dom, char_name):
            base_x = 650
            base_y = 350
            width = 580
            
            # [1] 주도권 (Dominance)
            # ------------------------------------------------
            draw.text((base_x, base_y-30), "USER", font=font_ui, fill="#4169E1")
            
            # ★ 수정됨: ENEMY 대신 캐릭터 이름 출력 (우측 정렬)
            name_w = font_ui.getlength(char_name)
            draw.text((base_x+width-name_w, base_y-30), char_name, font=font_ui, fill="#DC143C")
            
            # 바 그리기
            bar_h = 25
            draw.rectangle([(base_x, base_y), (base_x+width, base_y+bar_h)], outline="white", width=2)
            
            # 슬라이더
            center_x = base_x + (width // 2)
            slider_pos = center_x + (dom * (width / 200))
            slider_pos = max(base_x, min(base_x+width, slider_pos))
            
            draw.rectangle([(base_x, base_y), (slider_pos, base_y+bar_h)], fill="#4169E1")
            draw.rectangle([(slider_pos, base_y), (base_x+width, base_y+bar_h)], fill="#DC143C")
            draw.line([(slider_pos, base_y-5), (slider_pos, base_y+bar_h+5)], fill="white", width=4)

            # [2] 서브 게이지 (Lust / Link)
            # ------------------------------------------------
            sub_y = base_y + 60
            sub_w = 280
            
            # (A) LUST
            aff_r = max(0, min(100, aff)) / 100.0
            draw.text((base_x, sub_y), f"LUST {aff}%", font=font_ui, fill="#FF69B4")
            draw.rectangle([(base_x, sub_y+25), (base_x+sub_w, sub_y+40)], fill="#333333", outline="#555555")
            draw.rectangle([(base_x, sub_y+25), (base_x+(sub_w*aff_r), sub_y+40)], fill="#FF1493")
            
            # (B) LINK
            rel_r = max(0, min(100, rel)) / 100.0
            rx = base_x + width - sub_w
            
            lbl = f"LINK {rel}%"
            lw = font_ui.getlength(lbl)
            draw.text((base_x + width - lw, sub_y), lbl, font=font_ui, fill="#FFD700")
            
            draw.rectangle([(rx, sub_y+25), (base_x+width, sub_y+40)], fill="#333333", outline="#555555")
            fill_start = (base_x + width) - (sub_w * rel_r)
            draw.rectangle([(fill_start, sub_y+25), (base_x+width, sub_y+40)], fill="#FFD700")

        # 실행
        if stats_input and ':' in stats_input:
            try:
                parts = stats_input.split(':')
                if len(parts) >= 3:
                    # ★ display_name 인자 추가
                    draw_hud(int(parts[0]), int(parts[1]), int(parts[2]), display_name)
            except: pass

        # ----------------------------------------------------
        # 대사창 (하단) - 반투명 처리
        # ----------------------------------------------------
        box_h = 250
        
        # 1. 반투명 레이어 생성 (RGBA 모드)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # 2. 반투명 검정 박스 그리기
        # (0, 0, 0, 200) -> 마지막 숫자가 투명도 (0~255). 200이면 약 80% 불투명.
        overlay_draw.rectangle([(0, 768-box_h), (1280, 768)], fill=(0, 0, 0, 200))
        
        # 3. 원본 이미지와 합성
        img = Image.alpha_composite(img.convert('RGBA'), overlay)
        draw = ImageDraw.Draw(img) # 합성된 이미지에 다시 그리기 도구 연결

        # 4. 상단 경계선 (선명하게 보이도록 합성 후 그림)
        draw.line([(0, 768-box_h), (1280, 768-box_h)], fill="#444444", width=3)
        
        # 5. 텍스트 출력
        text_y = 768 - box_h + 50
        lines = textwrap.wrap(text_input, width=40)
        for line in lines:
            draw.text((62, text_y+2), line, font=font_main, fill="#222222") 
            draw.text((60, text_y), line, font=font_main, fill="white")
            text_y += 60

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.end_headers()
        self.wfile.write(img_byte_arr)
        return
