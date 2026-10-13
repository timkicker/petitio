# Petitio

A small citizens' petition portal, built for the Cyber Security Base project.
Anyone can post a petition and sign the petitions of others. The code carries
five deliberate flaws from the OWASP Top Ten 2021 and their fixes, each fix
commented out next to its flaw in `pages/views.py`.

## Run

    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seeddata
    python manage.py runserver

Then open http://localhost:8000. The seed command adds a few demo accounts with
weak passwords on purpose: alice/sunshine, bob/liverpool, mallory/123456 and the
moderator mod1.
