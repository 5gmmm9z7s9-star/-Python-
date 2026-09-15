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
pygame.display.set_caption("流体模拟器 - 右下角胶囊版")

clock = pygame.time.Clock()

# 提前创建好所有字体对象
font_slider = pygame.font.Font(None, 22)
font_title = pygame.font.Font(None, 26)
font_btn = pygame.font.Font(None, 22)
font_medium = pygame.font.Font(None, 18)
font_fps = pygame.font.Font(None, 18)  # 胶囊信息专用字体

# 模拟参数
params = {
    "resolution": 48,
    "density": 1.2,
    "speed": 0.8,
    "vortex": 1.2,
    "radius": 30,
}

# 20 种精心调配的流体色彩主题配置
color_palettes = [
    {"name": "Rainbow",    "type": "dynamic", "hue_start": 0, "hue_range": 360, "preview_hues": (0, 120, 240, 360)},
    {"name": "Neon Blue",  "type": "range", "base": (180, 240), "preview_hues": (180, 210, 240)}, 
    {"name": "Cyberpunk",  "type": "range", "base": (280, 340), "preview_hues": (280, 310, 340)}, 
    {"name": "Sunset",     "type": "range", "base": (10, 50),    "preview_hues": (10, 30, 50)},    
    {"name": "Emerald",    "type": "range", "base": (100, 160),  "preview_hues": (100, 130, 160)},  
    {"name": "Flame",      "type": "range", "base": (0, 25),     "preview_hues": (0, 12, 25)},     
    {"name": "Amethyst",   "type": "range", "base": (240, 280),  "preview_hues": (240, 260, 280)}, 
    {"name": "Sakura",     "type": "range", "base": (330, 360),  "preview_hues": (330, 345, 360)}, 
    {"name": "Golden",     "type": "range", "base": (40, 65),    "preview_hues": (40, 52, 65)},    
    {"name": "Aurora",     "type": "range", "base": (140, 180),  "preview_hues": (140, 160, 180)}, 
    {"name": "Deep Space", "type": "range", "base": (200, 260),  "preview_hues": (200, 230, 260)},
    {"name": "Neon Pink",  "type": "range", "base": (300, 330),  "preview_hues": (300, 315, 330)},
    {"name": "Matrix",     "type": "range", "base": (110, 140),  "preview_hues": (110, 125, 140)},
    {"name": "Lava",       "type": "range", "base": (15, 40),     "preview_hues": (15, 28, 40)},   
    {"name": "Arctic",     "type": "range", "base": (170, 210),  "preview_hues": (170, 190, 210)},
    {"name": "Toxic",      "type": "range", "base": (70, 100),   "preview_hues": (70, 85, 100)},  
    {"name": "Twilight",   "type": "range", "base": (260, 300),  "preview_hues": (260, 280, 300)},
    {"name": "Peach",      "type": "range", "base": (20, 45),    "preview_hues": (20, 32, 45)},   
    {"name": "Galaxy",     "type": "range", "base": (270, 320),  "preview_hues": (270, 295, 320)},
    {"name": "Mint",       "type": "range", "base": (130, 165),  "preview_hues": (130, 148, 165)},
]
current_palette_idx = 0

panel_expanded = True
ui_alpha = 255.0        
idle_timer = 0          
IDLE_LIMIT = 120        

last_motion_pos = None
cached_panel_surf = None
cached_panel_w, cached_panel_h = 0, 0

