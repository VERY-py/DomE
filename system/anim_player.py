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

    def play(self, screen: pygame.Surface, pos: Tuple[int, int],
             reset: bool = False) -> bool:
        """
        Воспроизводит текущий кадр анимации.

        Args:
            screen: Поверхность для отрисовки
            pos: Позиция (x, y)
            reset: Сбросить анимацию в начало

        Returns:
            bool: True если анимация активна
        """
        if reset:
            self.current_frame = 0

        if not self.frames:
            return False

        screen.blit(self.frames[self.current_frame], pos)

        return True

    def update(self, dt: float) -> bool:
        """
        Обновляет состояние анимации (вызывать каждый кадр).

        Args:
            dt: Время с последнего кадра в секундах

        Returns:
            bool: True если анимация активна
        """
        if not self.frames:
            return False

        self._frame_time += dt * 1000

        if self._frame_time >= self._frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames) if self.loop else min(
                self.current_frame + 1, len(self.frames) - 1)
            self._frame_time = 0

        return self.loop or self.current_frame < len(self.frames) - 1

    def reset(self) -> None:
        """Сбрасывает анимацию в начало."""
        self.current_frame = 0
        self._frame_time = 0

    def is_finished(self) -> bool:
        """Проверяет, завершилась ли анимация."""
        return not self.loop and self.current_frame >= len(self.frames) - 1

    def get_current_frame(self) -> Optional[pygame.Surface]:
        """Возвращает текущий кадр."""
        if self.frames:
            return self.frames[self.current_frame]
        return None
