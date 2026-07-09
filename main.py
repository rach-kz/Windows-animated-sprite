import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageSequence
import os

class AnimatedSprite:
    def __init__(self, gif_path="0.gif", x=320, y=320):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.wm_attributes('-transparentcolor', '#010101')
        self.root.config(bg='#010101')

        # Инициализация атрибутов
        self.frames = []
        self.delay = 100
        self.current_frame = 0
        self.is_paused = False
        self.speed_multiplier = 1.0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_running = True
        self.update_id = None

        # Если файла нет - создаем тестовый
        if not os.path.exists(gif_path):
            self.create_gif()
            gif_path = "animation.gif"

        # Загружаем GIF
        self.load_gif(gif_path)

        # Если кадров нет - создаем заглушку
        if not self.frames:
            self.create_fallback()

        # Интерфейс
        self.label = tk.Label(self.root, bg='#010101', bd=0)
        self.label.pack()

        if self.frames:
            first_frame = self.frames[0]
            self.root.geometry(f"{first_frame.width()}x{first_frame.height()}+{x}+{y}")
            self.update_frame()
        else:
            self.label.config(text="ОШИБКА", fg="white", bg="#010101")
            self.root.geometry("200x100+{}+{}".format(x, y))

        # Управление
        self.label.bind('<Button-1>', self.start_move)
        self.label.bind('<B1-Motion>', self.do_move)
        self.label.bind('<Double-Button-1>', self.toggle_pause)
        #self.label.bind('<Button-3>', self.show_menu)
        self.root.bind('<Escape>', lambda _e: self.stop())

    @staticmethod
    def create_gif():
        """Создает тестовый анимированный GIF"""
        frames = []
        colors = ['red', 'green', 'blue', 'yellow', 'purple', 'orange']

        for i, color in enumerate(colors):
            img = Image.new('RGB', (200, 200), color=color)
            draw = ImageDraw.Draw(img)
            draw.text((40, 40), str(i+1), fill='white')
            frames.append(img)

        frames[0].save('test_animation.gif',
                       save_all=True,
                       append_images=frames[1:],
                       duration=200,
                       loop=0)

    def load_gif(self, gif_path, size=(320, 320)):
        """Загружает GIF и разбивает на кадры"""
        self.frames = []
        try:
            # Используем контекстный менеджер для автоматического закрытия файла
            with Image.open(gif_path) as img:
                for frame in ImageSequence.Iterator(img):
                    # Конвертируем в RGBA для сохранения прозрачности
                    if frame.mode != 'RGBA':
                        frame = frame.convert('RGBA')
                    frame.thumbnail(size, Image.Resampling.LANCZOS)

                    self.frames.append(ImageTk.PhotoImage(frame))
                # Получаем задержку
                self.delay = img.info.get('duration', 100)
                if self.delay <= 0:
                    self.delay = 100

        except FileNotFoundError:
            print(f"Файл не найден: {gif_path}")
        except Exception as e:
            print(f"Ошибка при загрузке GIF: {e}")

    def create_fallback(self):
        """Создает заглушку"""
        img = Image.new('RGBA', (200, 80), color=(255, 0, 0, 255))
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "НЕТ ИЗОБРАЖЕНИЯ", fill='white')
        photo = ImageTk.PhotoImage(img)
        self.frames = [photo]
        self.delay = 1000

    def update_frame(self):
        """Обновляет текущий кадр анимации"""
        if not self.frames or not self.is_running:
            return

        if not self.is_paused:
            try:
                self.label.config(image=self.frames[self.current_frame])
                self.label.image = self.frames[self.current_frame]
                self.current_frame = (self.current_frame + 1) % len(self.frames)

                actual_delay = max(16, int(self.delay / self.speed_multiplier))
                # noinspection PyTypeChecker
                self.update_id = self.root.after(actual_delay, self.update_frame)
            except Exception as e:
                print(f"Ошибка анимации: {e}")
                # noinspection PyTypeChecker
                self.update_id = self.root.after(100, self.update_frame)
        else:
            # noinspection PyTypeChecker
            self.update_id = self.root.after(250, self.update_frame)

    def toggle_pause(self, _event=None):
        """Пауза/продолжение"""
        self.is_paused = not self.is_paused
        if not self.is_paused:
            if self.update_id is not None:
                self.root.after_cancel(self.update_id)
                self.update_id = None
            self.update_frame()

    def show_menu(self, event):
        """Контекстное меню"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="⏸ Пауза" if not self.is_paused else "▶ Продолжить",
            command=self.toggle_pause
        )
        menu.add_separator()
        speed_menu = tk.Menu(menu, tearoff=0)
        speeds = [0.5, 1.0, 2.0]
        for speed in speeds:
            label = f"{speed}x {'✓' if self.speed_multiplier == speed else ''}"
            speed_menu.add_command(
                label=label,
                command=lambda s=speed: self.set_speed(s))
        menu.add_cascade(label="🚀 Скорость", menu=speed_menu)
        menu.add_separator()
        menu.add_command(label="❌ Закрыть", command=self.stop)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def set_speed(self, multiplier):
        """Изменение скорости"""
        self.speed_multiplier = multiplier
        if not self.is_paused and self.update_id is not None:
            self.root.after_cancel(self.update_id)
            self.update_id = None
            self.update_frame()

    def start_move(self, event):
        """Начало перетаскивания"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def do_move(self, event):
        """Перетаскивание"""
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        """Запуск"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Остановка"""
        self.is_running = False
        if self.update_id is not None:
            try:
                self.root.after_cancel(self.update_id)
            except (tk.TclError, ValueError):
                pass
            self.update_id = None
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

if __name__ == "__main__":
    sprite = AnimatedSprite("3.gif")
    sprite.run()