# 缓存所有调色盘的平滑渐变预览 Surface
preview_surfs = []
for pal in color_palettes:
    preview_w, preview_h = 40, 15
    p_surf = pygame.Surface((preview_w, preview_h))
    hues = pal["preview_hues"]
    
    for px in range(preview_w):
        t = px / (preview_w - 1) if preview_w > 1 else 0
        seg_idx = min(int(t * (len(hues) - 1)), len(hues) - 2)
        local_t = (t * (len(hues) - 1)) - seg_idx
        
        h1 = hues[seg_idx]
        h2 = hues[seg_idx + 1]
        
        if abs(h2 - h1) > 180:
            if h2 > h1: h1 += 360
            else: h2 += 360
        curr_h = (h1 + (h2 - h1) * local_t) % 360
        
        c = pygame.Color(0)
        c.hsva = (curr_h, 95, 100, 100)
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

  def draw(self, surface, panel_y, alpha_int):
    rx, ry = self.x, panel_y + self.y
    self.rect.topleft = (rx, ry)
    pygame.draw.rect(surface, (45, 45, 60, alpha_int), self.rect, border_radius=6)
    val_range = self.max_val - self.min_val
    fill_w = int(self.w * (self.val - self.min_val) / val_range)
    pygame.draw.rect(surface, (0, 160, 255, alpha_int), pygame.Rect(rx, ry, fill_w, self.h), border_radius=6)
    pygame.draw.rect(surface, (100, 110, 140, alpha_int), self.rect, 2, border_radius=6)
    
    text_copy = self.text_surf.copy()
    text_copy.set_alpha(alpha_int)
    surface.blit(text_copy, (rx, ry - 22))
    return self.rect

  def check_hit(self, pos, panel_y):
    self.hit_rect.topleft = (self.x, panel_y + self.y)
    return self.hit_rect.collidepoint(pos)

  def update_val(self, pos):
    rel_x = max(0, min(pos[0] - self.x, self.w))
    self.val = self.min_val + (rel_x / self.w) * (self.max_val - self.min_val)
    self.text_surf = font_slider.render(f"{self.name}: {self.val:.2f}", True, (255, 255, 255))


sliders = [
    Slider(20, 50, 230, 20, 16, 128, params["resolution"], "Resolution"),
    Slider(20, 130, 230, 20, 0.1, 3.0, params["density"], "Density"),
    Slider(20, 210, 230, 20, 0.1, 2.0, params["speed"], "Speed"),
    Slider(20, 290, 230, 20, 0.0, 3.0, params["vortex"], "Vortex"),
    Slider(20, 370, 230, 20, 5, 60, params["radius"], "Radius"),
]

palette_button_rects = []
particles = []
active_touches = {}  
running = True
hue = 0

title_surface = font_title.render("Fluid Multi-Touch Panel", True, (255, 255, 255))
palette_title = font_slider.render("Color Themes (20)", True, (200, 210, 230))
collapse_text = font_btn.render("Collapse ▼", True, (255, 255, 255))
expand_text = font_btn.render("Expand Panel ▲", True, (255, 255, 255))

