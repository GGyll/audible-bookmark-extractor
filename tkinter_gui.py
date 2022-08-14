from tkinter import *

from auth import authorize_audible
import io
import httpx
from PIL import Image, ImageTk

root = Tk()

e = Entry(root, width=50, borderwidth=5)
e.pack()

f = Entry(root, width=50, borderwidth=5)
f.pack()

myLabel1 = Label(root, text="Export and Transcribe your Audible Bookmarks!")
myLabel1.pack()
myLabel2 = Label(root, text="My name is GUstaf")


def myClick():
    myLabel = Label(root, text=e.get())
    myLabel.pack()


button_auth = Button(root, text="Authenticate with Audible",
                     command=lambda: openNewWindow(), fg="blue", bg="#ffffff")
button_auth.pack()


def openNewWindow():

    def captcha_callback(captcha_url: str) -> str:
        #     """Helper function for handling captcha."""
        captcha = httpx.get(captcha_url).content
        f = io.BytesIO(captcha)
        img = Image.open(f)
        img.show()
        guess = entry_captcha.get()

    def _authorize_audible(entry_captcha):
        auth = authorize_audible(e.get(), f.get(), "uk", captcha_callback)

    # Toplevel object which will
    # be treated as a new window
    newWindow = Toplevel()

    # sets the title of the
    # Toplevel widget
    newWindow.title("New Window")

    # sets the geometry of toplevel
    newWindow.geometry("200x200")

    # A Label widget to show in toplevel
    new_label = Label(newWindow, width=200, height=200,
                      text="This is a new window")

    new_label.pack()

    entry_captcha = Entry(root, width=50, borderwidth=5)
    entry_captcha.pack()
    _authorize_audible(entry_captcha)


if __name__ == "__main__":
    root.mainloop()
