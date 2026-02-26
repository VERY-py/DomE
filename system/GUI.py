import pygame
import pygame_gui
import os
import json
from pygame_gui.elements import UIButton, UITextEntryLine, UICheckBox
from pygame_gui.windows import UIFileDialog
from pygame_gui.elements import UILabel
from pygame_gui.elements.ui_panel import UIPanel
from pathlib import Path
pygame.init()

class PresetWindow:
    def __init__(self, manager, gui):
        self.manager = manager
        self.gui = gui
        self.window = None
        self.preset_buttons = []
        self.current_page = 0
        self.items_per_page = 8
        self.filtered_presets = []
        self.search_entry = None
        self.save_entry = None
        self.load_btn = None
        self.save_btn = None

    def show(self):
        if self.window:
            self.window.kill()

        self.window = UIPanel(
            relative_rect=pygame.Rect(100, 50, 500, 450),
            manager=self.manager
        )

        title = UILabel(
            pygame.Rect(10, 10, 480, 30),
            "Пресеты",
            container=self.window,
            manager=self.manager,
            object_id='#preset_title'
        )

        self.search_entry = UITextEntryLine(
            pygame.Rect(10, 50, 200, 30),
            container=self.window,
            manager=self.manager,
            placeholder_text="Поиск пресетов..."
        )

        self.load_btn = UIButton(
            pygame.Rect(220, 50, 100, 30),
            "Загрузить",
            container=self.window,
            manager=self.manager
        )
        self.save_btn = UIButton(
            pygame.Rect(330, 50, 100, 30),
            "Сохранить",
            container=self.window,
            manager=self.manager
        )

        self.save_entry = UITextEntryLine(
            pygame.Rect(440, 50, 40, 30),
            container=self.window,
            manager=self.manager,
            placeholder_text="Имя"
        )

        self.list_panel = UIPanel(
            pygame.Rect(10, 90, 480, 300),
            container=self.window,
            manager=self.manager
        )

        close_btn = UIButton(
            pygame.Rect(450, 10, 30, 30),
            "X",
            container=self.window,
            manager=self.manager
        )
        close_btn.is_close = True

        self.update_preset_list()

    def update_preset_list(self):
        if not self.window or not hasattr(self, 'list_panel'):
            return

        for btn in self.preset_buttons:
            btn.kill()
        self.preset_buttons = []

        search_term = self.search_entry.get_text().lower().strip() if self.search_entry else ""
        if search_term:
            self.filtered_presets = [
                name for name in self.gui.presets
                if search_term in name.lower()
            ]
        else:
            self.filtered_presets = list(self.gui.presets.keys())

        self.current_page = 0
        self.refresh_preset_page()

    def refresh_preset_page(self):
        if not hasattr(self, 'list_panel'):
            return

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_presets = self.filtered_presets[start_idx:end_idx]

        for i, preset_name in enumerate(page_presets):
            y_pos = 10 + i * 30
            if y_pos + 25 > 290:
                break

            btn = UIButton(
                pygame.Rect(10, y_pos, 350, 25),
                preset_name[:30] + "..." if len(preset_name) > 30 else preset_name,
                container=self.list_panel,
                manager=self.manager
            )
            btn.preset_name = preset_name
            self.preset_buttons.append(btn)

        total_pages = (len(self.filtered_presets) + self.items_per_page - 1) // self.items_per_page
        if total_pages > 1:
            y_pos = 280
            if self.current_page > 0:
                prev_btn = UIButton(
                    pygame.Rect(10, y_pos, 40, 25),
                    "<",
                    container=self.list_panel,
                    manager=self.manager
                )
                prev_btn.is_pagination = True
                prev_btn.direction = "prev"

            page_label = UILabel(
                pygame.Rect(60, y_pos + 3, 80, 20),
                f"{self.current_page + 1}/{total_pages}",
                container=self.list_panel,
                manager=self.manager
            )

            if self.current_page < total_pages - 1:
                next_btn = UIButton(
                    pygame.Rect(150, y_pos, 40, 25),
                    ">",
                    container=self.list_panel,
                    manager=self.manager
                )
                next_btn.is_pagination = True
                next_btn.direction = "next"

    def process_preset_events(self, event):
        if not self.window:
            return False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if hasattr(event.ui_element, 'is_close') and event.ui_element.is_close:
                self.window.kill()
                self.window = None
                return True

            if hasattr(event.ui_element, 'preset_name'):
                preset_data = self.gui.presets[event.ui_element.preset_name]
                self.gui.entry_path1.set_text(preset_data.get("player1_img", ""))
                self.gui.entry_path2.set_text(preset_data.get("player2_img", ""))
                self.gui.entry_host.set_text(preset_data.get("host", "localhost"))
                self.gui.entry_port.set_text(preset_data.get("port", "12345"))
                self.gui.entry_name.set_text(preset_data.get("name", ""))
                return True

            if self.load_btn and event.ui_element == self.load_btn:
                selected_preset = self.filtered_presets[self.current_page * self.items_per_page] if self.filtered_presets else None
                if selected_preset and selected_preset in self.gui.presets:
                    preset_data = self.gui.presets[selected_preset]
                    self.gui.entry_path1.set_text(preset_data.get("player1_img", ""))
                    self.gui.entry_path2.set_text(preset_data.get("player2_img", ""))
                    self.gui.entry_host.set_text(preset_data.get("host", "localhost"))
                    self.gui.entry_port.set_text(preset_data.get("port", "12345"))
                    self.gui.entry_name.set_text(preset_data.get("name", ""))
                return True

            if self.save_btn and event.ui_element == self.save_btn:
                preset_name = self.save_entry.get_text().strip()
                if not preset_name:
                    return True

                self.gui.presets[preset_name] = {
                    "player1_img": self.gui.entry_path1.get_text().strip(),
                    "player2_img": self.gui.entry_path2.get_text().strip(),
                    "host": self.gui.entry_host.get_text().strip(),
                    "port": self.gui.entry_port.get_text().strip(),
                    "name": self.gui.entry_name.get_text().strip()
                }
                self.gui.save_presets_file(self.gui.presets)
                self.update_preset_list()
                return True

            if hasattr(event.ui_element, 'is_pagination'):
                if event.ui_element.direction == "prev":
                    self.current_page = max(0, self.current_page - 1)
                else:
                    total_pages = (len(self.filtered_presets) + self.items_per_page - 1) // self.items_per_page
                    self.current_page = min(total_pages - 1, self.current_page + 1)
                self.refresh_preset_page()
                return True

        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if self.search_entry and event.ui_element == self.search_entry:
                self.update_preset_list()
                return True

        return False

