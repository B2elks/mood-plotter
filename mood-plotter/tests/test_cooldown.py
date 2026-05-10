import time
from pathlib import Path

import pytest

from cooldown import Cooldown


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "cooldown.db"


def test_cooldown_allows_first_call(db_path):
    cd = Cooldown(db_path, seconds=300)
    assert cd.try_acquire() is True


def test_cooldown_blocks_second_call_within_window(db_path):
    cd = Cooldown(db_path, seconds=300)
    cd.try_acquire()
    assert cd.try_acquire() is False


def test_cooldown_allows_after_window(db_path):
    cd = Cooldown(db_path, seconds=1)
    cd.try_acquire()
    time.sleep(1.1)
    assert cd.try_acquire() is True


def test_cooldown_release_clears_lock(db_path):
    cd = Cooldown(db_path, seconds=300)
    cd.try_acquire()
    cd.release()
    assert cd.try_acquire() is True


def test_cooldown_persists_across_instances(db_path):
    cd1 = Cooldown(db_path, seconds=300)
    cd1.try_acquire()
    cd2 = Cooldown(db_path, seconds=300)
    assert cd2.try_acquire() is False
