#!/usr/bin/env python3
"""
Временный скрипт для установки Firebase Admin SDK
"""

import subprocess
import sys
import os

def install_firebase_admin():
    """Установка Firebase Admin SDK"""
    try:
        print("🔧 Установка Firebase Admin SDK...")

        # Команды для установки
        commands = [
            [sys.executable, '-m', 'pip', 'install', 'firebase-admin==6.4.0'],
            [sys.executable, '-m', 'pip', 'install', 'google-cloud-firestore'],
            [sys.executable, '-m', 'pip', 'install', 'google-cloud-messaging']
        ]

        for cmd in commands:
            print(f"Выполняю: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Успешно: {cmd[-1]}")
            else:
                print(f"❌ Ошибка: {result.stderr}")

        # Проверка установки
        try:
            import firebase_admin
            print(f"🎉 Firebase Admin SDK установлен! Версия: {firebase_admin.__version__}")
            return True
        except ImportError:
            print("❌ Firebase Admin SDK не удалось импортировать")
            return False

    except Exception as e:
        print(f"❌ Ошибка при установке: {e}")
        return False

if __name__ == "__main__":
    success = install_firebase_admin()
    if success:
        print("\n🚀 Теперь можно перезапустить Flask приложение!")
    else:
        print("\n⚠️ Установка не удалась. Попробуйте вручную в IDE.")
