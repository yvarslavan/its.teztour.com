#!/usr/bin/env python3
"""
Test script to create a temporary route for testing MyTasksApp without authentication
"""

from blog import create_app
from flask import render_template

app = create_app()

@app.route('/test-my-tasks')
def test_my_tasks():
    """Test route for MyTasksApp without authentication"""
    # Generate cache buster
    import time
    cache_buster = str(int(time.time()))

    return render_template("my_tasks.html",
                         title="Мои задачи (тест)",
                         count_notifications=0,
                         cache_buster=cache_buster,
                         show_kanban_tips=True)

if __name__ == "__main__":
    print("🧪 Starting test server for MyTasksApp...")
    print("📝 Test URL: http://localhost:5001/test-my-tasks")
    print("⚠️  This bypasses authentication for testing purposes only")
    app.run(host="127.0.0.1", port=5001, debug=True)
