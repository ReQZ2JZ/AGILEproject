import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Данные по задачам
tasks = [
    ("Проектирование", 0, 6),
    ("Интеграция TMDB API", 7, 13),
    ("Интеграция OpenRouter/GPT", 14, 20),
    ("Модули рекомендаций", 21, 34),
    ("Игра 'Угадай фильм'", 35, 41),
    ("Список 'Посмотреть позже'", 42, 48),
    ("Тематические подборки", 49, 55),
    ("FSM и состояния", 56, 62),
    ("Тестирование и отладка", 63, 69),
    ("Финализация и документация", 70, 76),
]

# Начальная дата
start_date = datetime(2025, 3, 1)

# Создание графика
fig, ax = plt.subplots(figsize=(12, 6))

for i, (task, start_offset, end_offset) in enumerate(tasks):
    start = start_date + timedelta(days=start_offset)
    end = start_date + timedelta(days=end_offset)
    ax.barh(i, (end - start).days, left=start, height=0.5, color="skyblue")
    ax.text(start + timedelta(days=1), i, task, va='center', ha='left', fontsize=9)

# Настройка осей
ax.set_yticks(range(len(tasks)))
ax.set_yticklabels([""] * len(tasks))  # убираем лишние надписи слева
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
plt.xticks(rotation=45)
ax.set_title("Диаграмма Ганта — Разработка Telegram-бота", fontsize=14)
plt.tight_layout()
plt.grid(True, axis='x', linestyle='--', alpha=0.6)

# Сохранение в файл
plt.savefig("gantt_telegram_bot.png", dpi=300)
plt.show()
