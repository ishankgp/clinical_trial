import asyncio
import pytest
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))

from mcp.clinical_trial_mcp_server import ClinicalTrialMCPServer

class DummyDB:
    def __init__(self):
        self.received_filters = None
    def search_trials(self, filters, limit):
        self.received_filters = filters
        return []

def make_server():
    server = ClinicalTrialMCPServer.__new__(ClinicalTrialMCPServer)
    server.db = DummyDB()
    return server

@pytest.mark.asyncio
async def test_perform_search_uses_llm_filters():
    server = make_server()

    async def fake_parse(query):
        return {"filters": {"indication": ["diabetes"]}}

    server._parse_natural_language_query = fake_parse

    await server._perform_search("find diabetes", {"trial_phase": "PHASE3"}, 10)

    assert server.db.received_filters == {"indication": ["diabetes"], "trial_phase": "PHASE3"}
