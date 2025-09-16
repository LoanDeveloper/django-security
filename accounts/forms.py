from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    accept_cgu = forms.BooleanField(required=True, label="J'accepte les CGU")
    # Champ honeypot anti-bot
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"autocomplete": "off"}))

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            # Message générique pour anti-enumeration
            raise forms.ValidationError("Inscription impossible avec ces informations")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            # Message générique pour anti-enumeration
            raise forms.ValidationError("Inscription impossible avec ces informations")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            # Honeypot rempli => considérer comme invalide
            raise forms.ValidationError("Inscription impossible avec ces informations")
        return cleaned


class LoginForm(forms.Form):
    identifier = forms.CharField(label="Nom d'utilisateur ou email")
    password = forms.CharField(widget=forms.PasswordInput)
