import random
import math
import sys
import heapq
import pygame
import numpy as np

# 初始化 Pygame 及其字体模块
pygame.init()
pygame.font.init()

# 竖屏尺寸 (宽度 540，高度 950)
WIDTH, HEIGHT = 540, 950
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("炫彩星光流体面板")

clock = pygame.time.Clock()

# 基础 UI 字体
font_slider = pygame.font.Font(None, 22)
font_title = pygame.font.Font(None, 26)
font_btn = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 20)

# 经典星空色系
STAR_COLORS = [
    (255, 60, 120),    # 深粉红
    (255, 100, 180),   # 粉紫
    (255, 160, 50),    # 金橙
    (255, 230, 80),    # 亮黄
    (80, 180, 255),    # 亮蓝
    (180, 100, 255),   # 艳紫
    (50, 255, 200),    # 青翠绿
    (255, 255, 255),   # 纯白
]

# 模拟参数
params = {
    "resolution": 48,
    "density": 1.0,
    "speed": 0.8,
    "vortex": 1.2,
    "radius": 35,
}

# 粒子形状类型: 0=圆, 1=星光爱心, 2=星, 3=菱形
particle_shape_mode = 1
shape_data = [
    {"symbol": "●", "name": "Circle"},
    {"symbol": "♥", "name": "StarHeart"},
    {"symbol": "★", "name": "Star"},
    {"symbol": "◆", "name": "Diamond"}
]

STAR_TEMPLATE = []
for i in range(5):
    angle_outer = i * (2 * math.pi / 5) - math.pi / 2
    angle_inner = angle_outer + math.pi / 5
    STAR_TEMPLATE.append((math.cos(angle_outer), math.sin(angle_outer), 1.0))
    STAR_TEMPLATE.append((math.cos(angle_inner), math.sin(angle_inner), 0.4))

# 全局复用随机数池
RANDOM_POOL_SIZE = 5000
rand_pool_x = np.random.rand(RANDOM_POOL_SIZE) - 0.5
rand_pool_y = np.random.rand(RANDOM_POOL_SIZE) - 0.5
rand_pool_vx = (np.random.rand(RANDOM_POOL_SIZE) - 0.5) * 1.5
rand_pool_vy = (np.random.rand(RANDOM_POOL_SIZE) - 0.5) * 1.5
rand_pool_idx = 0

def get_pooled_randoms(count):
    global rand_pool_idx
    if rand_pool_idx + count >= RANDOM_POOL_SIZE:
        rand_pool_idx = 0
    idx = rand_pool_idx
    rand_pool_idx += count
    return rand_pool_x[idx:idx+count], rand_pool_y[idx:idx+count], rand_pool_vx[idx:idx+count], rand_pool_vy[idx:idx+count]

# ==================== 绘制函数 ====================
def draw_particle(surface, mode, x, y, size, color):
    if mode == 1 or mode == 0:
        pygame.draw.circle(surface, color, (int(x), int(y)), max(1, int(size)))
    elif mode == 2:
        points = [(x + cos_a * size * 1.5 * sf, y + sin_a * size * 1.5 * sf) for cos_a, sin_a, sf in STAR_TEMPLATE]
        pygame.draw.polygon(surface, color, points)
    elif mode == 3:
        points = [(x, y - size * 1.5), (x + size * 1.2, y), (x, y + size * 1.5), (x - size * 1.2, y)]
        pygame.draw.polygon(surface, color, points)

# 一键消出特效状态变量
burst_effect_active = False
burst_particles = []

def trigger_one_key_burst(active_parts):
    global burst_effect_active, burst_particles
    burst_effect_active = True
    burst_particles = []
    for p in active_parts:
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(6.0, 15.0)
        burst_particles.append({
            "x": p["x"], "y": p["y"],
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "color": p["color"],
            "life": 380.0
        })

