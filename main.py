# -*- coding: cp1251 -*-
import re
from recognizer import recognition
from validator import validation
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import Progressbar
from tkinterdnd2 import *
from tkinter.messagebox import showwarning
import threading


def save_mistakes(output_path, mistakes):
    text = "Название статьи:\n"
    for mistake in mistakes[0]:
        text += mistake + "\n"

    text += "Список авторов:\n"
    for mistake in mistakes[1]:
        text += mistake + "\n"

    text += "Аннотация:\n"
    for mistake in mistakes[2]:
        text += mistake + "\n"

    text += "Список ключевых слов:\n"
    for mistake in mistakes[3]:
        text += mistake + "\n"

    text += "Аффилиация:\n"
    for mistake in mistakes[4]:
        text += mistake + "\n"

    text += "Заголовки разделов:\n"
    for mistake in mistakes[5]:
        text += mistake + "\n"

    text += "Рисунки, таблицы и ссылки:\n"
    for mistake in mistakes[6]:
        text += mistake + "\n"

    if len(mistakes[7]) != 0:
        text += mistakes[7][0] + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 1000),
        height * (bbox[1] / 1000),
        width * (bbox[2] / 1000),
        height * (bbox[3] / 1000),
    ]


def start_thread():
    threading.Thread(target=pdf_scan, daemon=True).start()


def pdf_scan():
    global entryWidget, outputWidget
    output_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not output_path.endswith(".txt"):
        showwarning(title="Предупреждение", message="Неправильный формат файла!")
        return 0
    # Окно сканирования
    window = Toplevel()
    window.title("Сканирование")
    window.geometry("250x50")
    window.protocol("WM_DELETE_WINDOW", lambda: 0)

    # Шкала прогресса
    progress = Progressbar(window, orient="horizontal", length=200, mode="indeterminate")
    progress.pack(anchor=CENTER)
    progress.start(10)
    root.update()

    outputWidget.delete("1.0", END)
    outputWidget.configure(state=DISABLED)
    path = entryWidget.get("1.0", END)
    path = path[:-1]

    pages, width = recognition(path, output_path[:-3] + "pdf")
    mistakes = validation(pages, width)
    output = save_mistakes(output_path, mistakes)
    lines = output.split("\n")
    length = 80
    for line in lines:
        if length < len(line):
            length = len(line)
    entryWidget.configure(width=length)
    outputWidget.configure(state=NORMAL)
    outputWidget.configure(width=length)
    outputWidget.insert("1.0", output)
    window.destroy()


def pdf_drop(event):
    global entryWidget
    path = event.data
    if path.startswith("{") and path.endswith("}"):
        path = path[1:-1]
    if path.endswith("\n"):
        path = path[0:-1]
    extensions = re.findall(r"\.[a-z]{3,4}", path)
    if len(extensions) == 1 and extensions[0] == ".pdf":
        entryWidget.configure(state=NORMAL)
        entryWidget.delete("1.0", END)
        entryWidget.insert("1.0", path)
        entryWidget.configure(state=DISABLED)
    else:
        showwarning(title="Предупреждение", message="Неправильный формат файла!")


# Создание формы и событий
root = TkinterDnD.Tk()
root.title("ИИ-рецензент")
root.geometry("800x420")
root.option_add("*tearOff", FALSE)

# Создание окна для ввода
entryWidget = Text(root, height=3)
entryWidget.pack(anchor=N)
entryWidget.insert("1.0", "Перетащите файл PDF сюда.")
entryWidget.configure(state=DISABLED)
entryWidget.drop_target_register(DND_FILES)
entryWidget.dnd_bind("<<Drop>>", pdf_drop)

# Создание кнопки
btn = Button(root, text="Сканировать", command=start_thread)
btn.pack(anchor=CENTER, padx=10, pady=10)

# Создание окна для вывода
outputWidget = Text(root)
outputWidget.pack(anchor=S, fill=Y)

root.mainloop()
