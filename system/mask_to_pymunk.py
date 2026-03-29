import pygame
import pymunk
import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class RectSegment:
    """Прямоугольный сегмент для создания pymunk.Poly."""
    x: float
    y: float
    width: float
    height: float


class MaskToPymunk:
    """Конвертирует pygame.mask.Mask в набор статичных физических объектов Pymunk."""

    def __init__(self, mask: pygame.mask.Mask,
                 min_rect_size: int = 8,
                 simplify_threshold: float = 0.9):
        """
        Инициализация конвертера.

        Args:
            mask: маска уровня (препятствия)
            min_rect_size: минимальный размер прямоугольника (пикселей)
            simplify_threshold: порог упрощения для объединения соседних блоков (0-1)
        """
        self.mask = mask
        self.min_rect_size = min_rect_size
        self.simplify_threshold = simplify_threshold
        self.width = mask.get_size()[0]
        self.height = mask.get_size()[1]

    def extract_blocks(self) -> List[RectSegment]:
        """
        Извлекает прямоугольные блоки из маски.
        Использует алгоритм сканирования и объединения.
        """
        # Создаём булеву матрицу (True = препятствие)
        matrix = self._mask_to_matrix()

        # Отмечаем уже обработанные пиксели
        processed = np.zeros((self.height, self.width), dtype=bool)
        blocks = []

        # Проходим по всей матрице
        for y in range(self.height):
            for x in range(self.width):
                if matrix[y][x] and not processed[y][x]:
                    # Находим максимальный прямоугольник, начиная с текущей позиции
                    block = self._find_max_rectangle(matrix, processed, x, y)
                    if block.width >= self.min_rect_size and block.height >= self.min_rect_size:
                        blocks.append(block)
                        # Отмечаем все пиксели этого блока как обработанные
                        self._mark_processed(processed, block)

        # Объединяем соседние блоки для оптимизации
        blocks = self._merge_adjacent_blocks(blocks)

        return blocks

    def _mask_to_matrix(self) -> List[List[bool]]:
        """Преобразует маску в булеву матрицу."""
        matrix = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Проверяем, есть ли пиксель в маске
                row.append(bool(self.mask.get_at((x, y))))
            matrix.append(row)
        return matrix

    def _find_max_rectangle(self, matrix: List[List[bool]],
                            processed: np.ndarray,
                            start_x: int, start_y: int) -> RectSegment:
        """Находит максимальный прямоугольник, начинающийся с (start_x, start_y)."""
        # Определяем максимальную ширину на текущей строке
        max_width = self.width - start_x
        for x in range(start_x, self.width):
            if not matrix[start_y][x] or processed[start_y][x]:
                max_width = x - start_x
                break

        if max_width == 0:
            return RectSegment(start_x, start_y, 1, 1)

        # Расширяем прямоугольник вниз, пока это возможно
        height = 1
        for y in range(start_y + 1, self.height):
            # Проверяем всю строку на наличие препятствий
            valid_row = True
            for x in range(start_x, start_x + max_width):
                if not matrix[y][x] or processed[y][x]:
                    valid_row = False
                    break

            if not valid_row:
                break
            height += 1

        return RectSegment(start_x, start_y, max_width, height)

    def _mark_processed(self, processed: np.ndarray, block: RectSegment):
        """Отмечает пиксели блока как обработанные."""
        for y in range(int(block.y), int(block.y + block.height)):
            for x in range(int(block.x), int(block.x + block.width)):
                if y < self.height and x < self.width:
                    processed[y][x] = True

    def _merge_adjacent_blocks(self, blocks: List[RectSegment]) -> List[RectSegment]:
        """Объединяет соседние блоки для оптимизации."""
        if not blocks:
            return blocks

        merged = []
        used = [False] * len(blocks)

        for i, block1 in enumerate(blocks):
            if used[i]:
                continue

            current_block = RectSegment(block1.x, block1.y, block1.width, block1.height)
            changed = True

            while changed:
                changed = False
                for j, block2 in enumerate(blocks):
                    if used[j] or j == i:
                        continue

                    # Проверяем возможность объединения
                    if self._can_merge_horizontal(current_block, block2):
                        current_block = self._merge_horizontal(current_block, block2)
                        used[j] = True
                        changed = True
                    elif self._can_merge_vertical(current_block, block2):
                        current_block = self._merge_vertical(current_block, block2)
                        used[j] = True
                        changed = True

            merged.append(current_block)

        return merged

    def _can_merge_horizontal(self, block1: RectSegment, block2: RectSegment) -> bool:
        """Проверяет, можно ли объединить блоки по горизонтали."""
        if abs(block1.y - block2.y) > self.simplify_threshold:
            return False
        if abs(block1.height - block2.height) > self.simplify_threshold:
            return False
        # Проверяем, соприкасаются ли блоки по горизонтали
        if abs((block1.x + block1.width) - block2.x) <= self.simplify_threshold:
            # Проверяем перекрытие по вертикали
            overlap_y = min(block1.y + block1.height, block2.y + block2.height) - max(block1.y, block2.y)
            if overlap_y >= min(block1.height, block2.height) * 0.5:
                return True
        return False

    def _merge_horizontal(self, block1: RectSegment, block2: RectSegment) -> RectSegment:
        """Объединяет два блока по горизонтали."""
        new_x = min(block1.x, block2.x)
        new_width = max(block1.x + block1.width, block2.x + block2.width) - new_x
        new_y = min(block1.y, block2.y)
        new_height = max(block1.y + block1.height, block2.y + block2.height) - new_y
        return RectSegment(new_x, new_y, new_width, new_height)

    def _can_merge_vertical(self, block1: RectSegment, block2: RectSegment) -> bool:
        """Проверяет, можно ли объединить блоки по вертикали."""
        if abs(block1.x - block2.x) > self.simplify_threshold:
            return False
        if abs(block1.width - block2.width) > self.simplify_threshold:
            return False
        # Проверяем, соприкасаются ли блоки по вертикали
        if abs((block1.y + block1.height) - block2.y) <= self.simplify_threshold:
            # Проверяем перекрытие по горизонтали
            overlap_x = min(block1.x + block1.width, block2.x + block2.width) - max(block1.x, block2.x)
            if overlap_x >= min(block1.width, block2.width) * 0.5:
                return True
        return False

    def _merge_vertical(self, block1: RectSegment, block2: RectSegment) -> RectSegment:
        """Объединяет два блока по вертикали."""
        new_y = min(block1.y, block2.y)
        new_height = max(block1.y + block1.height, block2.y + block2.height) - new_y
        new_x = min(block1.x, block2.x)
        new_width = max(block1.x + block1.width, block2.x + block2.width) - new_x
        return RectSegment(new_x, new_y, new_width, new_height)

    def create_pymunk_shapes(self, space, elasticity=0.3, friction=0.5, static_body=None):
        """Создаёт физические формы Pymunk из маски."""
        if static_body is None:
            static_body = space.static_body

        blocks = self.extract_blocks()
        shapes = []

        for block in blocks:
            # Пропускаем слишком маленькие блоки
            if block.width < 2 or block.height < 2:
                continue

            points = [
                (block.x, block.y),
                (block.x + block.width, block.y),
                (block.x + block.width, block.y + block.height),
                (block.x, block.y + block.height)
            ]

            shape = pymunk.Poly(static_body, points)
            shape.elasticity = elasticity
            shape.friction = friction
            space.add(shape)
            shapes.append(shape)

        return shapes


def visualize_blocks(screen: pygame.Surface, blocks: List[RectSegment], color=(255, 0, 0), offset=(0, 0)):
    """
    Визуализирует прямоугольные блоки для отладки.

    Args:
        screen: поверхность Pygame
        blocks: список блоков
        color: цвет отрисовки
        offset: смещение (для комнат, которые не с (0,0) начинаются)
    """
    for block in blocks:
        rect = pygame.Rect(
            block.x + offset[0],
            block.y + offset[1],
            block.width,
            block.height
        )
        pygame.draw.rect(screen, color, rect, 1)