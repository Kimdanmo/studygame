import pygame
import random
import time
import json
import os

pygame.init()

pygame.mixer.init()
# 배경음악 파일 경로
bgm_normal = "sounds/bgm_normal.mp3"
bgm_fast = "sounds/bgm_fast.mp3"

# 처음에 일반 배경음악 재생
pygame.mixer.music.load(bgm_normal)
pygame.mixer.music.set_volume(0.4)        # 볼륨 (0.0 ~ 1.0)

correct_sound = pygame.mixer.Sound("sounds/correct.mp3")
wrong_sound = pygame.mixer.Sound("sounds/wrong.mp3")

correct_sound.set_volume(0.5)  # 볼륨 조절 (0.0~1.0)
wrong_sound.set_volume(0.5)

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# 성공 애니메이션 프레임 로드
success_frames = []
for i in range(21):  # frame_00.gif ~ frame_20.gif 총 21개
    filename = f"images/success/frame_{i:02d}.gif"
    img = pygame.image.load(filename).convert_alpha()
    success_frames.append(img)

# 실패 애니메이션 프레임 로드 (fail도 동일하게 분해했다 가정)
fail_frames = []
for i in range(8):
    filename = f"images/fail/frame_{i:02d}.gif"
    img = pygame.image.load(filename).convert_alpha()
    fail_frames.append(img)
    
# 플레이어 애니메이션 프레임 불러오기 (좌우반전 포함)
player_frames = []
for i in range(4):  # 프레임 수에 따라 조절
    img = pygame.image.load(f"images/player/frame_{i:02d}.gif").convert_alpha()
    flipped_img = pygame.transform.flip(img, True, False)  # ← 좌우반전!
    scaled_img = pygame.transform.scale(flipped_img, (120, 100))
    player_frames.append(scaled_img)

player_frame_index = 0
player_frame_timer = 0
frame_duration = 0.12  # 프레임 간격 (초)

# 애니메이션 상태 변수 초기화
success_anim_index = 0
success_anim_timer = 0
fail_anim_index = 0
fail_anim_timer = 0

success_anim_speed = 0.05  # 초 단위, 프레임 당 재생 시간
fail_anim_speed = 0.05

success_anim_playing = False
fail_anim_playing = False

pygame.display.set_caption("달려라 고딩!")

font_path = "fonts/Maplestory Bold.ttf"
font = pygame.font.Font(font_path, 48)
small_font = pygame.font.Font(font_path, 36)
big_font = pygame.font.Font(font_path, 120)

subject_display = {
    "물리학": "physics",
    "수학 I": "math1",
    "수학 II": "math2",
    "화학": "chemistry"
}

heart_full_img = pygame.image.load("images/heart_full.png").convert_alpha()
heart_empty_img = pygame.image.load("images/heart_empty.png").convert_alpha()
heart_size = (40, 40)
heart_full_img = pygame.transform.scale(heart_full_img, heart_size)
heart_empty_img = pygame.transform.scale(heart_empty_img, heart_size)

sutuk_images = {
    "physics": pygame.transform.scale(pygame.image.load("images/sutuk_physics.jpg").convert_alpha(), (80, 100)),
    "math1": pygame.transform.scale(pygame.image.load("images/sutuk_math1.jpg").convert_alpha(), (80, 100)),
    "math2": pygame.transform.scale(pygame.image.load("images/sutuk_math2.jpg").convert_alpha(), (80, 100)),
    "chemistry": pygame.transform.scale(pygame.image.load("images/sutuk_chemistry.jpg").convert_alpha(), (80, 100))
}

title_image = pygame.image.load("images/title_screen.png")
title_image = pygame.transform.scale(title_image, (WIDTH, HEIGHT))

WHITE = (255, 255, 255)
GRAY = (230, 230, 230)
BLACK = (0, 0, 0)
DARK_GRAY = (180, 180, 180)

subject_options = list(subject_display.keys())
selected_subject = subject_options[0]
dropdown_open = False
dropdown_x = WIDTH // 2 - 100
dropdown_y = HEIGHT // 2 - 50
dropdown_width = 200
dropdown_height = 70

start_button_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT // 2 + 300, 250, 90)
retry_button_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT // 2 + 150, 250, 90)

clock = pygame.time.Clock()
running = True
game_started = False
game_over = False

