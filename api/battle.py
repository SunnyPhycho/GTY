from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from PIL import Image, ImageDraw, ImageFont
import io
import os
import textwrap

ASSETS = {
    '김레드': {'file': 'R.PNG'},
    'default': {'file': 'bg_battle.png', 'x': 1280, 'y': 768, 'color': 'white'}
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        text_input = query_params.get('text', [''])[0].replace('_', ' ')
        stats_input = query_params.get('stats', ['0:0:0'])[0]

        

        try:
            font_main = ImageFont.truetype("font.ttf", 48)
            font_ui = ImageFont.truetype("font.ttf", 22)
        except:
            font_main = font_ui = ImageFont.load_default()

        # ----------------------------------------------------
        # ★ HUD 그리기 (우측 상단 배치)
        # ----------------------------------------------------
        def draw_hud(aff, rel, dom):
            # 기준점: 화면 오른쪽 구역 (x=650 ~ 1230)
            base_x = 650
            base_y = 50
            width = 580  # HUD 전체 너비
            
            # 1. 주도권 (Dominance) - 맨 위
            # ------------------------------------------------
            draw.text((base_x, base_y-30), "USER", font=font_ui, fill="#4169E1")
            draw.text((base_x+width-100, base_y-30), "ENEMY", font=font_ui, fill="#DC143C")
            
            # 바 그리기
            bar_h = 25
            draw.rectangle([(base_x, base_y), (base_x+width, base_y+bar_h)], outline="white", width=2)
            
            # 슬라이더 위치 (-100~100)
            center_x = base_x + (width // 2)
            slider_pos = center_x + (dom * (width / 200))
            slider_pos = max(base_x, min(base_x+width, slider_pos))
            
            draw.rectangle([(base_x, base_y), (slider_pos, base_y+bar_h)], fill="#4169E1")
            draw.rectangle([(slider_pos, base_y), (base_x+width, base_y+bar_h)], fill="#DC143C")
            draw.line([(slider_pos, base_y-5), (slider_pos, base_y+bar_h+5)], fill="white", width=4)

            # 2. 서브 게이지 (Lust / Link) - 주도권 아래
            # ------------------------------------------------
            sub_y = base_y + 60
            sub_w = 280 # 반반 나누기엔 좁으니 위아래로 배치? 
                        # 아니면 작게 2열 배치 (width 580이니까 280씩 가능)
            
            # (A) LUST (왼쪽)
            aff_r = max(0, min(100, aff)) / 100.0
            draw.text((base_x, sub_y), f"LUST {aff}%", font=font_ui, fill="#FF69B4")
            draw.rectangle([(base_x, sub_y+25), (base_x+sub_w, sub_y+40)], fill="#333333", outline="#555555")
            draw.rectangle([(base_x, sub_y+25), (base_x+(sub_w*aff_r), sub_y+40)], fill="#FF1493")
            
            # (B) LINK (오른쪽)
            rel_r = max(0, min(100, rel)) / 100.0
            rx = base_x + width - sub_w
            
            # 라벨 우측 정렬
            lbl = f"LINK {rel}%"
            lw = font_ui.getlength(lbl)
            draw.text((base_x + width - lw, sub_y), lbl, font=font_ui, fill="#FFD700")
            
            draw.rectangle([(rx, sub_y+25), (base_x+width, sub_y+40)], fill="#333333", outline="#555555")
            # 오른쪽에서 차오름
            fill_start = (base_x + width) - (sub_w * rel_r)
            draw.rectangle([(fill_start, sub_y+25), (base_x+width, sub_y+40)], fill="#FFD700")

        if stats_input and ':' in stats_input:
            try:
                parts = stats_input.split(':')
                if len(parts) >= 3:
                    draw_hud(int(parts[0]), int(parts[1]), int(parts[2]))
            except: pass

        # ----------------------------------------------------
        # 대사창 (하단)
        # ----------------------------------------------------
        box_h = 250
        # 반투명 박스 (그라데이션 느낌은 못 내도 깔끔하게)
        draw.rectangle([(0, 768-box_h), (1280, 768)], fill="#000000")
        draw.line([(0, 768-box_h), (1280, 768-box_h)], fill="#444444", width=3)
        
        # 텍스트
        text_y = 768 - box_h + 50
        lines = textwrap.wrap(text_input, width=40) # 화면 넓으니 글자수 늘림
        for line in lines:
            draw.text((62, text_y+2), line, font=font_main, fill="#222222") # 그림자
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
