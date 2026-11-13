import sys
from pathlib import Path

# Garante que o diretório raiz do projeto esteja no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient
from main import app
from app.controllers.pedagogy_controller import PedagogyController, DOMAIN_RESTRICTION_MESSAGE

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
    """Valida a lógica do controlador pedagógico para dúvidas válidas na disciplina."""
    # Teste Nível 1 - Socrático Estrito em Algoritmos
    c1 = PedagogyController(max_help_level=1)
    res_1 = c1.process_interaction("Não entendi o laço while", help_level=1)
    
    assert res_1["level"] == 1
    assert len(res_1["response"]) > 0
    assert DOMAIN_RESTRICTION_MESSAGE != res_1["response"]
    assert "?" in res_1["response"] or "Socrático" in res_1["response"] or "Nível 1" in res_1["response"]

    # Teste Nível 6 - ChatGPT Irrestrito em Algoritmos
    c6 = PedagogyController(max_help_level=6)
    res_6 = c6.process_interaction("Quero o código pronto do laço while", help_level=6)
    
    assert res_6["level"] == 6
    assert len(res_6["response"]) > 0
    assert DOMAIN_RESTRICTION_MESSAGE != res_6["response"]

def test_domain_restriction_off_topic_queries():
    """Garante que perguntas fora do escopo de Algoritmos e Estrutura de Dados são bloqueadas."""
    controller = PedagogyController(max_help_level=1)
    
    off_topic_prompts = [
        "Como fazer um bolo de chocolate?",
        "Quem descobriu o Brasil?",
        "Qual é a capital da França?",
        "Quem ganhou a última Copa do Mundo de futebol?",
        "Me conte uma piada engraçada",
        "Qual remédio tomar para dor de cabeça?",
        "Fale sobre a segunda guerra mundial",
        "Como investir em ações na bolsa de valores?"
    ]
    
    for prompt in off_topic_prompts:
        result = controller.process_interaction(prompt, help_level=1)
        assert result["response"] == DOMAIN_RESTRICTION_MESSAGE, f"Falhou para o prompt: {prompt}"

def test_domain_restriction_level_6_still_enforced():
    """Garante que mesmo no Nível 6 (livre), perguntas fora de Algoritmos e Estruturas de Dados são recusadas."""
    c6 = PedagogyController(max_help_level=6)
    result = c6.process_interaction("Receita de pizza de calabresa", help_level=6)
    assert result["response"] == DOMAIN_RESTRICTION_MESSAGE

def test_in_domain_data_structures_queries():
    """Valida que dúvidas legítimas de Algoritmos e Estruturas de Dados continuam sendo atendidas."""
    controller = PedagogyController(max_help_level=2)
    valid_prompts = [
        "Como funciona a inserção em uma árvore binária de busca?",
        "Qual a diferença entre pilha e fila?",
        "Como implementar o algoritmo de Dijkstra em um grafo?",
        "Qual a complexidade Big-O do QuickSort?",
        "int main() { printf(\"teste\"); return 0; }"
    ]
    
    for prompt in valid_prompts:
        res = controller.process_interaction(prompt, help_level=2)
        assert res["response"] != DOMAIN_RESTRICTION_MESSAGE, f"Falso positivo para: {prompt}"
