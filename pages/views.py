"""views for the petition portal"""

import hashlib

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.db import connection

from .models import Petition, Account, Signature, AuditLog


# === FLAW 2 (A02 Cryptographic Failures) ================================
# passwords are stored as unsalted md5. md5 is fast and broken, so a leaked
# hash falls to a rainbow table or a wordlist in seconds (see FLAW 3, which
# leaks exactly these hashes).
def hash_pw(pw: str) -> str:
    return hashlib.md5(pw.encode()).hexdigest()


def verify_pw(pw: str, stored: str) -> bool:
    return hash_pw(pw) == stored
# === FIX (uncomment, comment out the two functions above) ===============
# from django.contrib.auth.hashers import make_password, check_password
# def hash_pw(pw: str) -> str:
#     return make_password(pw)          # pbkdf2_sha256, salted, many rounds
# def verify_pw(pw: str, stored: str) -> bool:
#     return check_password(pw, stored)
# ========================================================================


# === FLAW 5 (A09 Security Logging and Monitoring Failures) ==============
# nothing security-relevant is recorded: failed logins (FLAW 4), cross-user
# deletes (FLAW 1) and moderation actions all leave no trace, so an attack is
# invisible afterwards. the call sites below are marked but commented out.
# === FIX (uncomment this helper and every log_event(...) call marked below) =
# import logging
# audit_logger = logging.getLogger("petitio.audit")
# def log_event(request, action, target):
#     actor = str(request.session.get("account_id", "anon"))
#     ip = request.META.get("REMOTE_ADDR", "?")
#     audit_logger.warning("actor=%s action=%s target=%s ip=%s", actor, action, target, ip)
#     AuditLog.objects.create(actor=actor, action=action, target=target, ip=ip)
# =======================================================================


def _current(request):
    aid = request.session.get("account_id")
    return Account.objects.filter(id=aid).first() if aid else None


def listView(request):
    petitions = Petition.objects.filter(status="open").order_by("-created_at")
    return render(request, "pages/list.html", {"petitions": petitions})


def detailView(request, pid):
    petition = get_object_or_404(Petition, id=pid)
    return render(request, "pages/detail.html", {"petition": petition})


def searchView(request):
    q = request.GET.get("q", "")
    results = []
    if q:
        # === FLAW 3 (A03 Injection) =====================================
        # q is pasted straight into the SQL string. a crafted q breaks out
        # of the quotes, e.g.
        #   ' UNION SELECT username, password_hash FROM pages_account --
        # which dumps every account next to the weak md5 hashes from FLAW 2.
        sql = "SELECT id, title FROM pages_petition WHERE title LIKE '%%%s%%'" % q
        with connection.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
        # === FIX (uncomment, comment the five lines above) ==============
        # results = list(Petition.objects.filter(title__icontains=q).values_list("id", "title"))
        # ================================================================
    return render(request, "pages/search.html", {"q": q, "results": results})


def createView(request):
    account = _current(request)
    if account is None:
        return redirect("/login")
    if request.method == "POST":
        Petition.objects.create(owner=account, title=request.POST.get("title", ""), body=request.POST.get("body", ""))
        return redirect("/")
    return render(request, "pages/new.html")


def editView(request, pid):
    account = _current(request)
    if account is None:
        return redirect("/login")
    petition = get_object_or_404(Petition, id=pid)
    # === FLAW 1 (A01 Broken Access Control) =============================
    # checks only that *someone* is logged in, not that they own this
    # petition. any user can edit any petition by opening its edit url.
    # === FIX (uncomment) ================================================
    # if petition.owner_id != account.id and not account.is_moderator:
    #     return HttpResponseForbidden("not your petition")
    # ====================================================================
    if request.method == "POST":
        petition.title = request.POST.get("title", petition.title)
        petition.body = request.POST.get("body", petition.body)
        petition.save()
        return redirect("/petition/%d/" % petition.id)
    return render(request, "pages/edit.html", {"petition": petition})


def deleteView(request, pid):
    account = _current(request)
    if account is None:
        return redirect("/login")
    petition = get_object_or_404(Petition, id=pid)
    # === FLAW 1 (A01 Broken Access Control), same gap as editView =======
    # === FIX (uncomment) ================================================
    # if petition.owner_id != account.id and not account.is_moderator:
    #     return HttpResponseForbidden("not your petition")
    # ====================================================================
    # FLAW 5 (A09): this delete is not recorded
    # log_event(request, "petition_delete", str(pid))
    petition.delete()
    return redirect("/")


def signaturesView(request, pid):
    account = _current(request)
    if account is None:
        return redirect("/login")
    petition = get_object_or_404(Petition, id=pid)
    # === FLAW 1 (A01 Broken Access Control) =============================
    # the signer list holds names and e-mails. any logged-in user can read
    # any petition's signers, not just the owner.
    # === FIX (uncomment) ================================================
    # if petition.owner_id != account.id and not account.is_moderator:
    #     return HttpResponseForbidden()
    # ====================================================================
    return render(request, "pages/signatures.html", {"petition": petition, "sigs": petition.signatures.all()})


def signView(request, pid):
    petition = get_object_or_404(Petition, id=pid)
    if request.method == "POST":
        Signature.objects.create(petition=petition, signer_name=request.POST.get("name", ""), signer_email=request.POST.get("email", ""))
    return redirect("/petition/%d/" % petition.id)


def moderationView(request):
    account = _current(request)
    if account is None or not account.is_moderator:
        return HttpResponseForbidden()
    if request.method == "POST":
        pid = request.POST.get("pid")
        action = request.POST.get("action")
        petition = get_object_or_404(Petition, id=pid)
        if action == "close":
            petition.status = "closed"
            petition.save()
            # FLAW 5 (A09): moderation action not recorded
            # log_event(request, "mod_close", str(petition.id))
        elif action == "delete":
            # log_event(request, "mod_delete", str(pid))
            petition.delete()
        return redirect("/mod")
    petitions = Petition.objects.all().order_by("-created_at")
    return render(request, "pages/mod.html", {"petitions": petitions})


def registerView(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            error = "username and password required"
        elif Account.objects.filter(username=username).exists():
            error = "username taken"
        else:
            # === FLAW 4 (A07): no password policy, anything goes ===
            # === FIX (uncomment): enforce a minimum length ===
            # if len(password) < 10:
            #     return render(request, "pages/register.html", {"error": "password too short"})
            acc = Account.objects.create(username=username, email=email, password_hash=hash_pw(password))
            request.session["account_id"] = acc.id
            return redirect("/")
    return render(request, "pages/register.html", {"error": error})


def loginView(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        account = Account.objects.filter(username=username).first()

        # === FLAW 4 (A07 Identification and Authentication Failures) ====
        # no rate limiting at all: passwords can be tried endlessly, a plain
        # brute force (failed_logins is tracked but ignored).
        if account and verify_pw(password, account.password_hash):
            request.session["account_id"] = account.id
            return redirect("/")
        error = "login failed"
        # FLAW 5 (A09): this failed login is not recorded
        # log_event(request, "login_failed", username)
        # === FIX (uncomment this block and comment the four lines above) =
        # if account and account.failed_logins >= 5:
        #     error = "too many attempts, account locked"
        # elif account and verify_pw(password, account.password_hash):
        #     account.failed_logins = 0
        #     account.save()
        #     request.session["account_id"] = account.id
        #     return redirect("/")
        # elif account:
        #     account.failed_logins += 1
        #     account.save()
        #     error = "login failed"
        # ================================================================
    return render(request, "pages/login.html", {"error": error})


def logoutView(request):
    request.session.flush()
    return redirect("/")
