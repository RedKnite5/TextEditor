
import tkinter as tk


def reset_grid(event=None):
    canvas.grid_remove()
    canvas.grid(row=0, column=1)

root = tk.Tk()

b = tk.Button(text="hello", command=reset_grid)
b.grid(row=0, column=0)

canvas = tk.Canvas(bg="blue")
canvas.grid(row=0, column=1)


root.mainloop()
