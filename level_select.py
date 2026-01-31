"""
Level selection screen with:
- Toggle between Developer and Gemini maps
- Level grid with circular buttons ("Level 01", etc.)
- Level preview panel on the right
- Play, Exit, Back options (homepage style, smaller)
"""
import os
import json
import pygame
import glob
from scripts.utils import load_image, load_images, Animation
from homepage import generate_level_with_gemini


def _load_level_preview_assets(game_dir):
    """Load minimal assets needed for level preview rendering."""
    assets = {
        'decor': load_images('tiles/decor'),
        'grass': load_images('tiles/grass'),
        'large_decor': load_images('tiles/large_decor'),
        'stone': load_images('tiles/stone'),
        'background': pygame.transform.scale(
            load_image('background2.png'),
            (540, 380)
        ),
    }
    noportalzone_img = load_image('tiles/noportalzone.png')
    noportalzone_img.set_alpha(128)
    assets['noportalzone'] = [pygame.transform.scale(noportalzone_img, (16, 16))]
    spikes_img = pygame.transform.scale(load_image('spikes.png'), (16, 8))
    assets['spikes'] = [spikes_img]
    spring_img = load_image('spring_horizontal.png')
    assets['spring_horizontal'] = [spring_img]
    assets['red_box'] = [spring_img]
    door_img = load_image('tiles/door.png')
    assets['door'] = [door_img]
    key_img = pygame.transform.scale(load_image('tiles/key.png'), (48, 48))
    assets['key'] = [key_img]
    return assets


def _render_level_preview(level_path, width, height, assets, game_dir):
    """Render a level to a preview surface."""
    try:
        with open(level_path, 'r') as f:
            data = json.load(f)
    except Exception:
        return None

    tilemap = data.get('tilemap', {})
    offgrid = data.get('offgrid', [])
    tile_size = data.get('tile_size', 16)

    # Level is typically 34x24 tiles = 544x384
    level_w = 544
    level_h = 384
    preview = pygame.Surface((level_w, level_h))
    preview.blit(assets['background'], (0, 0))

    # Render tilemap tiles
    for loc, tile in tilemap.items():
        pos = tile['pos']
        x, y = pos[0] * tile_size, pos[1] * tile_size
        tile_type = tile['type']
        variant = tile.get('variant', 0)
        if tile_type == 'spawners':
            continue

        if tile_type in assets and tile_type not in ('spikes', 'spring_horizontal', 'red_box', 'door', 'key', 'noportalzone'):
            img = assets[tile_type][min(variant, len(assets[tile_type]) - 1)]
            preview.blit(img, (x, y))
        elif tile_type == 'noportalzone':
            preview.blit(assets['noportalzone'][0], (x, y))
        elif tile_type == 'spikes':
            img = assets['spikes'][0].copy()
            rot = tile.get('rotation', 0)
            if rot != 0:
                img = pygame.transform.rotate(img, -rot)
            if rot == 0:
                preview.blit(img, (x, y + 8))
            else:
                preview.blit(img, (x, y))
        elif tile_type in ('spring_horizontal', 'red_box'):
            preview.blit(assets['spring_horizontal'][0], (x, y))
        elif tile_type in ('door', 'key'):
            img = assets[tile_type][0]
            ox = (tile_size - img.get_width()) // 2
            oy = (tile_size - img.get_height()) // 2
            preview.blit(img, (x + ox, y + oy))

    # Render offgrid
    for tile in offgrid:
        if tile['type'] == 'spawners' and tile['variant'] in (1, 3):
            continue
        if tile['type'] == 'spawners':
            continue
        pos = tile['pos']
        x, y = pos[0], pos[1]
        tile_type = tile['type']
        variant = tile.get('variant', 0)
        if tile_type in assets:
            img = assets[tile_type][min(variant, len(assets[tile_type]) - 1)]
            preview.blit(img, (x, y))

    # Scale to preview size
    scaled = pygame.transform.scale(preview, (width, height))
    return scaled


