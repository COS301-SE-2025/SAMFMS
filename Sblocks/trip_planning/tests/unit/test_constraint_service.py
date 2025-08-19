import pytest
from types import SimpleNamespace

class _Constraint(SimpleNamespace): pass

@pytest.mark.asyncio
async def test_update_trip_constraints_writes_array(fake_db):
    from services.constraint_service import ConstraintService
    svc = ConstraintService(); svc.db = fake_db
    svc.get_trip_constraints = AsyncMock(return_value=[
        _Constraint(dict=lambda: {"a":1}), _Constraint(dict=lambda: {"b":2})
    ])
    await svc._update_trip_constraints("507f1f77bcf86cd799439011") 
    fake_db.trips.update_one.assert_awaited()

def test_get_constraint_templates_nonempty():
    from services.constraint_service import ConstraintService
    out = asyncio.get_event_loop().run_until_complete(ConstraintService().get_constraint_templates())
    assert isinstance(out, list) and len(out) >= 1 