"""
Test suite for database functions.
Run with: python -m pytest tests/ -v
"""
import pytest
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    init_db, save_schedule, get_schedule, delete_schedule,
    set_chat_time, get_chat_time, toggle_weekend_mode, get_weekend_mode,
    migrate_chat_id, get_schedules_due_now, get_default_schedules_due,
    mark_schedule_sent, set_chat_language, get_chat_language
)


# Use a test database
TEST_DB = "test_schedules.db"


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup and teardown test database."""
    # Set test database path
    os.environ["DATABASE_FILE"] = TEST_DB
    
    # Initialize database
    init_db()
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestScheduleCRUD:
    """Test schedule create, read, update, delete operations."""
    
    def test_save_and_get_schedule(self):
        chat_id = -123456789
        file_id = "AgACAgIAAxkBAAIS_test_file_id"
        
        save_schedule(chat_id, file_id)
        result = get_schedule(chat_id)
        
        assert result == file_id
    
    def test_delete_schedule(self):
        chat_id = -123456789
        file_id = "test_file"
        
        save_schedule(chat_id, file_id)
        assert get_schedule(chat_id) == file_id
        
        delete_schedule(chat_id)
        assert get_schedule(chat_id) is None


class TestTimeSettings:
    """Test broadcast time settings."""
    
    def test_set_and_get_time(self):
        chat_id = -111111111
        time_str = "09:30"
        
        # First ensure schedule exists
        save_schedule(chat_id, "test_file")
        
        set_chat_time(chat_id, time_str)
        result = get_chat_time(chat_id)
        
        assert result == time_str


class TestWeekendMode:
    """Test weekend mode toggling."""
    
    def test_toggle_weekend_mode(self):
        chat_id = -222222222
        save_schedule(chat_id, "test_file")
        
        # Should be off by default
        assert get_weekend_mode(chat_id) == False
        
        # Toggle on
        new_val = toggle_weekend_mode(chat_id)
        assert new_val == 1
        assert get_weekend_mode(chat_id) == True
        
        # Toggle off
        new_val = toggle_weekend_mode(chat_id)
        assert new_val == 0
        assert get_weekend_mode(chat_id) == False


class TestChatMigration:
    """Test chat ID migration (group → supergroup)."""
    
    def test_migrate_chat_id(self):
        old_id = -333333333
        new_id = -1001333333333
        
        save_schedule(old_id, "test_file_migrate")
        set_chat_time(old_id, "10:00")
        
        # Verify old ID exists
        assert get_schedule(old_id) == "test_file_migrate"
        
        # Migrate
        migrate_chat_id(old_id, new_id)
        
        # Verify old ID no longer exists
        assert get_schedule(old_id) is None
        
        # Verify new ID has the data
        assert get_schedule(new_id) == "test_file_migrate"
        assert get_chat_time(new_id) == "10:00"


class TestScheduleDueQueries:
    """Test efficient schedule querying for broadcasts."""
    
    def test_get_schedules_due_now(self):
        chat_id = -444444444
        save_schedule(chat_id, "test_file")
        set_chat_time(chat_id, "08:00")
        
        # Query for matching time
        schedules = get_schedules_due_now("08:00", "2024-01-15", False)
        
        assert len(schedules) >= 1
        chat_ids = [s[0] for s in schedules]
        assert chat_id in chat_ids
    
    def test_no_duplicate_send(self):
        chat_id = -555555555
        current_date = "2024-01-15"
        
        save_schedule(chat_id, "test_file")
        set_chat_time(chat_id, "08:30")
        
        # Mark as sent
        mark_schedule_sent(chat_id, current_date)
        
        # Should not appear in due schedules for same day
        schedules = get_schedules_due_now("08:30", current_date, False)
        chat_ids = [s[0] for s in schedules]
        
        assert chat_id not in chat_ids


class TestLanguage:
    """Test language settings."""
    
    def test_set_and_get_language(self):
        chat_id = -666666666
        
        set_chat_language(chat_id, "EN")
        assert get_chat_language(chat_id) == "EN"
        
        set_chat_language(chat_id, "UZ")
        assert get_chat_language(chat_id) == "UZ"
    
    def test_default_language(self):
        # Non-existent chat should return default
        assert get_chat_language(-999999999) == "UZ"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
