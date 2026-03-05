import pygame
from pathlib import Path
from typing import Optional, Tuple

def count_files(folder_path: str) -> int:
    """Подсчитывает количество PNG файлов в папке."""
    folder = Path(folder_path)
    return sum(1 for item in folder.iterdir() if item.is_file() and item.suffix.lower() == '.png')

class Animation:
    def __init__(self, folder: str, fps: int = 10, loop: bool = True):
        """
        Инициализация анимации.

        Args:
            folder: Путь к папке с кадрами (1.png, 2.png, ...)
            fps: Кадров в секунду (по умолчанию 10)
            loop: Зацикливать анимацию (по умолчанию True)
        """
        self.folder = Path(folder)
        self.frame_count = count_files(folder)
        self.fps = fps
        self.loop = loop
        self.frames = []
        self.current_frame = 0
        self._frame_time = 0
        self._is_playing = True  # Флаг состояния воспроизведения
        self._is_finished = False  # Флаг завершения анимации
        self._load_frames()
        self._frame_delay = 1000 / fps  # Задержка в миллисекундах между кадрами

    def _load_frames(self) -> None:
        """Предзагружает все кадры в память."""
        self.frames = []
        for n in range(1, self.frame_count + 1):
            frame_path = self.folder / f"{n}.png"
            if frame_path.exists():
                frame = pygame.image.load(frame_path).convert_alpha()
                self.frames.append(frame)
        # Проверяем, что загрузились все ожидаемые кадры
        if len(self.frames) != self.frame_count:
            print(f"Внимание: загружено {len(self.frames)} кадров из {self.frame_count}")

    def play(self, screen: pygame.Surface, pos: Tuple[int, int],
             reset: bool = False) -> bool:
        """
        Воспроизводит текущий кадр анимации.

        Args:
            screen: Поверхность для отрисовки
            pos: Позиция (x, y)
            reset: Сбросить анимацию в начало

        Returns:
            bool: True если анимация активна и отображается
        """
        if reset:
            self.reset()

        if not self.frames or not self._is_playing:
            return False

        screen.blit(self.frames[self.current_frame], pos)
        return True

    def update(self, dt: float) -> bool:
        """
        Обновляет состояние анимации (вызывать каждый кадр).

        Args:
            dt: Время с последнего кадра в секундах

        Returns:
            bool: True если анимация должна продолжаться
        """
        if not self.frames or not self._is_playing or self._is_finished:
            return False

        self._frame_time += dt * 1000

        if self._frame_time >= self._frame_delay:
            if self.loop:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
            else:
                if self.current_frame < len(self.frames) - 1:
                    self.current_frame += 1
                else:
                    self._is_finished = True
            self._frame_time = 0

        return not self._is_finished

    def stop(self) -> None:
        """Останавливает анимацию на текущем кадре."""
        self._is_playing = False

    def start(self) -> None:
        """Запускает или возобновляет анимацию."""
        self._is_playing = True
        self._is_finished = False

    def reset(self) -> None:
        """Сбрасывает анимацию в начало."""
        self.current_frame = 0
        self._frame_time = 0
        self._is_finished = False
        # Если анимация была остановлена, при сбросе запускаем её
        self._is_playing = True

    def is_finished(self) -> bool:
        """Проверяет, завершилась ли анимация."""
        return self._is_finished

    def is_playing(self) -> bool:
        """Проверяет, воспроизводится ли анимация в данный момент."""
        return self._is_playing

    def get_current_frame(self) -> Optional[pygame.Surface]:
        """Возвращает текущий кадр."""
        if self.frames:
            return self.frames[self.current_frame]
        return None

    def set_fps(self, fps: int) -> None:
        """Изменяет скорость воспроизведения анимации."""
        self.fps = fps
        self._frame_delay = 1000 / fps

    def get_progress(self) -> float:
        """Возвращает прогресс анимации в процентах (0.0–1.0)."""
        if not self.frames:
            return 0.0
        return self.current_frame / (len(self.frames) - 1) if len(self.frames) > 1 else 1.0
