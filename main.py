import pygame
import sys
import os
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from system.player import Player
from system.client import Client
from system.console import Chat
pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("DomE")
ico = pygame.image.load('assets/logo_dome.ico')
PRESETS_FILE = "json/presets.json"
DEFAULT_DIR = os.path.expanduser("~")
pygame.display.set_icon(ico)
font = pygame.font.Font(None, 50)
font1 = pygame.font.Font(None, 30)
clock = pygame.time.Clock()
GRAVITY = 0.7
spawn_points = {
    "Вход в подземки": [(1, 1), (735, 749)],
    "Гора": [(3, 0), (1124, 807)],
}

def get_player_rect(size_state):
    """Возвращает pygame.Rect в зависимости от size_state"""
    if size_state == 1:
        return 45, 15
    elif size_state == 2:
        return 15, 45
    else:
        return 30, 30

def load_json(filename, default):
    """Возвращает данные или default, создает файл если нужно"""
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        data = default.copy()
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"📝 Создан {filename}")
        return data

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"🔧 Исправлен поврежденный {filename}")
        data = default.copy()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return data

def draw_nick(screen, font, nick, rect, color=(255, 255, 255), bg_color=None, padding=5):
    """Рисует ник над квадратом"""
    text_surface = font.render(nick, True, color)
    text_rect = text_surface.get_rect()

    text_rect.centerx = rect.centerx

    text_rect.bottom = rect.top - padding

    if bg_color:
        bg_rect = pygame.Rect(
            text_rect.x - 2,
            text_rect.y - 2,
            text_rect.width + 4,
            text_rect.height + 4
        )
        pygame.draw.rect(screen, bg_color, bg_rect)

    screen.blit(text_surface, text_rect)

def load_presets() -> dict:
    """Возвращает словарь {имя: [путь1, путь2, путь3, путь4]}"""
    if not os.path.exists(PRESETS_FILE):
        return {}
    with open(PRESETS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

            if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
                return data
        except Exception:
            pass
    return {}

def save_presets(presets: dict):
    """Сохраняет словарь пресетов в JSON‑файл."""
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)

def select_image(entry: tk.Entry):
    filepath = filedialog.askopenfilename(
        title="Выберите изображение",
        initialdir=DEFAULT_DIR,
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
    )
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)
        return filepath
    return None

def populate_preset_combo(combo: ttk.Combobox, presets: dict):
    combo['values'] = sorted(presets.keys())
    if presets:
        combo.current(0)

def start_room(event=None):
    global room_id, coords

    selected = room_combo.get()
    if not selected:
        room_id = [1, 1]
        coords = [735, 749]

    room_id = list(spawn_points[selected][0])
    coords = list(spawn_points[selected][1])

def on_select_preset(event=None):
    name1 = preset_combo.get()
    paths = presets.get(name1, [])
    if len(paths) >= 4:
        entry_image_path1.delete(0, tk.END)
        entry_image_path1.insert(0, paths[0])
        entry_image_path2.delete(0, tk.END)
        entry_image_path2.insert(0, paths[1])
        entry_host.delete(0, tk.END)
        entry_host.insert(0, paths[2])
        entry_port.delete(0, tk.END)
        entry_port.insert(0, paths[3])

def on_save_preset():
    name1 = preset_name_var.get().strip()
    if not name1:
        messagebox.showerror("Ошибка", "Введите имя пресета.")
        return

    p1 = entry_image_path1.get().strip()
    p2 = entry_image_path2.get().strip()
    host1 = entry_host.get().strip()
    port1 = entry_port.get().strip()

    if not (p1 and p2):
        messagebox.showerror("Ошибка", "Оба поля изображения должны быть заполнены.")
        return

    if not (host1 and port1):
        messagebox.showerror("Ошибка", "Должен быть заполнен и хост и порт.")
        return

    presets[name1] = [p1, p2, host1, port1]
    save_presets(presets)
    populate_preset_combo(preset_combo, presets)
    preset_name_var.set("")
    messagebox.showinfo("Успех", f"Пресет «{name1}» сохранён.")

def on_start():
    global image_path1, image_path2
    image_path1 = entry_image_path1.get()
    image_path2 = entry_image_path2.get()
    root.destroy()
    main()

def load_level(image_path):
    img = pygame.image.load(image_path).convert_alpha()
    level_mask = pygame.mask.from_surface(img)
    return level_mask

