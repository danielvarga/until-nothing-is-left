import heapq
import math
import random
from dataclasses import dataclass, field
from typing import Sequence

import pygame


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 600
CEILING_COLOR = (30, 30, 40)
FLOOR_COLOR = (40, 30, 20)

MAP_LAYOUT = [
    "111111111111111111111",
    "100000000000000000001",
    "101111101111111011101",
    "101000101000001010001",
    "101010101011101011101",
    "101010001010001000101",
    "101011111010111110101",
    "101000001010000010101",
    "101111101011111010101",
    "101000101000001010101",
    "101010101111101011101",
    "101010001000101000101",
    "101011111010101110101",
    "101000000010100010001",
    "101111111110111011101",
    "101000000000001010001",
    "101011111111101011101",
    "100010000000001000001",
    "111111111111111111111",
]

WORLD_MAP = [list(row) for row in MAP_LAYOUT]
MAP_WIDTH = len(WORLD_MAP[0])
MAP_HEIGHT = len(WORLD_MAP)
MONSTER_SPAWNS = [
    (15.5, 9.5),
]
MONSTER_ANIM_FPS = 6

WALL_COLORS = {
    "1": (210, 210, 220),
    "2": (200, 150, 60),
    "3": (160, 80, 80),
    "4": (80, 120, 200),
    "5": (120, 200, 120),
}


@dataclass
class Player:
    x: float
    y: float
    dir_x: float
    dir_y: float
    plane_x: float
    plane_y: float


@dataclass
class Monster:
    x: float
    y: float
    speed: float = 1.2
    pulse: float = field(default_factory=lambda: random.random() * math.tau)
    anim_timer: float = 0.0
    path: list[tuple[int, int]] = field(default_factory=list)
    path_cooldown: float = 0.0


@dataclass
class Pellet:
    x: float
    y: float
    collected: bool = False


def spawn_player() -> Player:
    return Player(x=3.5, y=3.5, dir_x=-1.0, dir_y=0.0, plane_x=0.0, plane_y=0.66)


def spawn_monsters() -> list[Monster]:
    return [Monster(x, y) for x, y in MONSTER_SPAWNS]


def spawn_pellets() -> list[Pellet]:
    pellets: list[Pellet] = []
    for y, row in enumerate(WORLD_MAP):
        for x, tile in enumerate(row):
            if tile == "0":
                pellets.append(Pellet(x + 0.5, y + 0.5))
    return pellets