# 20种颜色主题（只有最后一种 Rainbow Matrix 为全混色，其余19种为纯单色）
color_palettes = [
    {"name": "StarGlow", "type": "star_preset", "single_hue": 0, "preview_hues": (330, 280, 45, 190)},
    {"name": "Neon Blue", "type": "single", "single_hue": 210, "preview_hues": (210, 210)},
    {"name": "Cyberpunk", "type": "single", "single_hue": 310, "preview_hues": (310, 310)},
    {"name": "Sunset", "type": "single", "single_hue": 30, "preview_hues": (30, 30)},
    {"name": "Emerald", "type": "single", "single_hue": 130, "preview_hues": (130, 130)},
    {"name": "Amethyst", "type": "single", "single_hue": 280, "preview_hues": (280, 280)},
    {"name": "Ruby Red", "type": "single", "single_hue": 0, "preview_hues": (0, 0)},
    {"name": "Amber Gold", "type": "single", "single_hue": 45, "preview_hues": (45, 45)},
    {"name": "Mint Fresh", "type": "single", "single_hue": 150, "preview_hues": (150, 150)},
    {"name": "Deep Ocean", "type": "single", "single_hue": 230, "preview_hues": (230, 230)},
    {"name": "Hot Pink", "type": "single", "single_hue": 330, "preview_hues": (330, 330)},
    {"name": "Neon Lime", "type": "single", "single_hue": 100, "preview_hues": (100, 100)},
    {"name": "Lavender", "type": "single", "single_hue": 265, "preview_hues": (265, 265)},
    {"name": "Coral Reef", "type": "single", "single_hue": 20, "preview_hues": (20, 20)},
    {"name": "Turquoise", "type": "single", "single_hue": 180, "preview_hues": (180, 180)},
    {"name": "Electric Purple", "type": "single", "single_hue": 290, "preview_hues": (290, 290)},
    {"name": "Solar Flare", "type": "single", "single_hue": 32, "preview_hues": (32, 32)},
    {"name": "Spring Bud", "type": "single", "single_hue": 110, "preview_hues": (110, 110)},
    {"name": "Arctic Frost", "type": "single", "single_hue": 205, "preview_hues": (205, 205)},
    {"name": "Rainbow Matrix", "type": "range", "base": (0, 360), "preview_hues": (0, 120, 240, 360)},
]
current_palette_idx = 0
panel_expanded = True

# 预渲染主题色条
preview_surfs = []
for pal in color_palettes:
    preview_w, preview_h = 65, 22
    p_surf = pygame.Surface((preview_w, preview_h))
    hues = pal["preview_hues"]
    for px in range(preview_w):
        t = px / (preview_w - 1) if preview_w > 1 else 0
        seg_idx = min(int(t * (len(hues) - 1)), len(hues) - 2)
        local_t = (t * (len(hues) - 1)) - seg_idx
        h1, h2 = hues[seg_idx], hues[seg_idx + 1]
        if abs(h2 - h1) > 180:
            if h2 > h1: h1 += 360
            else: h2 += 360
        curr_h = (h1 + (h2 - h1) * local_t) % 360
        c = pygame.Color(0)
        c.hsva = (curr_h, 100, 100, 100)
        pygame.draw.line(p_surf, (c.r, c.g, c.b), (px, 0), (px, preview_h - 1))
    preview_surfs.append(p_surf)

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, val, name):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.min_val, self.max_val, self.val, self.name = min_val, max_val, val, name
        self.dragging = False
        self.text_surf = font_slider.render(f"{self.name}: {self.val:.2f}", True, (255, 255, 255))
        self.rect = pygame.Rect(x, y, w, h)
        self.hit_rect = pygame.Rect(x, y, w, h).inflate(20, 20)

    def draw(self, surface, panel_y):
        rx, ry = self.x, panel_y + self.y
        self.rect.topleft = (rx, ry)
        pygame.draw.rect(surface, (55, 55, 75), self.rect, border_radius=6)
        val_range = self.max_val - self.min_val
        fill_w = int(self.w * (self.val - self.min_val) / val_range)
        pygame.draw.rect(surface, (0, 180, 255), pygame.Rect(rx, ry, fill_w, self.h), border_radius=6)
        pygame.draw.rect(surface, (130, 140, 170), self.rect, 2, border_radius=6)
        surface.blit(self.text_surf, (rx, ry - 22))
        return self.rect

    def check_hit(self, pos, panel_y):
        self.hit_rect.topleft = (self.x, panel_y + self.y)
        return self.hit_rect.collidepoint(pos)

    def update_val(self, pos):
        rel_x = max(0, min(pos[0] - self.x, self.w))
        self.val = self.min_val + (rel_x / self.w) * (self.max_val - self.min_val)
        self.text_surf = font_slider.render(f"{self.name}: {self.val:.2f}", True, (255, 255, 255))

