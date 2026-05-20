# Tests end-to-end para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria compartido entre conexiones del mismo test
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# --- helpers ---

def _create_task(client, **kwargs):
    payload = {"title": "Tarea de prueba", **kwargs}
    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == 201
    return resp.json()


# --- tests de update_task con tareas completadas ---

def test_update_task_with_done_status_returns_400(client):
    """PATCH sobre una tarea con status 'done' debe devolver 400."""
    task = _create_task(client, status="done")
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "Nuevo titulo"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_task_with_pending_status_succeeds(client):
    """PATCH sobre una tarea con status 'pending' debe aplicar los cambios."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "Titulo actualizado"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Titulo actualizado"


def test_update_task_transition_to_done_from_pending(client):
    """Pasar una tarea de 'pending' a 'done' debe funcionar correctamente."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_update_done_task_even_with_status_field_returns_400(client):
    """Intentar cambiar el status de una tarea ya completada debe devolver 400."""
    task = _create_task(client, status="done")
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "pending"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_task_not_found_returns_404(client):
    """PATCH sobre un id inexistente debe devolver 404."""
    resp = client.patch("/tasks/9999", json={"title": "No existe"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"