player_lane = 1
lane_y_positions = [HEIGHT // 2 - 100, HEIGHT // 2, HEIGHT // 2 + 100]
player_x = 300
player_y = lane_y_positions[player_lane]
move_speed = 800

obstacle_color = (200, 50, 50)
answer_color = (50, 150, 50)
background_speed = 400

obstacles = []
last_obstacle_time = 0
obstacle_interval = random.uniform(0.7, 1.6)

max_hp = 5
hp = max_hp

problems = []
used_problems = []
current_problem = None
problem_start_time = 0
show_problem = False
show_answer = False
answer_display_start = 0
answer_result = None
answer_start_x = WIDTH + 100
answer_speed = background_speed

collision_cooldown = 1.0
last_collision_time = 0
correct_count = 0

correct_streak = 0  # 연속 정답 횟수
heart_items = []  # 떨어지는 하트 아이템들

speed_multiplier = 1.0

def draw_text_center(text, font, color, x, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)

def draw_wrapped_text(text, font, color, x, y, max_width, line_spacing=10):
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)

    for i, line in enumerate(lines):
        rendered = font.render(line.strip(), True, color)
        screen.blit(rendered, (x, y + i * (font.get_height() + line_spacing)))

loaded_question_images = {}

def get_question_image(path):
    if not path:
        return None
    if path not in loaded_question_images:
        if os.path.exists(path):
            loaded_question_images[path] = pygame.image.load(path).convert_alpha()
        else:
            loaded_question_images[path] = None
    return loaded_question_images[path]


def load_questions(filename, subject):
    if not os.path.exists(filename):
        print(f"파일이 없습니다: {filename}")
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [
        {
            "q": item.get("question"),
            "options": item.get("options"),
            "a": item.get("options")[item.get("answer")],
            "image_path": item.get("image")
        }
        for item in data if item.get("subject") == subject
    ]

def reset_problem():
    global current_problem, used_problems, problem_start_time
    global show_problem, show_answer, answer_display_start, answer_result, answer_start_x
    available = [p for p in problems if p not in used_problems]
    if not available:
        return False
    current_problem = random.choice(available)
    used_problems.append(current_problem)
    problem_start_time = time.time()
    show_problem = True
    show_answer = False
    answer_display_start = 0
    answer_result = None
    answer_start_x = WIDTH + 100
    return True

def reset_game():
    global hp, used_problems, obstacles, player_lane, last_obstacle_time, obstacle_interval
    global game_started, game_over, correct_count, correct_streak
    global success_anim_playing, fail_anim_playing
    
    hp = max_hp
    used_problems = []
    obstacles.clear()
    player_lane = 1
    last_obstacle_time = time.time()
    obstacle_interval = random.uniform(1, 2)
    game_started = True
    game_over = False
    correct_count = 0
    correct_streak = 0
    heart_items.clear()
    success_anim_playing = False
    fail_anim_playing = False
    pygame.mixer.music.play(-1)  # -1은 무한 반복
    
    reset_problem()
    
prev_speed_state = None  # 이전 상태 저장용

