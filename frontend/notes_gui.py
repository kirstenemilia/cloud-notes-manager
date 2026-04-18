import tkinter as tk
import requests

editing_note_id = None
filtered_notes = []

# global variables
token = None
notes_cache = []

API_URL = "http://127.0.0.1:5000"

# FUNCTIONS

def load_notes():
    global notes_cache, filtered_notes

    response = requests.get(
        f"{API_URL}/api/notes/",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        notes_cache = response.json()
    else:
        notes_cache = []

    filtered_notes = notes_cache

    listbox.delete(0, tk.END)

    for note in filtered_notes:
        listbox.insert(tk.END, note["title"])

    listbox.selection_clear(0, tk.END)


def add_note():
    global editing_note_id

    title = title_entry.get()
    content = content_entry.get()

    if not title or not content:
        return

    headers = {"Authorization": f"Bearer {token}"}

    if editing_note_id:  # edit mode
        requests.patch(
            f"{API_URL}/api/notes/{editing_note_id}",
            json={"title": title, "content": content},
            headers=headers
        )
        editing_note_id = None

    else:  # create mode
        requests.post(
            f"{API_URL}/api/notes/",
            json={"title": title, "content": content},
            headers=headers
        )

    title_entry.delete(0, tk.END)
    content_entry.delete(0, tk.END)

    load_notes()
    
def show_note(event):
    selection = listbox.curselection()

    if not selection:
        return

    index = selection[0]

    if index >= len(filtered_notes):
        return

    note = filtered_notes[index]

    view_title.config(text=note["title"])
    view_content.config(text=note["content"])


def delete_note():
    if not listbox.curselection():
        return

    index = listbox.curselection()[0]
    note_id = filtered_notes[index]["id"]

    requests.delete(
        f"{API_URL}/api/notes/{note_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    load_notes()

def go_to_list():
    add_frame.pack_forget()
    list_frame.pack(fill="both", expand=True)


def go_to_add():
    list_frame.pack_forget()
    add_frame.pack(fill="both", expand=True)

def edit_note():
    global editing_note_id

    if not listbox.curselection():
        return

    index = listbox.curselection()[0]
    note = filtered_notes[index]

    editing_note_id = note["id"]

    go_to_add()

    title_entry.delete(0, tk.END)
    title_entry.insert(0, note["title"])

    content_entry.delete(0, tk.END)
    content_entry.insert(0, note["content"])


def search_notes():
    global filtered_notes

    query = search_entry.get().lower()

    listbox.delete(0, tk.END)

    filtered_notes = [
        note for note in notes_cache
        if query in note["title"].lower() or query in note["content"].lower()
    ]

    for note in filtered_notes:
        listbox.insert(tk.END, note["title"])

    listbox.selection_clear(0, tk.END)


def login():
    global token

    username = login_user_entry.get()
    password = login_pass_entry.get()

    response = requests.post(
        f"{API_URL}/api/login",
        json={
            "username": username,
            "password": password
        }
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        status_label.config(text="Logged in!", fg="green")

        login_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)

        go_to_add()
        load_notes()
    else:
        status_label.config(text="Login failed", fg="red")

def register():
    username = login_user_entry.get()
    password = login_pass_entry.get()

    response = requests.post(
        f"{API_URL}/api/register",
        json={
            "username": username,
            "password": password
        }
    )

    if response.status_code == 201:
        status_label.config(text="User created! Now login.", fg="green")
    else:
        status_label.config(text="Registration failed", fg="red")

# WINDOW

root = tk.Tk()
root.configure(bg="lightblue")
root.title("Notes App")
root.geometry("400x400")

login_frame = tk.Frame(root, bg="lightblue")
login_frame.pack(fill="both", expand=True) #only show LOGIN frame at startup

main_frame = tk.Frame(root)

add_frame = tk.Frame(main_frame, bg="lightblue")
list_frame = tk.Frame(main_frame, bg="lightblue")

#LOGIN SCREEN
tk.Label(login_frame, text="Username", font=("Segoe UI", 11, "bold"), bg="lightblue").pack()

login_user_entry = tk.Entry(login_frame)
login_user_entry.pack()

tk.Label(login_frame, text="Password", font=("Segoe UI", 11, "bold"), bg="lightblue").pack()

login_pass_entry = tk.Entry(login_frame, show="*")
login_pass_entry.pack()

tk.Button(login_frame, text="Login", command=login).pack(pady=5)
tk.Button(login_frame, text="Register", command=register).pack(pady=5)

status_label = tk.Label(login_frame, text="")
status_label.pack()
# ADD SCREEN

tk.Label(add_frame, text="Title", font=("Segoe UI", 12, "bold"), bg="lightblue").pack()
title_entry = tk.Entry(add_frame)
title_entry.pack(pady=(0, 13))

tk.Label(add_frame, text="Content", font=("Segoe UI", 12, "bold"), bg="lightblue").pack()
content_entry = tk.Entry(add_frame)
content_entry.pack(pady=(0, 13))

tk.Button(add_frame, text="Add Note", command=add_note).pack(pady=5)
tk.Button(add_frame, text="Go to Notes", command=go_to_list).pack()

# LIST SCREEN

view_title = tk.Label(list_frame, text="", font=("Segoe UI", 12, "bold"))
view_content = tk.Label(list_frame, text="", wraplength=350, justify="left")

search_entry = tk.Entry(list_frame)
search_entry.pack(pady=(10, 5))

tk.Button(list_frame, text="Search", command=search_notes).pack()
tk.Button(list_frame, text="Reset", command=load_notes).pack()

listbox = tk.Listbox(list_frame, width=50)
listbox.pack(pady=(0, 13))

listbox.bind("<<ListboxSelect>>", show_note)

view_title.pack()
view_content.pack(pady=10)

tk.Button(list_frame, text="Edit Note", command=edit_note).pack(pady=(0, 10))
tk.Button(list_frame, text="Delete Note", command=delete_note).pack(pady=(0, 13))
tk.Button(list_frame, text="Back to Add Note", command=go_to_add).pack()

# RUN
# do NOT load notes at startup
root.mainloop()