#!/usr/bin/env python3
import sqlite3
import sys

def check_users():
    try:
        conn = sqlite3.connect('blog/db/blog.db')
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Users table does not exist")
            return

        # Get users
        cursor.execute("SELECT id, username, email, is_redmine_user FROM users LIMIT 10;")
        users = cursor.fetchall()

        if users:
            print("Found users:")
            for user in users:
                print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Redmine User: {user[3]}")
        else:
            print("No users found in database")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()