while running:
    dt = clock.tick(60) / 1000
    screen.fill(WHITE)
    
    # 플레이어 애니메이션 프레임 전환
    player_frame_timer += dt
    if player_frame_timer >= frame_duration:
        player_frame_index = (player_frame_index + 1) % len(player_frames)
        player_frame_timer = 0
    
    # 성공 애니메이션 재생 처리
    if success_anim_playing:
        success_anim_timer += dt
        if success_anim_timer >= success_anim_speed:
            success_anim_timer = 0
            success_anim_index += 1
            if success_anim_index >= len(success_frames):
                success_anim_index = 0
                success_anim_playing = False  # 애니메이션 종료

    # 실패 애니메이션 재생 처리
    if fail_anim_playing:
        fail_anim_timer += dt
        if fail_anim_timer >= fail_anim_speed:
            fail_anim_timer = 0
            fail_anim_index += 1
            if fail_anim_index >= len(fail_frames):
                fail_anim_index = 0
                fail_anim_playing = False  # 애니메이션 종료


    if game_started:
        speed_multiplier = 1.8 if hp <= 2 else 1.0
        
    # 배경음악 전환 체크
    if speed_multiplier == 1.8 and prev_speed_state != 'fast':
        pygame.mixer.music.load(bgm_fast)
        pygame.mixer.music.play(-1)
        prev_speed_state = 'fast'
    elif speed_multiplier == 1.0 and prev_speed_state != 'normal':
        pygame.mixer.music.load(bgm_normal)
        pygame.mixer.music.play(-1)
        prev_speed_state = 'normal'

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if not game_started and not game_over:
                dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
                if dropdown_rect.collidepoint(mouse_pos):
                    dropdown_open = not dropdown_open
                else:
                    if dropdown_open:
                        for i, option in enumerate(subject_options):
                            option_rect = pygame.Rect(dropdown_x, dropdown_y + (i + 1)*dropdown_height, dropdown_width, dropdown_height)
                            if option_rect.collidepoint(mouse_pos):
                                selected_subject = option
                                dropdown_open = False
                                break
                if start_button_rect.collidepoint(mouse_pos):
                    internal_subject = subject_display[selected_subject]
                    filename_map = {
                        "physics": "physics_questions.json",
                        "math1": "math1_questions.json",
                        "math2": "math2_questions.json",
                        "chemistry": "chemistry_questions.json"
                    }
                    problems = load_questions(filename_map[internal_subject], internal_subject)
                    if problems:
                        reset_game()
            elif game_over and retry_button_rect.collidepoint(mouse_pos):
                game_over = False
                game_started = False

        elif event.type == pygame.KEYDOWN and game_started:
            if event.key == pygame.K_UP and player_lane > 0:
                player_lane -= 1
            elif event.key == pygame.K_DOWN and player_lane < 2:
                player_lane += 1

    if not game_started and not game_over:
        screen.blit(title_image, (0, 0))
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
        pygame.draw.rect(screen, GRAY, dropdown_rect)
        pygame.draw.rect(screen, BLACK, dropdown_rect, 2)
        screen.blit(font.render(selected_subject + " ▼", True, BLACK), (dropdown_x + 10, dropdown_y + 15))
        if dropdown_open:
            for i, option in enumerate(subject_options):
                option_rect = pygame.Rect(dropdown_x, dropdown_y + (i + 1)*dropdown_height, dropdown_width, dropdown_height)
                pygame.draw.rect(screen, WHITE, option_rect)
                pygame.draw.rect(screen, BLACK, option_rect, 1)
                screen.blit(font.render(option, True, BLACK), (option_rect.x + 10, option_rect.y + 15))
        pygame.draw.rect(screen, DARK_GRAY, start_button_rect)
        pygame.draw.rect(screen, BLACK, start_button_rect, 2)
        draw_text_center("게임 시작", font, BLACK, start_button_rect.centerx, start_button_rect.centery)

    elif game_over:
        draw_text_center("Game Over!", big_font, (200, 0, 0), WIDTH // 2, HEIGHT // 2 - 150)
        draw_text_center(f"선택 과목: {selected_subject}", font, BLACK, WIDTH // 2, HEIGHT // 2 - 40)
        draw_text_center(f"맞춘 문제 수: {correct_count}", font, BLACK, WIDTH // 2, HEIGHT // 2 + 20)
        pygame.draw.rect(screen, DARK_GRAY, retry_button_rect)
        pygame.draw.rect(screen, BLACK, retry_button_rect, 2)
        draw_text_center("한 번 더", font, BLACK, retry_button_rect.centerx, retry_button_rect.centery)

    else:
        current_time = time.time()

        if current_time - last_obstacle_time > obstacle_interval:
            lane = random.randint(0, 2)
            obstacles.append({
                "lane": lane,
                "x": WIDTH + 50,
                "image": sutuk_images[subject_display[selected_subject]]
            })
            last_obstacle_time = current_time
            obstacle_interval = random.uniform(1, 2) / speed_multiplier

        current_speed = background_speed * speed_multiplier

        for obs in obstacles[:]:
            obs["x"] -= current_speed * dt
            img = obs["image"]
            obs_rect = pygame.Rect(obs["x"], lane_y_positions[obs["lane"]], img.get_width(), img.get_height())
            screen.blit(img, (obs["x"], lane_y_positions[obs["lane"]]))

            if obs_rect.colliderect(player_frames[player_frame_index].get_rect(topleft=(player_x, lane_y_positions[player_lane]))):
                if current_time - last_collision_time > collision_cooldown:
                    hp -= 1
                    last_collision_time = current_time
                    obstacles.remove(obs)
                    if hp <= 0:
                        game_over = True
                        pygame.mixer.music.stop()
                        game_started = False
                        
        # 하트 아이템 이동 및 충돌 처리
        for item in heart_items[:]:
            item["x"] -= current_speed * dt
            heart_rect = pygame.Rect(item["x"], item["y"], heart_size[0], heart_size[1])
            screen.blit(heart_full_img, (item["x"], item["y"]))

            if heart_rect.colliderect(player_rect):
                if hp < max_hp:
                    hp += 1
                heart_items.remove(item)

        target_y = lane_y_positions[player_lane]
        if abs(player_y - target_y) > 1:
            direction = 1 if target_y > player_y else -1
            player_y += direction * move_speed * dt
            if (direction == 1 and player_y > target_y) or (direction == -1 and player_y < target_y):
                player_y = target_y
        else:
            player_y = target_y

        current_player_img = player_frames[player_frame_index]
        player_rect = current_player_img.get_rect(topleft=(player_x, player_y))
        screen.blit(current_player_img, player_rect)
        
        # 애니메이션이 재생 중이면 화면 가운데에 애니메이션 그리기
        if success_anim_playing:
            frame = success_frames[success_anim_index]
            frame_rect = frame.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(frame, frame_rect)

        if fail_anim_playing:
            frame = fail_frames[fail_anim_index]
            frame_rect = frame.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(frame, frame_rect)

        elapsed = current_time - problem_start_time
        if show_problem:
            draw_wrapped_text(current_problem["q"], font, BLACK, WIDTH // 2 - 600, 190, 1200)
            
            question_img = get_question_image(current_problem.get("image_path"))
            if question_img:
                img_scaled = pygame.transform.scale(question_img, (400, 300))  # 크기 조절 (필요하면)
                screen.blit(img_scaled, (WIDTH // 2 + 300, 150))  # 위치는 상황에 맞게 조절
            
            if elapsed >= 10:
                show_answer = True
            if elapsed >= 20:
                answer_result = "오답!"
                hp -= 1
                show_problem = False
                show_answer = False
                answer_display_start = current_time
                if hp <= 0:
                    game_over = True
                    pygame.mixer.music.stop()
                    game_started = False

        if show_answer:
            answer_start_x -= answer_speed * speed_multiplier * dt
            for i, option in enumerate(current_problem["options"]):
                answer_rect = pygame.Rect(answer_start_x, lane_y_positions[i], 120, 100)
                pygame.draw.rect(screen, answer_color, answer_rect)
                screen.blit(small_font.render(option, True, BLACK), answer_rect.move(10, 30))
                if player_rect.colliderect(answer_rect):
                    if option == current_problem["a"]:
                        correct_count += 1
                        correct_streak += 1
                        answer_result = f"정답! ({correct_streak}연속)"
                        correct_sound.play()  # 효과음 재생!

                        if correct_streak >= 3 and correct_streak % 3 == 0:
                            # 하트 아이템 생성
                            heart_items.append({
                                "lane": player_lane,  # 현재 lane에 생성
                                "x": WIDTH + 100,
                                "y": lane_y_positions[player_lane],
                            })
                            correct_streak = 0
                        
                        # 성공 애니메이션 시작
                        success_anim_playing = True
                        success_anim_index = 0
                        success_anim_timer = 0
                        
                    else:
                        answer_result = "오답!"
                        hp -= 1
                        correct_streak = 0  # 틀리면 연속 정답 초기화
                        wrong_sound.play()  # 효과음 재생!
                        
                        # 실패 애니메이션 시작
                        fail_anim_playing = True
                        fail_anim_index = 0
                        fail_anim_timer = 0
                        
                        if hp <= 0:
                            game_over = True
                            pygame.mixer.music.stop()
                            game_started = False
                    show_answer = False
                    show_problem = False
                    answer_display_start = current_time
                    break

        if answer_result:
            color =(57, 255, 20) if answer_result == "정답!" else (200, 0, 0)
            draw_text_center(answer_result, font, color, WIDTH // 2, HEIGHT // 2)
            if current_time - answer_display_start > 3:
                answer_result = None
                if not game_over and not reset_problem():
                    game_over = True
                    pygame.mixer.music.stop()
                    game_started = False

        for i in range(max_hp):
            screen.blit(
                heart_full_img if i < hp else heart_empty_img,
                (200 + i * (heart_size[0] + 10), 130)
            )

    pygame.display.update()

pygame.quit()
