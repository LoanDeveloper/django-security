import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Order

from .forms import LoginForm, RegistrationForm
from .tokens import email_confirmation_token

logger = logging.getLogger("auth")
User = get_user_model()


def home_view(request: HttpRequest) -> HttpResponse:
    # Page d'accueil minimaliste qui affiche la navbar
    return render(request, "home.html")


@csrf_protect
def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            require_email_confirm = getattr(settings, "REQUIRE_EMAIL_CONFIRM", False)
            if require_email_confirm:
                user.is_active = False
            user.save()
            logger.info("New user registered: username=%s", user.username)
            # Envoi du lien de confirmation
            if require_email_confirm:
                from django.core.mail import send_mail
                from django.urls import reverse
                from django.utils.encoding import force_bytes
                from django.utils.http import urlsafe_base64_encode

                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token = email_confirmation_token.make_token(user)
                url = request.build_absolute_uri(reverse("confirm_email", args=[uidb64, token]))
                send_mail(
                    subject="Confirmez votre adresse email",
                    message=f"Bonjour {user.username}, cliquez pour confirmer: {url}",
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                messages.success(request, "Vérifiez votre email pour confirmer votre compte.")
            else:
                messages.success(request, "Inscription réussie. Vous pouvez vous connecter.")
            return redirect("login")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@csrf_protect
def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            password = form.cleaned_data["password"]
            user = authenticate(request, identifier=identifier, password=password)
            if user is not None and user.is_active:
                login(request, user)
                logger.info("User login: username=%s", user.username)
                return redirect("dashboard")
            messages.error(request, "Identifiants invalides")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        logger.info("User logout: username=%s", request.user.username)
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/dashboard.html")


def confirm_email_view(request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
    from django.utils.encoding import force_str
    from django.utils.http import urlsafe_base64_decode

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None
    if user and email_confirmation_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Email confirmé. Vous pouvez vous connecter.")
        return redirect("login")
    messages.error(request, "Lien invalide ou expiré")
    return redirect("home")


class RGPDExportView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "export"

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        data = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "date_joined": user.date_joined,
                "is_active": user.is_active,
            },
            "orders": [
                {
                    "id": o.id,
                    "product": o.product.name,
                    "quantity": o.quantity,
                    "created_at": o.created_at,
                }
                for o in orders
            ],
        }
        logger.info(f"[RGPD] Export demandé par user_id={user.id}")
        return Response(data)


class RGPDEraseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "erase"

    def post(self, request):
        user = request.user
        # Anonymisation des commandes
        Order.objects.filter(user=user).update(user=None)
        # Désactivation du compte
        user.is_active = False
        user.email = f"anon_{user.id}@example.com"
        user.username = f"anon_{user.id}"
        user.save(update_fields=["is_active", "email", "username"])
        logger.info(f"[RGPD] Suppression logique du compte user_id={user.id}")
        return Response(
            {"detail": "Compte désactivé et commandes anonymisées."}, status=status.HTTP_200_OK
        )


# Create your views here.
