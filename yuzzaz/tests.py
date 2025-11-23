import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dadjokess.settings")
django.setup()

from content.models import Joke, JokeLike, JokeComment

from django.test import TestCase

# Create your tests here.



# print(generate_username(1))
import time
from random_username.generate import generate_username
from content.models import Joke, JokeLike, JokeComment
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
import requests
import random

User = get_user_model()

while True:
    def random_hex_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    for i in range(0, 99):
        response = requests.get("https://icanhazdadjoke.com/", headers={"Accept": "text/plain"})
        user = User.objects.get(username="gftinity")
        font_types = [ ('Arial', 'Arial'),
                    ('Times New Roman', 'Times New Roman'), 
                    ('Courier New', 'Courier New'), 
                    ('Georgia', 'Georgia'), 
                    ('Verdana', 'Verdana'),
                    ('Comic Sans MS', 'Comic Sans MS'),
                        ('Trebuchet MS', 'Trebuchet MS'),
                        ('Impact', 'Impact'),
                        ('Lucida Console', 'Lucida Console'),
                        ('Palatino Linotype', 'Palatino Linotype')
                        
                    ]
        
        joke = Joke.objects.create(
            joke_by = user,
            content=response.text,
            bg_color=random_hex_color(),
            text_color=random_hex_color(),
            font_type=random.choice(font_types)[0],
            description=f"Description for joke {i+1}",

        )
        print(f"Created joke with ID: {joke.id}")
    






    django.setup()
    items = Joke.objects.all()
    print("Total jokes in DB:", items.count())

    # --- 2. Deduplicate by 'content' AND 'user' ---
    # Keep one instance per (content, joke_by) combination
    seen = {}
    duplicates = []

    for item in items:
        key = (item.content, item.joke_by.id)
        if key not in seen:
            seen[key] = item  # keep this one
        else:
            duplicates.append(item)  # mark for deletion

    print("Duplicates found:", len(duplicates))

    # --- 3. Delete duplicates from DB ---
    for dup in duplicates:
        dup.delete()

    # --- 4. Verify ---
    items_after = Joke.objects.all()
    print("Total jokes after deletion:", items_after.count())

    unique_jokes_after = list({(item.content, item.joke_by.id): item for item in items_after}.values())
    print("Unique jokes by content & user after deletion:", len(unique_jokes_after))

    with open("jokes.txt", "w") as log_file:
        for item in unique_jokes_after:
            log_file.write(f"User ID: {item.joke_by.id if item.joke_by else 'None'} | Joke ID: {item.id} | Content: {item.content}\n")

    # exec(open("yuzzaz/testscopy.py").read())











    time.sleep(60)

# exec(open("yuzzaz/tests.py").read())

