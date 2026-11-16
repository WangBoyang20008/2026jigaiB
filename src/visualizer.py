"""Pygame front-end: renders Step objects produced by the algorithm generators."""

import random
import sys

import pygame

from algorithms import ALGORITHMS, Step

WIDTH, HEIGHT = 1024, 640
TOP_BAR = 90
FPS = 60

COLORS = {
    "bg": (24, 26, 32),
    "bar": (110, 140, 200),
    "compare": (240, 200, 80),
    "swap": (235, 90, 90),
    "sorted": (90, 200, 130),
    "text": (220, 224, 232),
    "dim": (140, 146, 158),
}

BAR_COUNTS = [20, 50, 100, 200]
SPEEDS = [1, 2, 5, 15, 60]  # generator steps consumed per frame


def make_font(size, bold=False):
    name = pygame.font.match_font("microsoftyahei", bold=bold) or \
           pygame.font.match_font("simhei") or \
           pygame.font.match_font("arial")
    return pygame.font.Font(name, size)


class Visualizer:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Sorting Visualizer 排序算法可视化")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = make_font(18)
        self.font_small = make_font(15)
        self.font_title = make_font(22, bold=True)

        self.algo_keys = list(ALGORITHMS)
        self.algo_idx = 0
        self.bar_count_idx = 1
        self.speed_idx = 1
        self.reset()

    @property
    def algo_key(self):
        return self.algo_keys[self.algo_idx]

    def reset(self):
        n = BAR_COUNTS[self.bar_count_idx]
        self.data = random.sample(range(10, 500), k=n)
        self.generator = None
        self.step = Step(list(self.data))
        self.running = False
        self.finished = False

    def start(self):
        if self.finished:
            self.reset()
        if self.generator is None:
            self.generator = ALGORITHMS[self.algo_key][1](self.data)
        self.running = True

    def advance(self, steps):
        for _ in range(steps):
            try:
                self.step = next(self.generator)
            except StopIteration:
                self.running = False
                self.finished = True
                self.step = Step(self.step.array, sorted_upto=0,
                                 comparisons=self.step.comparisons,
                                 swaps=self.step.swaps)
                return

    def handle_key(self, key):
        if key == pygame.K_SPACE:
            if self.running:
                self.running = False
            else:
                self.start()
        elif key == pygame.K_RIGHT and not self.running and self.generator and not self.finished:
            self.advance(1)  # single step
        elif key == pygame.K_r:
            self.reset()
        elif key == pygame.K_UP:
            self.speed_idx = min(self.speed_idx + 1, len(SPEEDS) - 1)
        elif key == pygame.K_DOWN:
            self.speed_idx = max(self.speed_idx - 1, 0)
        elif key == pygame.K_TAB:
            self.bar_count_idx = (self.bar_count_idx + 1) % len(BAR_COUNTS)
            self.reset()
        elif pygame.K_1 <= key <= pygame.K_1 + len(self.algo_keys) - 1:
            self.algo_idx = key - pygame.K_1
            self.reset()

    def draw_bars(self):
        arr = self.step.array
        n = len(arr)
        if n == 0:
            return
        area_h = HEIGHT - TOP_BAR - 20
        bar_w = WIDTH / n
        max_v = max(arr) or 1
        for i, v in enumerate(arr):
            if i in self.step.swapping:
                color = COLORS["swap"]
            elif i in self.step.comparing:
                color = COLORS["compare"]
            elif self.step.sorted_upto >= 0 and i >= self.step.sorted_upto:
                color = COLORS["sorted"]
            else:
                color = COLORS["bar"]
            h = v / max_v * area_h
            pygame.draw.rect(
                self.screen, color,
                (i * bar_w, HEIGHT - h, max(bar_w - 1, 1), h),
            )

    def draw_header(self):
        label = ALGORITHMS[self.algo_key][0]
        title = self.font_title.render(label, True, COLORS["text"])
        self.screen.blit(title, (16, 12))

        stats = (f"比较 {self.step.comparisons} 次    交换/写入 {self.step.swaps} 次    "
                 f"规模 n={BAR_COUNTS[self.bar_count_idx]}    "
                 f"速度 {SPEEDS[self.speed_idx]} 步/帧    "
                 f"{'已完成' if self.finished else ('运行中' if self.running else '就绪/暂停')}")
        self.screen.blit(self.font.render(stats, True, COLORS["dim"]), (16, 44))

        hints = ("空格 开始/暂停 | → 单步 | R 重置数组 | ↑↓ 调速 | "
                 "Tab 切换规模 | 1-5 切换算法(冒泡/插入/快排/归并/堆)")
        self.screen.blit(self.font_small.render(hints, True, COLORS["dim"]), (16, 68))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            if self.running:
                self.advance(SPEEDS[self.speed_idx])

            self.screen.fill(COLORS["bg"])
            self.draw_header()
            self.draw_bars()
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Visualizer().run()