def main():
    global client, output, multiplayer, chat
    player1 = Player(coords, image_path1)
    player2 = Player(coords, image_path2,
        A=pygame.K_KP4,
        D=pygame.K_KP6,
        W=pygame.K_KP8,
        S=pygame.K_KP5,
        E=pygame.K_KP9,
        SHIFT=pygame.K_UP,
        CTRL=pygame.K_LEFT,
        SPACE=pygame.K_KP_ENTER)
    room_x, room_y = room_id
    room = f'room_{room_x}{room_y}'
    level_mask = load_level(f'assets/hb/{room}.png')
    level_img = pygame.image.load(f'assets/bg/{room}_bg.png').convert_alpha()
    text = font.render("E - продолжить. TAB - выход.", True, (255, 255, 255))

    st = {
    "": {
        "x": 0,
        "y": 0,
        "room": 00,
        "pl": 0
         }
    }

    if multiplayer:
        with open('json/input_info.json', 'w', encoding='utf-8') as f:
            json.dump(st, f, indent=4, ensure_ascii=False)
        client = Client(host, int(port))
        chat = Chat(player1, screen, name)
        try:
            client.connect()
        except ConnectionRefusedError:
            multiplayer = False

    running = True
    stop = False
    abs_run = True
    while abs_run:

        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    stop = False
                    abs_run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        player1.xy()
                        player2.xy()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                running = False
                stop = True

            a = True
            room_x, room_y, new_room = player1.new_room(room_x, room_y)
            if new_room != room:
                a = False
                try:
                    room = new_room
                    level_mask = load_level(f'assets/hb/{new_room}.png')
                    level_img = pygame.image.load(f'assets/bg/{new_room}_bg.png').convert_alpha()
                    player2.rect.topleft = player1.rect.topleft
                except FileNotFoundError:
                    running = False
                    stop = True

            if a:
                room_x, room_y, new_room = player2.new_room(room_x, room_y)
                if new_room != room:
                    try:
                        room = new_room
                        level_mask = load_level(f'assets/hb/{new_room}.png')
                        level_img = pygame.image.load(f'assets/bg/{new_room}_bg.png').convert_alpha()
                        player2.rect.topleft = player1.rect.topleft
                    except FileNotFoundError:
                        running = False
                        stop = True

            player1.update(level_mask, level_img)
            player2.update(level_mask, level_img)

            screen.fill((100, 100, 100))
            screen.blit(level_img, (0, 0))

            if multiplayer:
                output = {
                    f"{name}": {
                        "x": player1.rect.x,
                        "y": player1.rect.y,
                        "room": int(f"{room_x}{room_y}"),
                        "pl" : player1.size_state,
                        "txt" : chat.chat[name]
                    }
                }
                with open('json/output_info.json', 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)

                c = client.send_to_server('json/output_info.json')
                if c:
                    running = False
                    stop = True
                input = load_json('json/input_info.json', {"nicks": {}})

                for nick in input.keys():
                    try:
                        chat.print_in_chat(input[nick]["txt"])
                        if input[nick]["room"] == output[name]["room"]:
                            crd = get_player_rect(input[nick]["pl"])
                            player2.new_pl_size(crd)
                            rect2 = pygame.Rect(input[nick]["x"],
                                                input[nick]["y"],
                                                player2.rect.width,
                                                player2.rect.height)
                            screen.blit(player2.image, rect2)
                            draw_nick(screen, font1, nick, rect2)
                        else:
                            screen.blit(player1.image, player1.rect)
                    except KeyError:
                        pass

                draw_nick(screen, font1, name, player1.rect)
            else:
                screen.blit(player2.image, player2.rect)

            screen.blit(player1.image, player1.rect)

            pygame.display.flip()

        while stop:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    stop = False
                    abs_run = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        player1.xy()
                        player2.xy()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_TAB]:
                running = False
                stop = False
                abs_run = False
            elif keys[pygame.K_e]:
                running = True
                stop = False


            screen.fill((60, 60, 60))
            screen.blit(level_img, (0, 0))
            if multiplayer:
                input = load_json('json/input_info.json', {"nicks": {}})

                for nick in input.keys():
                    try:
                        if input[nick]["room"] == output[name]["room"]:
                            rect2 = pygame.Rect(input[nick]["x"], input[nick]["y"], 30, 30)
                            screen.blit(player2.image, (input[nick]["x"], input[nick]["y"]))
                            draw_nick(screen, font1, nick, rect2)
                        else:
                            screen.blit(player1.image, player1.rect)
                    except KeyError:
                        pass

                draw_nick(screen, font1, name, player1.rect)
            else:
                screen.blit(player2.image, player2.rect)

            screen.blit(player1.image, player1.rect)

            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT - 100))
            pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    image_path1 = None
    image_path2 = None

    root = tk.Tk()
    root.title("Запуск DomE 0.1")
    root.geometry("650x400")

    serv = tk.BooleanVar(value=False)

    btn_browse1 = tk.Button(root, text="Выбор скина для игрока 1",
                            command=lambda: select_image(entry_image_path1))
    btn_browse1.grid(row=0, column=0, padx=0, pady=10)

    entry_image_path1 = tk.Entry(root, width=60)
    entry_image_path1.grid(row=5, column=0, padx=0, pady=10)

    btn_browse2 = tk.Button(root, text="Выбор скина для игрока 2",
                            command=lambda: select_image(entry_image_path2))
    btn_browse2.grid(row=10, column=0, padx=0, pady=10)

    entry_image_path2 = tk.Entry(root, width=60)
    entry_image_path2.grid(row=15, column=0, padx=0, pady=10)

    presets = load_presets()

    preset_frame = ttk.LabelFrame(root, text="Пресеты")
    preset_frame.grid(row=20, column=0, padx=10, pady=10)

    preset_combo = ttk.Combobox(preset_frame, state="readonly")
    populate_preset_combo(preset_combo, presets)
    preset_combo.bind("<<ComboboxSelected>>", on_select_preset)
    preset_combo.grid(row=20, column=0, padx=5, pady=5, sticky="ew")

    preset_name_var = tk.StringVar()
    entry_new_preset = ttk.Entry(preset_frame, textvariable=preset_name_var, width=20)
    entry_new_preset.grid(row=20, column=1, padx=5, pady=5)

    room_label = ttk.Label(root, text="Выберите стартовую комнату:", font=("Arial", 10))
    room_label.grid(row=30, column=0, padx=10, pady=10, sticky='w')

    room_combo = ttk.Combobox(
        root,
        state="readonly",
        values=list(spawn_points.keys())
    )
    room_combo.bind("<<ComboboxSelected>>", start_room)
    room_combo.grid(row=30, column=0, padx=90, pady=10, sticky='e')

    btn_save_preset = ttk.Button(preset_frame, text="Сохранить пресет", command=on_save_preset)
    btn_save_preset.grid(row=20, column=2, padx=5, pady=5)

    checkbox = tk.Checkbutton(
        root,
        text="Сетевая игра",
        variable=serv,
        font=("Arial", 12)
    )
    checkbox.grid(row=0, column=1, padx=10, pady=10)

    label_host = tk.Label(root, text="Хост (по умолчанию localhost)", font=("Arial", 12))
    label_host.grid(row=5, column=1, padx=0, pady=0, sticky='w')

    entry_host = tk.Entry(root, width=23, font=("Arial", 12))
    entry_host.grid(row=10, column=1, padx=0, pady=0, sticky='w')

    label_port = tk.Label(root, text="Порт (по умолчанию 12345)", font=("Arial", 12))
    label_port.grid(row=15, column=1, padx=0, pady=0, sticky='w')

    entry_port = tk.Entry(root, width=23, font=("Arial", 12))
    entry_port.grid(row=20, column=1, padx=0, pady=0, sticky='w')

    label_name = tk.Label(root, text="Имя (обязательно)", font=("Arial", 12))
    label_name.grid(row=25, column=1, padx=0, pady=0, sticky='w')

    entry_name = tk.Entry(root, width=23, font=("Arial", 12))
    entry_name.grid(row=30, column=1, padx=0, pady=0, sticky='w')

    btn_start = tk.Button(root, text="Запуск", width=20, height=1, font=("Arial", 20), command=lambda: on_start())
    btn_start.grid(row=50, column=0, padx=10, pady=10)

    def on_start():
        global image_path1, image_path2, host, port, multiplayer, name
        image_path1 = entry_image_path1.get().strip()
        image_path2 = entry_image_path2.get().strip()
        host = entry_host.get()
        port = entry_port.get()
        multiplayer = serv.get()
        name = entry_name.get()
        room = room_combo.get()

        if not (image_path1 and image_path2):
            messagebox.showerror("Ошибка", "Выберите изображения для обоих игроков.")
            return

        if not room:
            messagebox.showerror("Ошибка", "Выберите стартовую локацию.")
            return

        if not name and multiplayer:
            messagebox.showerror("Ошибка", "Введите имя.")
            return

        root.destroy()
        main()

    root.mainloop()