def load_monster_frames(frame_count: int = 4) -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []
    width, height = 56, 80
    for idx in range(frame_count):
        phase = idx / frame_count
        surf = pygame.Surface((width, height), pygame.SRCALPHA)

        body_color = (120, 5, 5)
        chest_color = (200, 60, 40)
        outline_color = (30, 0, 0)
        horn_color = (240, 240, 240)
        eye_color = (255, 255, 80)

        # shadow halo for depth
        pygame.draw.ellipse(surf, (10, 0, 0, 120), pygame.Rect(8, height - 18, width - 16, 12))

        # torso and legs
        pygame.draw.rect(surf, outline_color, pygame.Rect(width // 2 - 14, 22, 28, 46), border_radius=10)
        pygame.draw.rect(surf, body_color, pygame.Rect(width // 2 - 12, 24, 24, 44), border_radius=8)
        pygame.draw.rect(surf, chest_color, pygame.Rect(width // 2 - 6, 32, 12, 26), border_radius=4)

        # legs
        pygame.draw.rect(surf, outline_color, pygame.Rect(width // 2 - 14, 52, 10, 20), border_radius=6)
        pygame.draw.rect(surf, outline_color, pygame.Rect(width // 2 + 4, 52, 10, 20), border_radius=6)
        pygame.draw.rect(surf, chest_color, pygame.Rect(width // 2 - 12, 54, 8, 18), border_radius=4)
        pygame.draw.rect(surf, chest_color, pygame.Rect(width // 2 + 4, 54, 8, 18), border_radius=4)

        # head
        pygame.draw.ellipse(surf, outline_color, pygame.Rect(width // 2 - 16, 4, 32, 28))
        pygame.draw.ellipse(surf, body_color, pygame.Rect(width // 2 - 14, 6, 28, 24))

        # horns with slight sway
        sway = int(math.sin(phase * math.tau) * 3)
        left_horn = [(width // 2 - 8 - sway, 8), (width // 2 - 20, -6), (width // 2 - 4 - sway, 6)]
        right_horn = [(width // 2 + 8 + sway, 8), (width // 2 + 20, -6), (width // 2 + 4 + sway, 6)]
        pygame.draw.polygon(surf, horn_color, left_horn)
        pygame.draw.polygon(surf, horn_color, right_horn)

        # jaw / teeth animation
        jaw_open = 4 + int(math.sin((phase + 0.25) * math.tau) * 3)
        pygame.draw.rect(surf, outline_color, pygame.Rect(width // 2 - 12, 22, 24, 8))
        pygame.draw.rect(surf, (255, 230, 200), pygame.Rect(width // 2 - 10, 23, 20, jaw_open))
        for tooth in range(4):
            tooth_x = width // 2 - 10 + tooth * 6
            pygame.draw.rect(surf, outline_color, pygame.Rect(tooth_x, 23, 4, jaw_open - 1))

        # eyes
        pygame.draw.circle(surf, eye_color, (width // 2 - 6, 16), 3)
        pygame.draw.circle(surf, eye_color, (width // 2 + 6, 16), 3)

        # arms swinging
        arm_swing = math.sin(phase * math.tau) * 10
        left_arm = [
            (width // 2 - 14, 30),
            (width // 2 - 24 - arm_swing, 40),
            (width // 2 - 18 - arm_swing, 46),
            (width // 2 - 10, 38),
        ]
        right_arm = [
            (width // 2 + 14, 30),
            (width // 2 + 24 + arm_swing, 40),
            (width // 2 + 18 + arm_swing, 46),
            (width // 2 + 10, 38),
        ]
        pygame.draw.polygon(surf, outline_color, left_arm)
        pygame.draw.polygon(surf, outline_color, right_arm)
        left_inner = [(x + 1, y + 1) for x, y in left_arm]
        right_inner = [(x - 1, y + 1) for x, y in right_arm]
        pygame.draw.polygon(surf, chest_color, left_inner)
        pygame.draw.polygon(surf, chest_color, right_inner)

        frames.append(surf)
    return frames


def load_pellet_sprite(size: int = 26) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for radius in range(center, 0, -1):
        intensity = radius / center
        color = (
            int(200 + 55 * intensity),
            int(200 + 55 * intensity),
            80,
            int(60 + 195 * intensity),
        )
        pygame.draw.circle(surf, color, (center, center), radius)
    pygame.draw.circle(surf, (255, 255, 200), (center, center), center // 3)
    return surf


def is_blocking(x: float, y: float) -> bool:
    if x < 0 or y < 0 or x >= MAP_WIDTH or y >= MAP_HEIGHT:
        return True
    tile = WORLD_MAP[int(y)][int(x)]
    return tile != "0"


def move_entity(x: float, y: float, move_x: float, move_y: float) -> tuple[float, float]:
    new_x = x + move_x
    new_y = y + move_y
    if not is_blocking(new_x, y):
        x = new_x
    if not is_blocking(x, new_y):
        y = new_y
    return x, y


def move_player(player: Player, move_x: float, move_y: float) -> None:
    player.x, player.y = move_entity(player.x, player.y, move_x, move_y)


def grid_blocked(tile_x: int, tile_y: int) -> bool:
    if tile_x < 0 or tile_y < 0 or tile_x >= MAP_WIDTH or tile_y >= MAP_HEIGHT:
        return True
    return WORLD_MAP[tile_y][tile_x] != "0"


def astar_path(start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
    if start == goal:
        return [start]
    if grid_blocked(*goal):
        return []

    open_heap: list[tuple[float, tuple[int, int]]] = []
    heapq.heappush(open_heap, (0, start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {start: 0.0}

    def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
            neighbor = (nx, ny)
            if grid_blocked(nx, ny):
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                priority = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (priority, neighbor))

    return []


def rotate_player(player: Player, angle: float) -> None:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    old_dir_x = player.dir_x
    player.dir_x = player.dir_x * cos_a - player.dir_y * sin_a
    player.dir_y = old_dir_x * sin_a + player.dir_y * cos_a
    old_plane_x = player.plane_x
    player.plane_x = player.plane_x * cos_a - player.plane_y * sin_a
    player.plane_y = old_plane_x * sin_a + player.plane_y * cos_a


def update_monsters(monsters: list[Monster], player: Player, delta_time: float) -> None:
    for monster in monsters:
        monster.pulse = (monster.pulse + delta_time * 2.0) % math.tau
        monster.anim_timer = (monster.anim_timer + delta_time) % 1000.0
        monster.path_cooldown -= delta_time

        monster_tile = (int(monster.x), int(monster.y))
        goal_tile = (int(player.x), int(player.y))
        needs_path = (
            monster.path_cooldown <= 0
            or not monster.path
            or monster.path[-1] != goal_tile
            or monster_tile not in monster.path
        )
        if needs_path:
            monster.path = astar_path(monster_tile, goal_tile)
            monster.path_cooldown = 0.4

        target_x = player.x
        target_y = player.y
        if monster.path and len(monster.path) > 1:
            # First node is current tile; follow the next waypoint.
            next_tile = monster.path[1]
            target_x = next_tile[0] + 0.5
            target_y = next_tile[1] + 0.5
            # Drop waypoint if we already moved into it.
            if abs(monster.x - target_x) < 0.1 and abs(monster.y - target_y) < 0.1:
                monster.path.pop(0)
                if len(monster.path) > 1:
                    next_tile = monster.path[1]
                    target_x = next_tile[0] + 0.5
                    target_y = next_tile[1] + 0.5
                else:
                    target_x = player.x
                    target_y = player.y

        dir_x = target_x - monster.x
        dir_y = target_y - monster.y
        distance = math.hypot(dir_x, dir_y)
        if distance > 0.001:
            dir_x /= distance
            dir_y /= distance
        move_x = dir_x * monster.speed * delta_time
        move_y = dir_y * monster.speed * delta_time
        monster.x, monster.y = move_entity(monster.x, monster.y, move_x, move_y)


def collect_pellets(player: Player, pellets: list[Pellet], radius: float = 0.35) -> int:
    collected_now = 0
    for pellet in pellets:
        if pellet.collected:
            continue
        if math.hypot(player.x - pellet.x, player.y - pellet.y) < radius:
            pellet.collected = True
            collected_now += 1
    return collected_now


def player_is_dead(player: Player, monsters: list[Monster]) -> bool:
    for monster in monsters:
        if math.hypot(player.x - monster.x, player.y - monster.y) < 0.4:
            return True
    return False


def nearest_monster_distance(player: Player, monsters: list[Monster]) -> float:
    if not monsters:
        return float("inf")
    return min(math.hypot(player.x - monster.x, player.y - monster.y) for monster in monsters)


def draw_minimap(screen: pygame.Surface, player: Player, monsters: list[Monster], pellets: list[Pellet]) -> None:
    scale = 12
    offset = (10, 10)
    mini_surface = pygame.Surface((MAP_WIDTH * scale, MAP_HEIGHT * scale), pygame.SRCALPHA)
    mini_surface.fill((0, 0, 0, 150))

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            tile = WORLD_MAP[y][x]
            if tile != "0":
                color = WALL_COLORS.get(tile, (150, 150, 150))
                rect = pygame.Rect(x * scale, y * scale, scale, scale)
                pygame.draw.rect(mini_surface, color, rect)

    px = int(player.x * scale)
    py = int(player.y * scale)
    pygame.draw.circle(mini_surface, (255, 50, 50), (px, py), 4)
    end_x = int(px + player.dir_x * 10)
    end_y = int(py + player.dir_y * 10)
    pygame.draw.line(mini_surface, (250, 250, 250), (px, py), (end_x, end_y), 2)

    for pellet in pellets:
        if pellet.collected:
            continue
        rx = int(pellet.x * scale)
        ry = int(pellet.y * scale)
        pygame.draw.circle(mini_surface, (240, 240, 180), (rx, ry), 2)

    for monster in monsters:
        mx = int(monster.x * scale)
        my = int(monster.y * scale)
        pygame.draw.circle(mini_surface, (120, 20, 220), (mx, my), 4)

    screen.blit(mini_surface, offset)


def render_column(screen: pygame.Surface, column: int, draw_start: int, draw_end: int, color: tuple[int, int, int]) -> None:
    pygame.draw.line(screen, color, (column, draw_start), (column, draw_end))


def cast_rays(screen: pygame.Surface, player: Player) -> list[float]:
    depth_buffer = [float("inf")] * SCREEN_WIDTH
    for column in range(SCREEN_WIDTH):
        camera_x = 2 * column / SCREEN_WIDTH - 1
        ray_dir_x = player.dir_x + player.plane_x * camera_x
        ray_dir_y = player.dir_y + player.plane_y * camera_x

        map_x = int(player.x)
        map_y = int(player.y)

        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float("inf")
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float("inf")

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (player.x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - player.x) * delta_dist_x
        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (player.y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - player.y) * delta_dist_y

        hit = False
        side = 0
        tile = "1"
        max_steps = MAP_WIDTH * MAP_HEIGHT
        steps = 0

        while not hit and steps < max_steps:
            steps += 1
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
                hit = True
                tile = "1"
            elif WORLD_MAP[map_y][map_x] != "0":
                tile = WORLD_MAP[map_y][map_x]
                hit = True

        if not hit:
            continue

        if side == 0:
            perp_wall_dist = (side_dist_x - delta_dist_x)
        else:
            perp_wall_dist = (side_dist_y - delta_dist_y)

        perp_wall_dist = max(perp_wall_dist, 0.0001)
        line_height = int(SCREEN_HEIGHT / perp_wall_dist)
        draw_start = max(-line_height // 2 + SCREEN_HEIGHT // 2, 0)
        draw_end = min(line_height // 2 + SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 1)

        base_color = WALL_COLORS.get(tile, (180, 180, 180))
        if side == 1:
            base_color = tuple(int(c * 0.65) for c in base_color)
        render_column(screen, column, draw_start, draw_end, base_color)
        depth_buffer[column] = perp_wall_dist

    return depth_buffer


def draw_monsters(
    screen: pygame.Surface,
    player: Player,
    monsters: list[Monster],
    depth_buffer: list[float],
    frames: Sequence[pygame.Surface],
) -> None:
    det = player.plane_x * player.dir_y - player.dir_x * player.plane_y
    if det == 0:
        return
    inv_det = 1.0 / det
    if not frames:
        return
    for monster in monsters:
        sprite_x = monster.x - player.x
        sprite_y = monster.y - player.y

        transform_x = inv_det * (player.dir_y * sprite_x - player.dir_x * sprite_y)
        transform_y = inv_det * (-player.plane_y * sprite_x + player.plane_x * sprite_y)
        if transform_y <= 0:
            continue

        frame_idx = int(monster.anim_timer * MONSTER_ANIM_FPS) % len(frames)
        frame = frames[frame_idx]

        sprite_screen_x = int((SCREEN_WIDTH / 2) * (1 + transform_x / transform_y))
        sprite_height = max(1, abs(int(SCREEN_HEIGHT / transform_y)))
        sprite_width = max(1, sprite_height)
        draw_start_y = max(-sprite_height // 2 + SCREEN_HEIGHT // 2, 0)
        draw_end_y = min(sprite_height // 2 + SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 1)
        draw_start_x = max(-sprite_width // 2 + sprite_screen_x, 0)
        draw_end_x = min(sprite_width // 2 + sprite_screen_x, SCREEN_WIDTH - 1)

        if draw_start_x >= draw_end_x or draw_start_y >= draw_end_y:
            continue

        scaled_sprite = pygame.transform.smoothscale(frame, (sprite_width, sprite_height))
        glow = (math.sin(monster.pulse) + 1) * 0.5
        tinted_sprite = scaled_sprite.copy()
        tint_strength = int(60 + 120 * glow)
        tinted_sprite.fill((tint_strength, 0, 0), special_flags=pygame.BLEND_RGB_ADD)

        sprite_left = -sprite_width // 2 + sprite_screen_x
        for stripe in range(draw_start_x, draw_end_x):
            tex_x = stripe - sprite_left
            if 0 <= stripe < SCREEN_WIDTH and 0 <= tex_x < sprite_width and depth_buffer[stripe] > transform_y:
                source_rect = pygame.Rect(tex_x, 0, 1, sprite_height)
                screen.blit(tinted_sprite, (stripe, draw_start_y), source_rect)


def draw_collectibles(
    screen: pygame.Surface,
    player: Player,
    pellets: list[Pellet],
    depth_buffer: list[float],
    sprite: pygame.Surface,
) -> None:
    det = player.plane_x * player.dir_y - player.dir_x * player.plane_y
    if det == 0 or not pellets:
        return
    inv_det = 1.0 / det
    sprite_width_base, sprite_height_base = sprite.get_size()
    for pellet in pellets:
        if pellet.collected:
            continue
        sprite_x = pellet.x - player.x
        sprite_y = pellet.y - player.y
        transform_x = inv_det * (player.dir_y * sprite_x - player.dir_x * sprite_y)
        transform_y = inv_det * (-player.plane_y * sprite_x + player.plane_x * sprite_y)
        if transform_y <= 0:
            continue

        sprite_screen_x = int((SCREEN_WIDTH / 2) * (1 + transform_x / transform_y))
        sprite_height = max(1, abs(int((SCREEN_HEIGHT / transform_y) * 0.35)))
        sprite_width = max(1, int(sprite_height * (sprite_width_base / sprite_height_base)))
        draw_start_y = max(-sprite_height // 2 + SCREEN_HEIGHT // 2, 0)
        draw_end_y = min(sprite_height // 2 + SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 1)
        draw_start_x = max(-sprite_width // 2 + sprite_screen_x, 0)
        draw_end_x = min(sprite_width // 2 + sprite_screen_x, SCREEN_WIDTH - 1)

        if draw_start_x >= draw_end_x or draw_start_y >= draw_end_y:
            continue

        scaled_sprite = pygame.transform.smoothscale(sprite, (sprite_width, sprite_height))
        sprite_left = -sprite_width // 2 + sprite_screen_x
        for stripe in range(draw_start_x, draw_end_x):
            tex_x = stripe - sprite_left
            if (
                0 <= stripe < SCREEN_WIDTH
                and 0 <= tex_x < sprite_width
                and depth_buffer[stripe] > transform_y
            ):
                source_rect = pygame.Rect(tex_x, 0, 1, sprite_height)
                screen.blit(scaled_sprite, (stripe, draw_start_y), source_rect)


def draw_danger_overlay(screen: pygame.Surface, distance: float) -> None:
    max_distance = 6.0
    if distance >= max_distance:
        return
    intensity = (max_distance - distance) / max_distance
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((120, 0, 0, int(160 * intensity)))
    screen.blit(overlay, (0, 0))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Labyrinth Raycaster")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Menlo", 16)
    monster_frames = load_monster_frames()
    pellet_sprite = load_pellet_sprite()

    def reset_state() -> tuple[Player, list[Monster], list[Pellet], int, int, bool, bool]:
        player_obj = spawn_player()
        monster_list = spawn_monsters()
        pellet_list = spawn_pellets()
        total = len(pellet_list)
        collected = 0
        win_target = max(1, math.ceil(total / 2))
        return player_obj, monster_list, pellet_list, collected, win_target, True, False

    player, monsters, pellets, collected_count, win_target, alive, won = reset_state()
    total_pellets = len(pellets)

    running = True
    while running:
        delta_time = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if alive and not won:
            move_speed = 3.0 * delta_time
            rot_speed = 1.8 * delta_time

            if keys[pygame.K_w]:
                move_player(player, player.dir_x * move_speed, player.dir_y * move_speed)
            if keys[pygame.K_s]:
                move_player(player, -player.dir_x * move_speed, -player.dir_y * move_speed)
            if keys[pygame.K_q]:
                move_player(player, -player.plane_x * move_speed, -player.plane_y * move_speed)
            if keys[pygame.K_e]:
                move_player(player, player.plane_x * move_speed, player.plane_y * move_speed)
            if keys[pygame.K_a]:
                rotate_player(player, rot_speed)
            if keys[pygame.K_d]:
                rotate_player(player, -rot_speed)

            update_monsters(monsters, player, delta_time)
            if player_is_dead(player, monsters):
                alive = False
            collected_count += collect_pellets(player, pellets)
            if collected_count >= win_target:
                won = True
        else:
            if keys[pygame.K_r]:
                player, monsters, pellets, collected_count, win_target, alive, won = reset_state()
                total_pellets = len(pellets)

        danger_distance = nearest_monster_distance(player, monsters)

        screen.fill(CEILING_COLOR)
        pygame.draw.rect(screen, FLOOR_COLOR, pygame.Rect(0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

        depth_buffer = cast_rays(screen, player)
        draw_collectibles(screen, player, pellets, depth_buffer, pellet_sprite)
        draw_monsters(screen, player, monsters, depth_buffer, monster_frames)
        draw_minimap(screen, player, monsters, pellets)
        if alive and not won:
            draw_danger_overlay(screen, danger_distance)

        info_lines = [
            "W/S: forward/back",
            "Q/E: strafe",
            "A/D: rotate",
            "R: respawn",
            f"Spheres: {collected_count}/{total_pellets} (need {win_target})",
            f"FPS: {clock.get_fps():5.1f}",
        ]
        for idx, text in enumerate(info_lines):
            surf = font.render(text, True, (230, 230, 230))
            screen.blit(surf, (SCREEN_WIDTH - 200, 10 + idx * 18))

        if danger_distance < 4.5 and alive and not won:
            flicker = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
            warn_color = (255, int(80 + 150 * flicker), int(80 + 60 * (1 - flicker)))
            warning = font.render("IT'S HUNTING YOU", True, warn_color)
            screen.blit(warning, (20, SCREEN_HEIGHT - 40))

        if not alive:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            death_text = font.render("The beast got you! Press R to respawn.", True, (255, 200, 200))
            screen.blit(death_text, (SCREEN_WIDTH // 2 - death_text.get_width() // 2, SCREEN_HEIGHT // 2))
        elif won:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 30, 0, 160))
            screen.blit(overlay, (0, 0))
            win_text = font.render("Victory! Half the spheres collected. Press R to restart.", True, (200, 255, 200))
            screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
