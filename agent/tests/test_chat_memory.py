"""Unit tests for bounded conversation memory (Phase 5)."""

from app.chat.conversation import Conversation, ConversationTurn, resolve_query
from app.chat.memory import MemoryStore
from app.chat.models import ChatReference


def _turn(question="q", intent="explain_code", refs=(), search_query="") -> ConversationTurn:
    return ConversationTurn(
        question=question,
        intent=intent,  # type: ignore[arg-type]
        answer="a",
        references=list(refs),
        search_query=search_query,
    )


def _ref(path="src/utils.py", start=1, end=2) -> ChatReference:
    return ChatReference(file_path=path, start_line=start, end_line=end)


def test_conversation_appends_and_bounds_turns():
    conv = Conversation("c1", max_turns=3)
    for i in range(5):
        conv.append(_turn(question=f"q{i}"))
    assert len(conv.turns) == 3
    assert conv.turns[-1].question == "q4"
    assert conv.turns[0].question == "q2"


def test_conversation_recent_questions_keeps_last_three():
    conv = Conversation("c1", max_turns=10)
    for i in range(6):
        conv.append(_turn(question=f"q{i}"))
    assert conv.recent_questions == ["q3", "q4", "q5"]


def test_conversation_last_turn():
    conv = Conversation("c1")
    assert conv.last_turn is None
    conv.append(_turn(question="q1"))
    assert conv.last_turn is not None
    assert conv.last_turn.question == "q1"


def test_conversation_references_deduplicated():
    conv = Conversation("c1")
    conv.append(_turn(refs=[_ref("a.py", 1, 2)]))
    conv.append(_turn(refs=[_ref("a.py", 1, 2), _ref("b.py", 3, 4)]))
    assert len(conv.references) == 2


def test_memory_store_create_get_ensure():
    store = MemoryStore(max_turns=5)
    cid = store.create_conversation()
    assert store.get(cid) is not None
    assert store.get(cid).conversation_id == cid
    assert store.get("missing") is None
    assert store.ensure("other").conversation_id == "other"
    assert store.conversations == 2


def test_memory_store_ids_unique():
    store = MemoryStore()
    ids = {store.create_conversation() for _ in range(20)}
    assert len(ids) == 20


def test_memory_store_append_creates_and_bounds():
    store = MemoryStore(max_turns=2)
    cid = store.create_conversation()
    for i in range(4):
        store.append(cid, _turn(question=f"q{i}"))
    conv = store.get(cid)
    assert conv is not None
    assert [t.question for t in conv.turns] == ["q2", "q3"]
    assert store.memory_turns == 2


def test_memory_store_clear():
    store = MemoryStore()
    store.create_conversation()
    store.create_conversation()
    assert store.conversations == 2
    store.clear()
    assert store.conversations == 0
    assert store.memory_turns == 0


def test_memory_store_thread_safety():
    import threading

    store = MemoryStore(max_turns=10)
    errors: list[Exception] = []

    def worker():
        try:
            cid = store.create_conversation()
            for i in range(20):
                store.append(cid, _turn(question=f"q{i}"))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert store.conversations == 8
    assert store.memory_turns == 80


def test_resolve_query_returns_subject_first():
    query, used = resolve_query("Question", "dealer approval", None)
    assert (query, used) == ("dealer approval", False)


def test_resolve_query_followup_reuses_previous_turn():
    previous = _turn(search_query="token refresh")
    query, used = resolve_query("what about it?", "", previous)
    assert (query, used) == ("token refresh", True)


def test_resolve_query_previous_turn_without_query_falls_back():
    previous = _turn(search_query="")
    query, used = resolve_query("what about it?", "", previous)
    assert (query, used) == ("what about it?", False)
