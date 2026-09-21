from django.urls import path

from . import views

urlpatterns = [
    path("", views.listView, name="home"),
    path("search", views.searchView, name="search"),
    path("petition/new", views.createView, name="create"),
    path("petition/<int:pid>/", views.detailView, name="detail"),
    path("petition/<int:pid>/edit", views.editView, name="edit"),
    path("petition/<int:pid>/delete", views.deleteView, name="delete"),
    path("petition/<int:pid>/signatures", views.signaturesView, name="signatures"),
    path("petition/<int:pid>/sign", views.signView, name="sign"),
    path("mod", views.moderationView, name="mod"),
    path("register", views.registerView, name="register"),
    path("login", views.loginView, name="login"),
    path("logout", views.logoutView, name="logout"),
]