while running:
  current_width, current_height = screen.get_size()
  panel_height = 480 if panel_expanded else 0
  panel_y = current_height - panel_height
  sim_height = panel_y

  screen.fill((12, 12, 16), (0, 0, current_width, current_height))
  toggle_btn_rect = pygame.Rect(current_width // 2 - 50, panel_y + 8, 100, 28) if panel_expanded else pygame.Rect(current_width // 2 - 60, current_height - 42, 120, 32)

  has_real_interaction = False
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False

    evt_pos, evt_id, action_type = None, None, None
    if event.type == pygame.FINGERDOWN:
      evt_pos, evt_id, action_type = (int(event.x * current_width), int(event.y * current_height)), f"f_{event.finger_id}", 'DOWN'
    elif event.type == pygame.FINGERMOTION:
      evt_pos, evt_id, action_type = (int(event.x * current_width), int(event.y * current_height)), f"f_{event.finger_id}", 'MOTION'
    elif event.type == pygame.FINGERUP:
      evt_id, action_type = f"f_{event.finger_id}", 'UP'
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
      evt_pos, evt_id, action_type = event.pos, "mouse_1", 'DOWN'
    elif event.type == pygame.MOUSEMOTION:
      evt_pos, evt_id, action_type = event.pos, "mouse_1", 'MOTION'
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
      evt_id, action_type = "mouse_1", 'UP'

    if action_type == 'DOWN':
      has_real_interaction, last_motion_pos = True, evt_pos
      if toggle_btn_rect.collidepoint(evt_pos):
        panel_expanded = not panel_expanded
      elif panel_expanded and evt_pos[1] >= sim_height:
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
      else:
        active_touches[evt_id] = evt_pos

    elif action_type == 'MOTION':
      if evt_pos:
        has_real_interaction = True
        if panel_expanded and evt_pos[1] >= sim_height:
          for slider in sliders:
            if slider.dragging: slider.update_val(evt_pos)
        elif evt_id in active_touches:
          active_touches[evt_id] = evt_pos

    elif action_type == 'UP':
      last_motion_pos = None
      if evt_id in active_touches: del active_touches[evt_id]
      for slider in sliders: slider.dragging = False

  ui_alpha += ((255.0 if (len(active_touches) > 0 or has_real_interaction or panel_expanded) else 40.0) - ui_alpha) * 0.25
  ui_alpha_int = int(max(40, min(255, ui_alpha)))

  params["resolution"] = int(sliders[0].val)
  params["density"] = sliders[1].val
  params["speed"] = sliders[2].val
  params["vortex"] = sliders[3].val
  params["radius"] = int(sliders[4].val)

  # 批量化生成粒子
  active_palette = color_palettes[current_palette_idx]
  for touch_id, pos in list(active_touches.items()):
    tx, ty = pos
    if panel_expanded and ty >= sim_height: continue

    if active_palette["type"] == "dynamic":
      hue = (hue + 3) % 360
      curr_hue = hue
    else:
      b_min, b_max = active_palette["base"]
      curr_hue = np.random.uniform(b_min, b_max) % 360

    color_rgb = pygame.Color(0)
    color_rgb.hsva = (curr_hue, 95, 100, 100)
    c_tuple = (color_rgb.r, color_rgb.g, color_rgb.b)

    count = int(params["density"] * 3)
    if count > 0:
      offsets_x = (np.random.rand(count) - 0.5) * params["radius"]
      offsets_y = (np.random.rand(count) - 0.5) * params["radius"]
      vxs = (np.random.rand(count) - 0.5) * 2
      vys = (np.random.rand(count) - 0.5) * 2

      new_particles = [{
          "x": tx + offsets_x[i], "y": ty + offsets_y[i],
          "vx": vxs[i], "vy": vys[i],
          "color": c_tuple, "life": 255.0
      } for i in range(count)]
      particles.extend(new_particles)

  # 粒子更新与渲染
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
    p["life"] -= 2.5

    if p["life"] <= 0 or not (0 <= p["x"] < current_width) or not (0 <= p["y"] < current_height):
      continue
    if panel_expanded and p["y"] >= sim_height: continue

    next_particles.append(p)
    r = max(1, int(params["radius"] * 0.25 * (p["life"] / 255.0) * params["density"]))
    pygame.draw.circle(screen, p["color"], (int(p["x"]), int(p["y"])), r)

  particles = next_particles
  if len(particles) > 2000:
    particles = heapq.nlargest(2000, particles, key=lambda item: item["life"])

  # UI 渲染
  if panel_expanded:
    if cached_panel_surf is None or cached_panel_w != current_width or cached_panel_h != panel_height:
      cached_panel_w, cached_panel_h = current_width, panel_height
      cached_panel_surf = pygame.Surface((cached_panel_w, cached_panel_h), pygame.SRCALPHA)
    else:
      cached_panel_surf.fill((0, 0, 0, 0))

    pygame.draw.rect(cached_panel_surf, (22, 22, 30, ui_alpha_int), cached_panel_surf.get_rect())
    pygame.draw.line(cached_panel_surf, (70, 70, 95, ui_alpha_int), (0, 0), (current_width, 0), 2)
    
    title_copy = title_surface.copy()
    title_copy.set_alpha(ui_alpha_int)
    cached_panel_surf.blit(title_copy, (20, 15))
    screen.blit(cached_panel_surf, (0, panel_y))

    for slider in sliders: slider.draw(screen, panel_y, ui_alpha_int)

    palette_x_start, palette_y_start = 265, 48
    title_p_copy = palette_title.copy()
    title_p_copy.set_alpha(ui_alpha_int)
    screen.blit(title_p_copy, (palette_x_start, palette_y_start - 26))

    palette_button_rects.clear()
    col_w, box_h = 132, 42
    max_palette_right = palette_x_start  # 用于计算右侧胶囊的起始位置
    for idx, pal in enumerate(color_palettes):
      bx = palette_x_start + (idx // 10) * 138
      by = panel_y + palette_y_start + (idx % 10) * 44
      brect = pygame.Rect(bx, by, col_w, box_h)
      palette_button_rects.append(brect)
      if brect.right > max_palette_right:
        max_palette_right = brect.right

      is_selected = (idx == current_palette_idx)
      pygame.draw.rect(screen, (50, 90, 140, ui_alpha_int) if is_selected else (35, 35, 48, ui_alpha_int), brect, border_radius=6)
      pygame.draw.rect(screen, (0, 180, 255, ui_alpha_int) if is_selected else (70, 75, 100, ui_alpha_int), brect, 2, border_radius=6)

      name_copy = font_medium.render(pal["name"], True, (255, 255, 255))
      name_copy.set_alpha(ui_alpha_int)
      screen.blit(name_copy, (bx + 8, by + 12))

      preview_x, preview_y = bx + col_w - 40 - 8, by + 13
      p_surf = preview_surfs[idx]
      if ui_alpha_int < 255:
        temp_p = p_surf.copy()
        temp_p.set_alpha(ui_alpha_int)
        screen.blit(temp_p, (preview_x, preview_y))
      else:
        screen.blit(p_surf, (preview_x, preview_y))
      pygame.draw.rect(screen, (150, 150, 180, ui_alpha_int), (preview_x, preview_y, 40, 15), 1, border_radius=3)

    btn_surf = pygame.Surface((100, 28), pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, (60, 60, 85, ui_alpha_int), btn_surf.get_rect(), border_radius=6)
    collapse_copy = collapse_text.copy()
    collapse_copy.set_alpha(ui_alpha_int)
    btn_surf.blit(collapse_copy, (10, 5))
    screen.blit(btn_surf, (toggle_btn_rect.x, toggle_btn_rect.y))

    # === 你画圈的位置（调色盘右侧的空白区域）：放置超大帧率与粒子数胶囊 ===
    capsule_x = max_palette_right + 10
    capsule_w = current_width - capsule_x - 12
    capsule_h = 135  # 让高度完美适配右侧调色盘的高度
    capsule_y = panel_y + palette_y_start

    if capsule_w > 40:
      capsule_surf = pygame.Surface((capsule_w, capsule_h), pygame.SRCALPHA)
      pygame.draw.rect(capsule_surf, (25, 30, 40, int(ui_alpha_int * 0.9)), capsule_surf.get_rect(), border_radius=16)
      pygame.draw.rect(capsule_surf, (0, 200, 150, ui_alpha_int), capsule_surf.get_rect(), 2, border_radius=16)
      
      current_fps = clock.get_fps()
      fps_str = f"FPS: {int(current_fps)}" if current_fps > 0 else "FPS: --"
      part_str = f"Particles: {len(particles)}"

      fps_surf_text = font_fps.render(fps_str, True, (0, 255, 180))
      part_surf_text = font_fps.render(part_str, True, (100, 220, 255))
      
      if ui_alpha_int < 255:
        fps_surf_text.set_alpha(ui_alpha_int)
        part_surf_text.set_alpha(ui_alpha_int)

      capsule_surf.blit(fps_surf_text, (capsule_w // 2 - fps_surf_text.get_width() // 2, 40))
      capsule_surf.blit(part_surf_text, (capsule_w // 2 - part_surf_text.get_width() // 2, 75))
      
      screen.blit(capsule_surf, (capsule_x, capsule_y))

  else:
    btn_surf = pygame.Surface((120, 32), pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, (50, 50, 75, ui_alpha_int), btn_surf.get_rect(), border_radius=8)
    expand_copy = expand_text.copy()
    expand_copy.set_alpha(ui_alpha_int)
    btn_surf.blit(expand_copy, (8, 7))
    screen.blit(btn_surf, (toggle_btn_rect.x, toggle_btn_rect.y))

    # === 面板收起时：右上角紧凑胶囊 ===
    current_fps = clock.get_fps()
    fps_text = f"FPS: {int(current_fps)}" if current_fps > 0 else "FPS: --"
    fps_surf_text = font_fps.render(fps_text, True, (0, 255, 180))
    
    capsule_w = fps_surf_text.get_width() + 20
    capsule_h = 24
    capsule_x = current_width - capsule_w - 15
    capsule_y = 15

    capsule_surf = pygame.Surface((capsule_w, capsule_h), pygame.SRCALPHA)
    pygame.draw.rect(capsule_surf, (30, 35, 45, int(ui_alpha_int * 0.85)), capsule_surf.get_rect(), border_radius=12)
    pygame.draw.rect(capsule_surf, (0, 200, 150, ui_alpha_int), capsule_surf.get_rect(), 1, border_radius=12)
    
    text_rect = fps_surf_text.get_rect(center=(capsule_w // 2, capsule_h // 2))
    if ui_alpha_int < 255:
      fps_surf_text.set_alpha(ui_alpha_int)
    capsule_surf.blit(fps_surf_text, text_rect)
    screen.blit(capsule_surf, (capsule_x, capsule_y))

  pygame.display.flip()
  clock.tick(60)

pygame.quit()
sys.exit()