sliders = [
    Slider(20, 50, 220, 20, 16, 128, params["resolution"], "Resolution"),
    Slider(20, 130, 220, 20, 0.1, 3.0, params["density"], "Density"),
    Slider(20, 210, 220, 20, 0.1, 2.0, params["speed"], "Speed"),
    Slider(20, 290, 220, 20, 0.0, 3.0, params["vortex"], "Vortex"),
    Slider(20, 370, 220, 20, 5, 60, params["radius"], "Radius")
]

palette_button_rects = []
particles = []
active_touches = {}
running = True

title_surface = font_title.render("Fluid Multi-Touch Panel", True, (255, 255, 255))
palette_title = font_slider.render("Color Themes (20)", True, (230, 240, 255))
collapse_text = font_btn.render("Collapse ▼", True, (255, 255, 255))
expand_text = font_btn.render("Expand Panel ▲", True, (255, 255, 255))

shape_btn_rect = pygame.Rect(0, 0, 0, 0)
burst_btn_rect = pygame.Rect(0, 0, 0, 0)
clear_btn_rect = pygame.Rect(0, 0, 0, 0)

while running:
    current_width, current_height = screen.get_size()
    panel_height = 510
    panel_y = current_height - panel_height
    sim_height = panel_y

    screen.fill((12, 12, 16))
    toggle_btn_rect = pygame.Rect(current_width // 2 - 60, panel_y + 8, 120, 32) if panel_expanded else pygame.Rect(current_width // 2 - 70, current_height - 48, 140, 36)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        evt_pos, evt_id, action_type = None, None, None
        if event.type == pygame.FINGERDOWN:
            evt_pos, evt_id, action_type = (int(event.x * current_width), int(event.y * current_height)), f"f_{event.finger_id}", "DOWN"
        elif event.type == pygame.FINGERMOTION:
            evt_pos, evt_id, action_type = (int(event.x * current_width), int(event.y * current_height)), f"f_{event.finger_id}", "MOTION"
        elif event.type == pygame.FINGERUP:
            evt_id, action_type = f"f_{event.finger_id}", "UP"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            evt_pos, evt_id, action_type = event.pos, "mouse_1", "DOWN"
        elif event.type == pygame.MOUSEMOTION:
            evt_pos, evt_id, action_type = event.pos, "mouse_1", "MOTION"
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            evt_id, action_type = "mouse_1", "UP"

        if action_type == "DOWN" and evt_pos:
            if toggle_btn_rect.collidepoint(evt_pos):
                panel_expanded = not panel_expanded
            elif panel_expanded and clear_btn_rect.collidepoint(evt_pos):
                particles.clear()
                active_touches.clear()
            elif panel_expanded and burst_btn_rect.collidepoint(evt_pos):
                trigger_one_key_burst(particles)
                particles.clear()
                active_touches.clear()
            elif panel_expanded and shape_btn_rect.collidepoint(evt_pos):
                particle_shape_mode = (particle_shape_mode + 1) % len(shape_data)
            elif panel_expanded:
                clicked_palette = False
                for idx, rect in enumerate(palette_button_rects):
                    if rect.collidepoint(evt_pos):
                        current_palette_idx = idx
                        clicked_palette = True
                        break
                if not clicked_palette:
                    for slider in sliders:
                        if slider.check_hit(evt_pos, panel_y):
                            slider.dragging = True
                            slider.update_val(evt_pos)
                            break
                    if evt_pos[1] < sim_height:
                        active_touches[evt_id] = evt_pos
            else:
                if evt_pos[1] < sim_height:
                    active_touches[evt_id] = evt_pos

        elif action_type == "MOTION" and evt_pos:
            if panel_expanded and evt_pos[1] >= sim_height:
                for slider in sliders:
                    if slider.dragging: slider.update_val(evt_pos)
            elif evt_id in active_touches:
                active_touches[evt_id] = evt_pos

        elif action_type == "UP":
            if evt_id in active_touches: del active_touches[evt_id]
            for slider in sliders: slider.dragging = False

    params["resolution"] = int(sliders[0].val)
    params["density"] = sliders[1].val
    params["speed"] = sliders[2].val
    params["vortex"] = sliders[3].val
    params["radius"] = int(sliders[4].val)

    active_palette = color_palettes[current_palette_idx]
    for touch_id, pos in list(active_touches.items()):
        tx, ty = pos
        if panel_expanded and ty >= sim_height: continue

        if active_palette["type"] == "star_preset":
            c_tuple = random.choice(STAR_COLORS)
        elif active_palette["type"] == "single":
            color_rgb = pygame.Color(0)
            color_rgb.hsva = (active_palette["single_hue"], 100, 100, 100)
            c_tuple = (color_rgb.r, color_rgb.g, color_rgb.b)
        else:
            curr_hue = np.random.uniform(0, 360)
            color_rgb = pygame.Color(0)
            color_rgb.hsva = (curr_hue, 100, 100, 100)
            c_tuple = (color_rgb.r, color_rgb.g, color_rgb.b)

        count = int(params["density"] * 2)
        if count > 0:
            off_x, off_y, v_x, v_y = get_pooled_randoms(count)
            new_particles = [{
                "x": tx + off_x[i] * params["radius"], "y": ty + off_y[i] * params["radius"],
                "vx": v_x[i] * 1.5, "vy": v_y[i] * 1.5,
                "color": c_tuple, "life": 255.0
            } for i in range(count)]
            particles.extend(new_particles)

    if burst_effect_active:
        next_burst = []
        for bp in burst_particles:
            bp["x"] += bp["vx"]
            bp["y"] += bp["vy"]
            bp["life"] -= 4.5
            if bp["life"] > 0:
                next_burst.append(bp)
                # 增大爆发消出时的圆点尺寸
                draw_particle(screen, particle_shape_mode, bp["x"], bp["y"], 8, bp["color"])
        burst_particles = next_burst
        if not burst_particles:
            burst_effect_active = False

    next_particles = []
    speed_mult = params["speed"] * 2.5
    vortex_val = params["vortex"] * 0.3
    touch_list = list(active_touches.values())

    for p in particles:
        p["vx"] *= 0.96
        p["vy"] *= 0.96
        for tx, ty in touch_list:
            dx, dy = p["x"] - tx, p["y"] - ty
            dist_sq = dx * dx + dy * dy
            if dist_sq < 32400:
                dist = math.sqrt(dist_sq) + 1e-5
                p["vx"] += (-dy / dist) * vortex_val
                p["vy"] += (dx / dist) * vortex_val

        p["x"] += p["vx"] * speed_mult
        p["y"] += p["vy"] * speed_mult
        p["life"] -= 3.0

        if p["life"] <= 0 or not (0 <= p["x"] < current_width) or not (0 <= p["y"] < current_height):
            continue
        if panel_expanded and p["y"] >= sim_height: continue

        next_particles.append(p)
        # 增大发射时每个圆点的基础半径系数（从 0.20 调大到 0.35）
        r = max(3, int(params["radius"] * 0.35 * (p["life"] / 255.0) * params["density"] * 0.6))
        draw_particle(screen, particle_shape_mode, p["x"], p["y"], r, p["color"])

    particles = next_particles
    
    if len(particles) > 1000:
        particles = heapq.nlargest(1000, particles, key=lambda item: item["life"])

    if panel_expanded:
        pygame.draw.rect(screen, (22, 22, 30), (0, panel_y, current_width, panel_height))
        pygame.draw.line(screen, (90, 90, 120), (0, panel_y), (current_width, panel_y), 2)
        screen.blit(title_surface, (20, panel_y + 15))

        for slider in sliders:
            slider.draw(screen, panel_y)

        palette_x_start, palette_y_start = 240, 48
        screen.blit(palette_title, (palette_x_start, panel_y + palette_y_start - 26))

        palette_button_rects.clear()
        col_w, box_h = 168, 28
        max_palette_right = palette_x_start
        for idx, pal in enumerate(color_palettes):
            bx = palette_x_start + (idx // 10) * 174
            by = panel_y + palette_y_start + (idx % 10) * 28
            brect = pygame.Rect(bx, by, col_w, box_h)
            palette_button_rects.append(brect)
            if brect.right > max_palette_right: max_palette_right = brect.right

            is_selected = (idx == current_palette_idx)
            pygame.draw.rect(screen, (70, 120, 180) if is_selected else (45, 45, 60), brect, border_radius=6)
            pygame.draw.rect(screen, (0, 220, 255) if is_selected else (100, 110, 140), brect, 1, border_radius=6)
            
            screen.blit(font_medium.render(pal["name"], True, (255, 255, 255)), (bx + 8, by + 4))

            preview_x, preview_y = bx + col_w - 65 - 6, by + 3
            screen.blit(preview_surfs[idx], (preview_x, preview_y))

        pygame.draw.rect(screen, (70, 70, 100), toggle_btn_rect, border_radius=8)
        screen.blit(collapse_text, (toggle_btn_rect.x + 10, toggle_btn_rect.y + 6))

        right_area_left = max_palette_right + 12
        right_area_width = current_width - right_area_left - 12
        if right_area_width > 40:
            capsule_w = right_area_width
            capsule_x = right_area_left
            capsule_y = panel_y + palette_y_start

            btn_h = 68
            btn_gap = 12

            shape_btn_rect = pygame.Rect(capsule_x, capsule_y, capsule_w, btn_h)
            pygame.draw.rect(screen, (60, 85, 120), shape_btn_rect, border_radius=8)
            pygame.draw.rect(screen, (0, 180, 255), shape_btn_rect, 2, border_radius=8)
            curr_info = shape_data[particle_shape_mode]
            s_text = font_btn.render(f"Shape: {curr_info['symbol']} {curr_info['name']}", True, (230, 245, 255))
            screen.blit(s_text, s_text.get_rect(center=shape_btn_rect.center))

            burst_btn_rect = pygame.Rect(capsule_x, shape_btn_rect.bottom + btn_gap, capsule_w, btn_h)
            pygame.draw.rect(screen, (220, 130, 30), burst_btn_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 200, 100), burst_btn_rect, 2, border_radius=8)
            b_text = font_btn.render("Burst Clear", True, (255, 255, 240))
            screen.blit(b_text, b_text.get_rect(center=burst_btn_rect.center))

            clear_btn_rect = pygame.Rect(capsule_x, burst_btn_rect.bottom + btn_gap, capsule_w, btn_h)
            pygame.draw.rect(screen, (160, 40, 40), clear_btn_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 100, 100), clear_btn_rect, 2, border_radius=8)
            cl_text = font_btn.render("Screen Clear", True, (255, 230, 230))
            screen.blit(cl_text, cl_text.get_rect(center=clear_btn_rect.center))
    else:
        shape_btn_rect = pygame.Rect(0, 0, 0, 0)
        burst_btn_rect = pygame.Rect(0, 0, 0, 0)
        clear_btn_rect = pygame.Rect(0, 0, 0, 0)

        pygame.draw.rect(screen, (60, 60, 90), toggle_btn_rect, border_radius=8)
        screen.blit(expand_text, (toggle_btn_rect.x + 10, toggle_btn_rect.y + 8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
