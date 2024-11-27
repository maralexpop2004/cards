import sqlite3
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw

# База данных
DB_NAME = "cards.db"

# Путь к папке с изображениями
IMAGE_PATH = "images"


# Создаем базу данных
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        suit TEXT,
        rank TEXT,
        is_played BOOLEAN DEFAULT 0
    )
    """)

    # Проверяем, заполнена ли база
    cursor.execute("SELECT COUNT(*) FROM cards")
    if cursor.fetchone()[0] == 0:
        suits = ['Черви', 'Бубны', 'Пики', 'Трефы']
        ranks = ['6', '7', '8', '9', '10', 'Валет', 'Дама', 'Король', 'Туз']
        for suit in suits:
            for rank in ranks:
                cursor.execute("INSERT INTO cards (suit, rank) VALUES (?, ?)", (suit, rank))
        conn.commit()
    conn.close()


# Получаем все карты, сгруппированные по мастям
def get_all_cards_by_suit():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, suit, rank, is_played FROM cards 
    ORDER BY suit, 
        CASE rank 
            WHEN '6' THEN 1 
            WHEN '7' THEN 2 
            WHEN '8' THEN 3 
            WHEN '9' THEN 4 
            WHEN '10' THEN 5 
            WHEN 'Валет' THEN 6 
            WHEN 'Дама' THEN 7 
            WHEN 'Король' THEN 8 
            WHEN 'Туз' THEN 9 
        END
    """)
    cards = cursor.fetchall()
    conn.close()
    suits = {'Черви': [], 'Бубны': [], 'Пики': [], 'Трефы': []}
    for card_id, suit, rank, is_played in cards:
        suits[suit].append((card_id, rank, is_played))
    return suits


# Переключаем статус карты (активна/выбывшая)
def toggle_card_status(card_id, is_played):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    new_status = 0 if is_played else 1
    cursor.execute("UPDATE cards SET is_played = ? WHERE id = ?", (new_status, card_id))
    conn.commit()
    conn.close()


# Сбрасываем статус всех карт
def reset_card_status():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE cards SET is_played = 0")
    conn.commit()
    conn.close()


# Создаем блеклое и перечеркнутое изображение
def create_faded_cross_image(image):
    image = image.convert("RGBA")
    faded = Image.new("RGBA", image.size, (255, 255, 255, 150))
    image = Image.alpha_composite(image, faded)

    draw = ImageDraw.Draw(image)
    draw.line((0, 0, image.size[0], image.size[1]), fill=(0, 0, 0, 200), width=3)
    draw.line((image.size[0], 0, 0, image.size[1]), fill=(0, 0, 0, 200), width=3)
    return image


# Интерфейс
class CardTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер карт")
        self.root.geometry("1000x600")

        # Заголовок
        tk.Label(root, text="Карты", font=("Arial", 16)).pack(pady=10)

        # Фрейм для отображения карт
        self.card_frame = tk.Frame(root)
        self.card_frame.pack(pady=10, fill="both", expand=True)
        self.update_card_list()

        # Кнопка обновления
        tk.Button(root, text="Сбросить и обновить список", command=self.reset_and_update).pack(pady=10)

    def update_card_list(self):
        for widget in self.card_frame.winfo_children():
            widget.destroy()

        cards_by_suit = get_all_cards_by_suit()
        row = 0
        for suit, cards in cards_by_suit.items():
            # Добавляем название масти в первой колонке
            tk.Label(self.card_frame, text=f"{suit}:", font=("Arial", 12, "bold")).grid(row=row, column=0, padx=10,
                                                                                        pady=5, sticky="w")

            col = 1
            for card_id, rank, is_played in cards:
                image_path = f"{IMAGE_PATH}/{rank.lower()}_{suit.lower()}.png"
                text_color = "red" if suit in ["Черви", "Бубны"] else "black"  # Цвет текста для бубен и червей

                try:
                    image = Image.open(image_path)
                    if is_played:
                        image = create_faded_cross_image(image)
                    photo = ImageTk.PhotoImage(image.resize((50, 75)))

                    # Кнопка с изображением
                    card_button = tk.Button(
                        self.card_frame,
                        image=photo,
                        command=lambda cid=card_id, played=is_played: self.toggle_card(cid, played)
                    )
                    card_button.image = photo
                    card_button.grid(row=row, column=col, padx=5, pady=5)

                except FileNotFoundError:
                    # Если изображения нет, показываем текстовый вариант
                    bg_color = 'lightgray' if is_played else 'white'
                    text = f"~{rank}~" if is_played else rank
                    card_button = tk.Button(
                        self.card_frame,
                        text=text,
                        command=lambda cid=card_id, played=is_played: self.toggle_card(cid, played),
                        bg=bg_color,
                        fg=text_color,  # Устанавливаем цвет текста
                        font=("Arial", 10)
                    )
                    card_button.grid(row=row, column=col, padx=5, pady=5)

                col += 1
            row += 1

    def reset_and_update(self):
        reset_card_status()
        self.update_card_list()

    def toggle_card(self, card_id, is_played):
        toggle_card_status(card_id, is_played)
        self.update_card_list()


# Основная программа
if __name__ == "__main__":
    init_database()
    root = tk.Tk()
    app = CardTrackerApp(root)
    root.mainloop()
