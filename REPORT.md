LINK: https://github.com/timkicker/petitio

Petitio is a small citizens' petition portal. Anyone can post a petition, read and search the petitions of others and sign one with a name and an email. A signed in user owns the petitions they create and a moderator can close or delete any of them. The app runs on Python and Django and keeps its data in SQLite, so the flaws and their fixes all sit in the backend where a user cannot reach them from the browser. I built it on purpose around five flaws from the OWASP Top Ten 2021 and I stayed on that one list. Each fix sits right next to its flaw as a commented out block in the same file, so the repository holds a single version with no branches for the fixes.

I chose the five flaws so that they form one chain and not five loose bugs. The injection in the search leaks the stored password hashes. The hashes are unsalted MD5 and a short wordlist turns them back into plaintext. The login has no lockout, so that wordlist can run without end. With a password in hand the broken access control lets an attacker edit or delete petitions that belong to other people and read the signer emails. None of this is written down, so the whole run stays invisible afterwards.

installation:

    python -m venv venv
    source venv/bin/activate        (Windows: venv\Scripts\activate)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seeddata
    python manage.py runserver

The seed command creates four demo accounts with weak passwords on purpose: alice/sunshine, bob/liverpool, mallory/123456 and the moderator mod1. The site then runs at http://localhost:8000.

FLAW 1 (A01 Broken Access Control):
https://github.com/timkicker/petitio/blob/main/pages/views.py#L90
The views that edit, delete and list the signatures of a petition check only that someone is signed in. They never check that the account actually owns the petition. Any user can open the edit URL of a petition that belongs to someone else and change or delete it. The signatures page hands out the name and email of everyone who signed. The moderation view does its own role check correctly, which shows that the gap is the missing owner check in these three views and not a general lack of checks. The effect is in flaw-1-before-1.png and flaw-1-after-1.png.
How to fix it: compare the owner of the petition against the current account before touching it and answer with 403 when they differ and the account is not a moderator. The commented fix under each of the three views does this with one guard, if petition.owner_id != account.id and not account.is_moderator: return HttpResponseForbidden().

FLAW 2 (A02 Cryptographic Failures):
https://github.com/timkicker/petitio/blob/main/pages/views.py#L16
Passwords are stored as an unsalted MD5 hash in hash_pw. MD5 is fast and without a salt the same password always gives the same hash, so a leaked hash falls to a rainbow table or a short wordlist almost at once. Paired with flaw 3, which leaks the hashes, this is enough to recover the plaintext passwords. The stored hash of the demo user alice is nothing more than the MD5 of the word sunshine. The before and after are in flaw-2-before-1.png and flaw-2-after-1.png.
How to fix it: hash with a slow and salted algorithm. The commented fix replaces hash_pw and verify_pw with Django's make_password and check_password, which use PBKDF2 with a per password salt and many rounds. A new registration then stores a pbkdf2_sha256 hash and the login keeps working.

FLAW 3 (A03 Injection):
https://github.com/timkicker/petitio/blob/main/pages/views.py#L65
The search builds its SQL by pasting the query text straight into the statement string. A crafted query breaks out of the quotes, so an input of the shape ' UNION SELECT username, password_hash FROM pages_account -- turns the search into a dump of every account next to its hash. The shot flaw-3-before-1.png shows the input in the URL and the four users with their hashes in the result. The follow up flaw-3-after-1.png shows the same input returning nothing after the fix.
How to fix it: never build SQL by string formatting. The commented fix uses the ORM with Petition.objects.filter(title__icontains=q), which passes the input as a bound parameter so it can no longer change the shape of the query. A normal search for a word in a title still returns the same petitions.

FLAW 4 (A07 Identification and Authentication Failures):
https://github.com/timkicker/petitio/blob/main/pages/views.py#L190
The login has no rate limiting. The account even carries a failed_logins counter but the login never reads it, so an attacker can try one password after another without end. Together with the weak hashes from flaw 2 a short wordlist finds a password in seconds. Registration has no length rule either, so a one character password is accepted. flaw-4-before-1.png and flaw-4-after-1.png show the endless attempts and then the lockout.
How to fix it: count the failed attempts and lock the account after five, set the counter back to zero on a correct password and ask for a minimum length on register. The commented fix in loginView does this, so after five wrong tries even the correct password is refused with a locked message. A normal login within the limit still works.

FLAW 5 (A09 Security Logging and Monitoring Failures):
https://github.com/timkicker/petitio/blob/main/pages/views.py#L31
Nothing security relevant is recorded. A failed login, a delete of someone else's petition and a moderation action all leave no trace, so the attack built from the flaws above cannot be seen or reconstructed afterwards. The AuditLog table exists but stays empty because nothing writes to it. flaw-5-before-1.png and flaw-5-after-1.png show the empty log and then the written record.
How to fix it: write an audit record for each of these events. The commented fix adds a small log_event helper that writes both to the Python logger and to an AuditLog row with the actor, the action, the target and the IP. The helper is called at every marked site. After the fix the same delete produces a log line and a database row.

To watch a single fix at work, uncomment the marked block for that flaw and comment the vulnerable lines above it, as the note in the code says. The screenshots folder holds a before and an after picture for each flaw.