class GUI:
    pr_dir = Path(__file__).parent.parent

    def __init__(self, spawn_points):
        self.screen = pygame.display.set_mode((650, 400))
        self.manager = pygame_gui.UIManager((650, 400))
        self.clock = pygame.time.Clock()

        self.image_path1 = "assets/ico/player1.png"
        self.image_path2 = "assets/ico/player2.png"
        self.host = "localhost"
        self.port = "12345"
        self.multiplayer = False
        self.name = ""
        self.running = True

        self.presets = self.load_presets()
        self.spawn_points = spawn_points

        self.current_entry = None
        self.file_dialog = None
        self.preset_window = None

        self.exit = False

        self.setup_ui()

    def setup_ui(self):
        self.btn_browse1 = UIButton(relative_rect=pygame.Rect(10, 10, 200, 30),
                                    text='Выбор скина для игрока 1',
                                    manager=self.manager)
        self.entry_path1 = UITextEntryLine(relative_rect=pygame.Rect(220, 10, 400, 30),
                                           manager=self.manager)

        self.btn_browse2 = UIButton(relative_rect=pygame.Rect(10, 60, 200, 30),
                                    text='Выбор скина для игрока 2',
                                    manager=self.manager)
        self.entry_path2 = UITextEntryLine(relative_rect=pygame.Rect(220, 60, 400, 30),
                                           manager=self.manager)

        self.checkbox_multi = UICheckBox(relative_rect=pygame.Rect(10, 110, 50, 30),
                                         text='Сетевая игра',
                                         manager=self.manager)

        UILabel(relative_rect=pygame.Rect(220, 110, 150, 30),
                text="Хост", manager=self.manager)
        self.entry_host = UITextEntryLine(relative_rect=pygame.Rect(380, 110, 150, 30),
                                          manager=self.manager)

        UILabel(relative_rect=pygame.Rect(220, 160, 150, 30),
                text="Порт", manager=self.manager)
        self.entry_port = UITextEntryLine(relative_rect=pygame.Rect(380, 160, 150, 30),
                                          manager=self.manager)

        UILabel(relative_rect=pygame.Rect(220, 210, 150, 30),
                text="Имя", manager=self.manager)
        self.entry_name = UITextEntryLine(relative_rect=pygame.Rect(380, 210, 150, 30),
                                          manager=self.manager)

        self.btn_presets = UIButton(
            relative_rect=pygame.Rect(10, 260, 150, 40),
            text='Пресеты',
            manager=self.manager
        )

        self.btn_start = UIButton(relative_rect=pygame.Rect(250, 350, 150, 40),
                                  text='Запуск', manager=self.manager)

    def on_presets_click(self):
        if self.preset_window is None:
            self.preset_window = PresetWindow(self.manager, self)
        self.preset_window.show()

    def save_presets_file(self, presets):
        preset_dir = str(self.pr_dir / "json")
        preset_file = os.path.join(preset_dir, "presets.json")
        try:
            if not os.path.exists(preset_dir):
                os.makedirs(preset_dir)
            with open(preset_file, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def load_presets(self):
        preset_dir = str(self.pr_dir / "json")
        preset_file = os.path.join(preset_dir, "presets.json")
        if not os.path.exists(preset_file):
            return {}
        try:
            with open(preset_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            return {}

    def handle_file_dialog(self, target_entry):
        if self.file_dialog:
            self.file_dialog.kill()
        self.file_dialog = UIFileDialog(
            pygame.Rect(50, 50, 550, 400),
            self.manager,
            window_title='Выберите скин',
            initial_file_path=str(self.pr_dir),
            allow_existing_files_only=True
        )
        self.current_entry = target_entry

    def process_events(self):
        time_delta = self.clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.exit = True

            if self.preset_window and self.preset_window.process_preset_events(event):
                continue

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.btn_browse1:
                    self.handle_file_dialog(self.entry_path1)
                elif event.ui_element == self.btn_browse2:
                    self.handle_file_dialog(self.entry_path2)
                elif event.ui_element == self.btn_presets:
                    self.on_presets_click()
                elif event.ui_element == self.btn_start:
                    self.on_start()

            if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                if self.current_entry:
                    self.current_entry.set_text(event.text)
                    self.current_entry = None

            if event.type == pygame_gui.UI_WINDOW_CLOSE:
                self.file_dialog = None
                self.current_entry = None
                if self.preset_window:
                    self.preset_window.window = None

            if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
                if event.ui_element == self.entry_host:
                    self.host = event.text
                elif event.ui_element == self.entry_port:
                    self.port = event.text
                elif event.ui_element == self.entry_name:
                    self.name = event.text

            if event.type == pygame_gui.UI_CHECK_BOX_CHECKED:
                if event.ui_element == self.checkbox_multi:
                    self.multiplayer = self.checkbox_multi.check_symbol

            self.manager.process_events(event)

        self.manager.update(time_delta)

    def on_start(self):
        self.image_path1 = self.entry_path1.get_text().strip()
        self.image_path2 = self.entry_path2.get_text().strip()

        if not (self.image_path1 and self.image_path2):
            return

        if self.multiplayer and not self.name:
            return

        if self.multiplayer:
            print(f"Хост: {self.host}, Порт: {self.port}")
        self.running = False

    def run(self):
        pygame.display.set_caption("Запуск DomE 0.1")
        while self.running:
            self.process_events()

            self.screen.fill((50, 50, 50))
            self.manager.draw_ui(self.screen)
            pygame.display.update()

        pygame.quit()
        return self.exit

if __name__ == "__main__":
    spawn_points = []
    gui = GUI(spawn_points)
    gui.run()