from .models import Account


def current_account(request):
    aid = request.session.get("account_id")
    account = Account.objects.filter(id=aid).first() if aid else None
    return {"account": account}
