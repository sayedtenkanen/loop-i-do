"""Tests for MemoryLayer - RED phase (failing tests)."""

from loop_engineering.memory import LoopState, MemoryLayer


class TestLoopState:
    """Tests for LoopState dataclass."""

    def test_loop_state_creation(self):
        state = LoopState(
            loop_id="loop-1",
            status="running",
            task="Fix bug",
        )
        assert state.loop_id == "loop-1"
        assert state.status == "running"

    def test_loop_state_defaults(self):
        state = LoopState(loop_id="loop-1", status="idle", task="Test")
        assert state.attempts == 0
        assert state.result is None


class TestMemoryLayer:
    """Tests for MemoryLayer class."""

    def test_memory_creation(self, tmp_path):
        db_path = tmp_path / "test.db"
        memory = MemoryLayer(db_path=str(db_path))
        assert memory is not None

    def test_memory_save_and_load(self, tmp_path):
        db_path = tmp_path / "test.db"
        memory = MemoryLayer(db_path=str(db_path))

        state = LoopState(loop_id="loop-1", status="running", task="Fix bug")
        memory.save(state)

        loaded = memory.load("loop-1")
        assert loaded is not None
        assert loaded.loop_id == "loop-1"
        assert loaded.status == "running"

    def test_memory_load_nonexistent(self, tmp_path):
        db_path = tmp_path / "test.db"
        memory = MemoryLayer(db_path=str(db_path))

        loaded = memory.load("nonexistent")
        assert loaded is None

    def test_memory_update_status(self, tmp_path):
        db_path = tmp_path / "test.db"
        memory = MemoryLayer(db_path=str(db_path))

        state = LoopState(loop_id="loop-1", status="running", task="Fix bug")
        memory.save(state)

        memory.update_status("loop-1", "completed")
        loaded = memory.load("loop-1")
        assert loaded.status == "completed"

    def test_memory_list_loops(self, tmp_path):
        db_path = tmp_path / "test.db"
        memory = MemoryLayer(db_path=str(db_path))

        memory.save(LoopState(loop_id="loop-1", status="running", task="Task 1"))
        memory.save(LoopState(loop_id="loop-2", status="idle", task="Task 2"))

        loops = memory.list_loops()
        assert len(loops) == 2
