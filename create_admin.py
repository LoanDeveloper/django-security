#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    """Crée un utilisateur admin"""
    try:
        if User.objects.filter(username='admin').exists():
            print("✅ Utilisateur admin existe déjà")
            return
        
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("✅ Utilisateur admin créé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    create_admin()
