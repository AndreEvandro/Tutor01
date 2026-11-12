import sys
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.controllers.pedagogy_controller import PedagogyController

client = TestClient(app)

def test_homepage_redirect():
    """Verifica se a rota raiz redireciona para a página de login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_login_page_renders():
    """Garante que a tela de login está a ser renderizada corretamente."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Tutor Socrático" in response.text

def test_about_page_renders():
    """Valida que a página Sobre renderiza corretamente com as informações acadêmicas."""
    response = client.get("/sobre")
    assert response.status_code == 200
    assert "André Evandro Lourenço" in response.text
    assert "SIN5006" in response.text
    assert "Patrícia Rufino Oliveira" in response.text

def test_socratic_pedagogy_controller():
    """Valida a lógica do controlador pedagógico (OpenAI real ou Simulador local)."""
    # Teste Nível 1 - Socrático Estrito
    c1 = PedagogyController(max_help_level=1)
    res_1 = c1.process_interaction("Não entendi o laço while", help_level=1)
    
    assert res_1["level"] == 1
    assert len(res_1["response"]) > 0
    # Valida que o nível 1 gerou uma pergunta socrática ou resposta válida
    assert "?" in res_1["response"] or "Socrático" in res_1["response"] or "Nível 1" in res_1["response"]

    # Teste Nível 6 - ChatGPT Irrestrito
    c6 = PedagogyController(max_help_level=6)
    res_6 = c6.process_interaction("Quero o código pronto do laço while", help_level=6)
    
    assert res_6["level"] == 6
    assert len(res_6["response"]) > 0