class LevelSelect:
    def __init__(self):
        pygame.init()
        self.display = pygame.Surface((540, 380), pygame.SRCALPHA)
        self.screen = pygame.display.set_mode((960, 640))
        self.clock = pygame.time.Clock()
        pygame.mouse.set_visible(True)

        game_dir = os.path.dirname(os.path.abspath(__file__))
        maps_dir = os.path.join(game_dir, 'data', 'maps')

        # Background
        bg_path = os.path.join(game_dir, 'data', 'homepage-assets', 'level_selection.png')
        self.background = pygame.transform.scale(
            pygame.image.load(bg_path).convert(),
            self.display.get_size()
        )

        # Level preview assets (cached)
        self._preview_assets = _load_level_preview_assets(game_dir)
        self._preview_cache = {}  # level_path -> surface

        # Fonts
        font_path = os.path.join(game_dir, 'data', 'fonts', 'PressStart2P-vaV7.ttf')
        self.font = pygame.font.Font(font_path, 8)

        # Discover levels
        self.standard_levels = []
        self.gemini_levels = []
        for f in sorted(glob.glob(os.path.join(maps_dir, 'level*.json'))):
            name = os.path.basename(f)
            if name.startswith('level') and name.endswith('.json'):
                num = name[5:-5]
                if num.isdigit():
                    self.standard_levels.append((int(num), f))
        self.standard_levels.sort(key=lambda x: x[0])

        for f in sorted(glob.glob(os.path.join(maps_dir, 'gemini*.json'))):
            name = os.path.basename(f)
            if name.startswith('gemini') and name.endswith('.json'):
                num = name[6:-5]
                if num.isdigit():
                    self.gemini_levels.append((int(num), f))
        self.gemini_levels.sort(key=lambda x: x[0])

        # Margins (consistent on all sides)
        self.margin = 18

        # Title at top - bigger, white text, blue outline
        self.title_font = pygame.font.Font(font_path, 14)
        self.title_y = self.margin
        self.title_toggle_gap = 20

        # Toggle: "developer" or "gemini" - centered on screen
        self.map_type = "developer"
        self.toggle_y = self.title_y + self.title_font.get_height() + self.title_toggle_gap
        self.toggle_height = 24
        self.toggle_bottom_margin = 20
        self.toggle_width = 110
        self.toggle_gap = 10
        toggle_center_x = self.display.get_width() // 2
        self.developer_toggle_rect = pygame.Rect(
            toggle_center_x - self.toggle_width - self.toggle_gap // 2,
            self.toggle_y,
            self.toggle_width,
            self.toggle_height
        )
        self.gemini_toggle_rect = pygame.Rect(
            toggle_center_x + self.toggle_gap // 2,
            self.toggle_y,
            self.toggle_width,
            self.toggle_height
        )

        # Level grid: 4 per row, square with rounded corners
        self.grid_left = self.margin
        self.grid_cols = 4
        self.cell_w = 55
        grid_width = self.grid_cols * self.cell_w
        self.base_grid_top = self.toggle_y + self.toggle_height + self.toggle_bottom_margin
        self.cell_h = 55
        self.square_size = 44
        self.level_font = pygame.font.Font(font_path, 9)
        self.generate_height = 24
        self.generate_grid_gap = 8

        # Spacing between level grid and preview
        self.grid_preview_gap = 18
        self.preview_left = self.grid_left + grid_width + self.grid_preview_gap
        self.preview_top = self.base_grid_top
        self.preview_width = self.display.get_width() - self.preview_left - self.margin
        self.preview_height = 165

        # Generate button (when Gemini) - on top of level squares
        self.generate_rect = pygame.Rect(
            self.grid_left,
            self.base_grid_top,
            grid_width,
            self.generate_height
        )

        # Action buttons (Play, Exit, Back)
        self.options_top_margin = 24
        self.action_line_gap = 18
        self.action_font = pygame.font.Font(font_path, 8)
        self.menu_action_rects = {}

        # State
        self.selected_level_path = None
        self.selection_time = 0.0  # When level was selected (for animations)
        self.hovered = None
        self.clicked = None
        self.click_anim_time = 0.0
        self.elapsed_time = 0.0
        self.is_loading = False

        # Portal sizzle effect (red/white alternating)
        portal_red_imgs = load_images('portal_red')
        portal_white_imgs = load_images('portal_white')
        self.portal_red_anim = Animation(portal_red_imgs, img_dur=5)
        self.portal_white_anim = Animation(portal_white_imgs, img_dur=5)
        self.portal_sizzle_size = self.square_size + 4  # Slightly larger to "cover" the square

        # Game goat sprite for selection animation (player idle)
        goat_idle_imgs = load_images('entities/player/idle')
        self.goat_anim = Animation(goat_idle_imgs, img_dur=6)
        goat_scale = 1.4  # 200% bigger (was 0.7)
        self.goat_w = int(goat_idle_imgs[0].get_width() * goat_scale)
        self.goat_h = int(goat_idle_imgs[0].get_height() * goat_scale)

    def _get_current_levels(self):
        levels = self.standard_levels if self.map_type == "developer" else self.gemini_levels
        return levels

    def _get_levels(self):
        return self._get_current_levels()

    def _get_grid_top(self):
        """Top of level squares - below generate button when Gemini."""
        if self.map_type == "gemini":
            return self.base_grid_top + self.generate_height + self.generate_grid_gap
        return self.base_grid_top

    def _get_level_rect(self, index):
        row, col = index // self.grid_cols, index % self.grid_cols
        grid_top = self._get_grid_top()
        x = self.grid_left + col * self.cell_w + (self.cell_w - self.square_size) // 2
        y = grid_top + row * self.cell_h + (self.cell_h - self.square_size) // 2
        return pygame.Rect(x, y, self.square_size, self.square_size)

    def _get_preview_surface(self, level_path):
        if level_path not in self._preview_cache:
            game_dir = os.path.dirname(os.path.abspath(__file__))
            surf = _render_level_preview(
                level_path,
                self.preview_width,
                self.preview_height,
                self._preview_assets,
                game_dir
            )
            self._preview_cache[level_path] = surf
        return self._preview_cache.get(level_path)

    def update(self, dt):
        self.elapsed_time += dt
        if self.click_anim_time > 0:
            self.click_anim_time = max(0, self.click_anim_time - dt)
        if self.selected_level_path:
            self.portal_red_anim.update()
            self.portal_white_anim.update()
            self.goat_anim.update()

    def _render_outlined(self, text, font, fg=(255, 255, 255), outline=(0, 50, 120), thickness=1):
        base = font.render(text, False, fg)
        w, h = base.get_size()
        surf = pygame.Surface((w + thickness * 2, h + thickness * 2), pygame.SRCALPHA)
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx * dx + dy * dy <= thickness * thickness and (dx or dy):
                    surf.blit(font.render(text, False, outline), (thickness + dx, thickness + dy))
        surf.blit(base, (thickness, thickness))
        return surf

    def _draw_title(self):
        title_surf = self._render_outlined("Level Selection", self.title_font, fg=(255, 255, 255), outline=(0, 80, 180), thickness=2)
        cx = self.display.get_width() // 2
        self.display.blit(title_surf, (cx - title_surf.get_width() // 2, self.title_y))

    def _draw_toggle(self):
        for rect, label, active in [
            (self.developer_toggle_rect, "Developer", self.map_type == "developer"),
            (self.gemini_toggle_rect, "Gemini", self.map_type == "gemini"),
        ]:
            is_hovered = self.hovered == ("toggle", label)
            c = (255, 220, 100) if active else (220, 220, 220)
            if is_hovered and not active:
                c = (240, 240, 240)
            pygame.draw.rect(self.display, c, rect, border_radius=4)
            pygame.draw.rect(self.display, (0, 50, 120), rect, 2, border_radius=4)
            txt = self.font.render(label, False, (0, 50, 120) if active else (120, 120, 120))
            self.display.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def _draw_level_grid(self):
        levels = self._get_levels()
        selected_rect = None
        selected_index = None
        for i, (num, path) in enumerate(levels):
            rect = self._get_level_rect(i)

            # Square with rounded corners: gray when not selected, yellow when selected (like developer toggle)
            is_hovered = self.hovered == ("level", path)
            is_selected = self.selected_level_path == path
            if is_selected:
                selected_rect = rect
                selected_index = i
            color = (135, 206, 235) if is_selected else (220, 220, 220)  # Sky blue when selected, light gray otherwise
            if is_hovered and not is_selected:
                color = (100, 150, 220)  # Blue on hover
            pygame.draw.rect(self.display, color, rect)
            outline_color = (0, 100, 200) if is_selected else (0, 50, 120)  # Blue when selected
            pygame.draw.rect(self.display, outline_color, rect, 2)

            # Level number (2 digits)
            num_str = f"{num:02d}"
            txt_color = (0, 80, 160) if is_selected else (130, 130, 130)  # Blue text when selected
            txt = self.level_font.render(num_str, False, txt_color)
            self.display.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        # Draw portal sizzle and goat on selected level square
        if selected_rect and self.selected_level_path:
            self._draw_selection_effects(selected_rect)

    def _draw_selection_effects(self, rect):
        """Draw goat (behind) and teleporting portal outline (sizzling) on selected level square."""
        # Goat first (behind the sizzling outline)
        sel_elapsed = self.elapsed_time - self.selection_time
        jump_duration = 0.4
        if sel_elapsed < jump_duration:
            # Jump arc: emerge from portal (center of square), pop up, land on square
            t = sel_elapsed / jump_duration
            arc = 4 * t * (1 - t)  # Parabolic: 0 at start/end, 1 at peak (t=0.5)
            # Start: goat half-emerged at bottom of square; peak: 20px above; end: standing
            start_y = rect.bottom - self.goat_h // 2
            peak_offset = -20
            end_y = rect.bottom - self.goat_h
            goat_y = start_y + (end_y - start_y) * t + arc * peak_offset
        else:
            goat_y = rect.bottom - self.goat_h  # Standing on square
        goat_x = rect.centerx - self.goat_w // 2
        goat_img = self.goat_anim.img()
        goat_surf = pygame.transform.scale(goat_img, (self.goat_w, self.goat_h))
        self.display.blit(goat_surf, (int(goat_x), int(goat_y)))

        # Portal sizzle on top (alternate red/white, scaled to cover the square)
        sizzle = int(self.elapsed_time * 5) % 2
        portal_anim = self.portal_red_anim if sizzle == 0 else self.portal_white_anim
        portal_img = portal_anim.img()
        scaled = pygame.transform.scale(portal_img, (self.portal_sizzle_size, self.portal_sizzle_size))
        px = rect.centerx - self.portal_sizzle_size // 2
        py = rect.centery - self.portal_sizzle_size // 2
        self.display.blit(scaled, (px, py))

    def _draw_preview_panel(self):
        # Preview with blue outline and rounded corners - image clipped to match
        preview_rect = pygame.Rect(self.preview_left, self.preview_top, self.preview_width, self.preview_height)
        corner_radius = 8

        if self.selected_level_path:
            surf = self._get_preview_surface(self.selected_level_path)
            if surf:
                # Clip image to rounded corners using mask
                w, h = self.preview_width, self.preview_height
                clipped = pygame.Surface((w, h), pygame.SRCALPHA)
                clipped.blit(surf, (0, 0))
                mask = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=corner_radius)
                clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                self.display.blit(clipped, (self.preview_left, self.preview_top))
        else:
            pygame.draw.rect(self.display, (220, 220, 220), preview_rect, border_radius=corner_radius)
            placeholder = self.font.render("Select a level", False, (100, 100, 100))
            self.display.blit(placeholder, (self.preview_left + (self.preview_width - placeholder.get_width()) // 2,
                                           self.preview_top + (self.preview_height - placeholder.get_height()) // 2))

        # Blue outline (same as level buttons)
        pygame.draw.rect(self.display, (0, 50, 120), preview_rect, 3, border_radius=corner_radius)

    def _get_action_y(self):
        """Y position for action menu - below preview."""
        return self.preview_top + self.preview_height + self.options_top_margin

    def _draw_generate_button(self):
        """Generate Level button - on top of level squares (Gemini mode only)."""
        gen_rect = self.generate_rect
        is_hovered = self.hovered == "generate"
        c = (130, 180, 255) if is_hovered else (100, 150, 255)
        pygame.draw.rect(self.display, c, gen_rect, border_radius=4)
        pygame.draw.rect(self.display, (0, 50, 120), gen_rect, 2, border_radius=4)
        t = self.action_font.render("Generate Level", False, (255, 255, 255))
        self.display.blit(t, (gen_rect.centerx - t.get_width() // 2, gen_rect.centery - t.get_height() // 2))

    def _draw_action_menu(self):
        """Play, Exit, Back - homepage style ("> X <" on hover, yellow when selected)."""
        center_x = self.preview_left + self.preview_width // 2
        action_y = self._get_action_y()

        items = [
            ("play", "Play"),
            ("back", "Back"),
            ("exit", "Exit"),
        ]
        self.menu_action_rects = {}
        for i, (aid, label) in enumerate(items):
            is_hovered = self.hovered == ("action", aid)
            text = f">{label}<" if is_hovered else label
            color = (0, 100, 200) if is_hovered else (95, 95, 95)  # Blue on hover, darker gray otherwise
            s, _ = self._render_text_with_spacing(text, self.action_font, color, 2)
            y = action_y + i * self.action_line_gap
            r = s.get_rect(center=(center_x, y))
            self.display.blit(s, r)
            self.display.blit(s, (r.x + 1, r.y))
            pad = 6
            self.menu_action_rects[aid] = pygame.Rect(r.x - pad, r.y - pad, r.w + pad * 2, r.h + pad * 2)

    def _render_text_with_spacing(self, text, font, color, spacing=2):
        if not text:
            return font.render("", False, color), 0
        chars = [font.render(c, False, color) for c in text]
        w = sum(s.get_width() for s in chars) + (len(text) - 1) * spacing
        h = max(s.get_height() for s in chars)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        x = 0
        for i, s in enumerate(chars):
            surf.blit(s, (x, 0))
            x += s.get_width() + (spacing if i < len(chars) - 1 else 0)
        return surf, w

    def render(self):
        self.display.fill((0, 0, 0))
        self.display.blit(self.background, (0, 0))

        self._draw_title()
        self._draw_toggle()
        if self.map_type == "gemini":
            self._draw_generate_button()
        self._draw_level_grid()
        self._draw_preview_panel()
        self._draw_action_menu()

        if self.is_loading:
            overlay = pygame.Surface(self.display.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.display.blit(overlay, (0, 0))
            s = self.font.render("Generating level...", False, (255, 255, 255))
            self.display.blit(s, (self.display.get_width() // 2 - s.get_width() // 2,
                                 self.display.get_height() // 2 - s.get_height() // 2))

    def update_hover(self, mouse_pos):
        dx = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        dy = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        pos = (dx, dy)
        self.hovered = None

        if self.developer_toggle_rect.collidepoint(pos):
            self.hovered = ("toggle", "Developer")
        elif self.gemini_toggle_rect.collidepoint(pos):
            self.hovered = ("toggle", "Gemini")
        elif self.map_type == "gemini" and self.generate_rect.collidepoint(pos):
            self.hovered = "generate"
        else:
            for aid, rect in self.menu_action_rects.items():
                if rect.collidepoint(pos):
                    self.hovered = ("action", aid)
                    return
            levels = self._get_levels()
            for i, (_, path) in enumerate(levels):
                if self._get_level_rect(i).collidepoint(pos):
                    self.hovered = ("level", path)
                    return

    def handle_click(self, mouse_pos):
        dx = int((mouse_pos[0] / self.screen.get_width()) * self.display.get_width())
        dy = int((mouse_pos[1] / self.screen.get_height()) * self.display.get_height())
        pos = (dx, dy)
        self.clicked = self.hovered
        self.click_anim_time = 0.12

        if self.developer_toggle_rect.collidepoint(pos):
            self.map_type = "developer"
            return None
        if self.gemini_toggle_rect.collidepoint(pos):
            self.map_type = "gemini"
            return None
        if self.map_type == "gemini" and self.generate_rect.collidepoint(pos):
            return "GENERATE_GEMINI"

        for aid, rect in self.menu_action_rects.items():
            if rect.collidepoint(pos):
                if aid == "play" and self.selected_level_path:
                    return self.selected_level_path
                if aid == "back":
                    return "BACK"
                if aid == "exit":
                    return "QUIT"
                return None

        levels = self._get_levels()
        for i, (_, path) in enumerate(levels):
            if self._get_level_rect(i).collidepoint(pos):
                self.selected_level_path = path
                self.selection_time = self.elapsed_time
                return None

        return None


def run_level_select():
    level_select = LevelSelect()

    while True:
        dt = level_select.clock.tick(60) / 1000.0
        level_select.update(dt)
        level_select.update_hover(pygame.mouse.get_pos())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEMOTION:
                level_select.update_hover(event.pos)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                choice = level_select.handle_click(event.pos)

                if choice == "GENERATE_GEMINI":
                    level_select.is_loading = True
                    level_select.render()
                    scaled = pygame.transform.scale(level_select.display, level_select.screen.get_size())
                    level_select.screen.blit(scaled, (0, 0))
                    pygame.display.update()

                    generated = generate_level_with_gemini()
                    level_select.is_loading = False

                    if generated:
                        maps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'maps')
                        level_select.gemini_levels = []
                        for f in sorted(glob.glob(os.path.join(maps_dir, 'gemini*.json'))):
                            name = os.path.basename(f)
                            if name.startswith('gemini') and name.endswith('.json'):
                                num = name[6:-5]
                                if num.isdigit():
                                    level_select.gemini_levels.append((int(num), f))
                        level_select.gemini_levels.sort(key=lambda x: x[0])
                        level_select._preview_cache.clear()
                    else:
                        print("Failed to generate level.")
                    continue

                elif choice == "BACK":
                    return "BACK"
                elif choice == "QUIT":
                    return "QUIT"
                elif choice:
                    return choice

        level_select.render()
        scaled = pygame.transform.scale(level_select.display, level_select.screen.get_size())
        level_select.screen.blit(scaled, (0, 0))
        pygame.display.update()


if __name__ == "__main__":
    print(run_level_select())
