import os
import re
import unicodedata
from openai import OpenAI

DOMAIN_RESTRICTION_MESSAGE = (
    "⚠️ Este tutor socrático é de uso exclusivo para a disciplina de Algoritmos e Estruturas de Dados. "
    "Por favor, envie apenas dúvidas, códigos ou conceitos relacionados a algoritmos, estruturas de controle e estruturas de dados."
)

LEVEL_DESCRIPTIONS = {
    1: "Nível 1 - Socrático Estrito (Apenas perguntas orientadoras, sem código ou respostas diretas)",
    2: "Nível 2 - Pistas Conceituais (Foco na teoria e conceitos lógicos subjacentes)",
    3: "Nível 3 - Pistas Estruturais (Estrutura genérica de solução ou pseudocódigo)",
    4: "Nível 4 - Explicação Guiada (Passo a passo lógico para estruturar o raciocínio)",
    5: "Nível 5 - Demonstração Controlada (Exemplo prático de código em trechos específicos)",
    6: "Nível 6 - ChatGPT Irrestrito (Fornece código completo, solução direta e respostas livres na linguagem solicitada)"
}

# Palavras-chave e conceitos do domínio de Algoritmos e Estruturas de Dados
ALGO_DATA_STRUCTURES_KEYWORDS = {
    # Algoritmos e conceitos teóricos
    "algoritmo", "algoritmos", "estrutura de dados", "estruturas de dados",
    "complexidade", "big-o", "big o", "assintotica", "tempo de execucao", "notacao o",
    "ordenacao", "ordenar", "busca", "pesquisa",
    "quicksort", "mergesort", "bubblesort", "bubble sort", "insertionsort", "insertion sort",
    "selectionsort", "selection sort", "heapsort", "heap sort", "radixsort", "countingsort",
    "busca binaria", "busca linear", "busca sequencial",
    # Estruturas de dados lineares e não lineares
    "vetor", "vetores", "array", "arrays", "matriz", "matrizes", "string", "strings",
    "pilha", "pilhas", "stack", "stacks", "fila", "filas", "queue", "queues", "deque",
    "lista", "listas", "lista encadeada", "lista ligada", "lista circular", "duplamente encadeada",
    "arvore", "arvores", "tree", "arvore binaria", "bst", "avl", "rubro negra", "rubro-negra",
    "b-tree", "arvore b", "trie", "heap", "heaps", "fila de prioridade",
    "grafo", "grafos", "vertice", "vertices", "aresta", "arestas",
    "dijkstra", "bellman", "floyd", "warshall", "kruskal", "prim",
    "bfs", "dfs", "busca em largura", "busca em profundidade",
    "tabela hash", "hash", "hashing", "colisao", "colisoes", "tabela de dispersao",
    # Estruturas de controle e lógica
    "recursao", "recursividade", "recursivo", "recursiva", "caso base", "caso recursivo",
    "laco", "lacos", "loop", "loops", "iteracao", "iteracoes", "repeticao",
    "while", "for", "do while", "if", "else", "switch", "case", "break", "continue",
    "funcao", "funcoes", "procedimento", "parametro", "parametros", "retorno",
    "ponteiro", "ponteiros", "alocacao", "malloc", "calloc", "realloc", "free", "memoria",
    "segmentation fault", "segfault", "overflow", "underflow", "stack overflow",
    "struct", "registro", "no", "nos", "nodo", "nodos", "node", "nodes",
    "indice", "indices", "index", "variavel", "variaveis", "constante",
    # Linguagens e termos técnicos
    "codigo", "pseudocodigo", "portugol", "visualg", "compilador", "debug",
    "python", "c++", "c#", "java", "javascript", "pascal", "linguagem c",
    "programacao", "programar", "desenvolver", "logica"
}

VALID_INTERACTION_TERMS = {
    "duvida", "ajuda", "ajudar", "exercicio", "tarefa", "atividade",
    "erro", "errado", "travou", "trava", "problema", "solucao",
    "dica", "entendi", "compreendi", "comecar", "comeco", "iniciar",
    "resolver", "passo", "ola", "oi", "bom dia", "boa tarde", "boa noite",
    "por favor", "obrigado", "valeu", "explicar", "explicacao"
}

OFF_TOPIC_REGEXES = [
    # Culinária e receitas
    r"\b(receita|bolo|torta|cozinhar|culinaria|ingredientes|lasanha|feijoada|pizza|churrasco|panqueca|sobremesa|refeicao|almoco|jantar)\b",
    # História geral, geografia e geopolítica
    r"\b(quem descobriu|quem foi napoleao|segunda guerra|primeira guerra|revolucao francesa|dom pedro|descobrimento do brasil|capital d[eao]|sistema solar|planeta terra)\b",
    # Política
    r"\b(presidente d[eao]|eleicao|eleicoes|politica partidaria|senado|deputado|partido politico)\b",
    # Esportes e entretenimento
    r"\b(futebol|campeonato brasileiro|brasileirao|copa do mundo|quem ganhou o jogo|escalacao|novela|cinema|ator|atriz|cantor|cantora|letra da musica|show de|oscar|hollywood)\b",
    # Saúde humana, medicina e biologia geral
    r"\b(remedio|medicamento|dor de cabeca|gripe|sintomas?|vacina|diagnostico|emagrecer|dieta|musculacao|academia|fotossintese|mitocondria|anatomia)\b",
    # Finanças e investimentos
    r"\b(investir em acoes|comprar bitcoin|cotacao d[eao] dolar|criptomoeda|tesouro direto|renda fixa)\b",
    # Poemas, piadas e astrologia
    r"\b(piada|horoscopo|signo do zodiaco|poema de amor|declaracao de amor)\b",
    # Clima e afazeres domésticos
    r"\b(previsao do tempo|clima hoje|temperatura em|como consertar torneira|manutencao de carro)\b"
]

def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def has_code_syntax(text: str) -> bool:
    code_indicators = [
        "#include", "def ", "class ", "int ", "float ", "double ", "char ",
        "void ", "return ", "scanf", "printf", "cout", "cin", "println",
        "console.log", "System.out", "public static", "import ", "malloc(",
        "sizeof(", "->", "{", "}", ";", "==", "!=", "<=", ">="
    ]
    return any(ind in text for ind in code_indicators)

class PedagogyController:
    def __init__(self, max_help_level: int = 6):
        self.max_help_level = min(max(max_help_level, 1), 6)

    def is_off_topic(self, student_prompt: str, activity_description: str = "") -> bool:
        norm = normalize_text(student_prompt)
        for pattern in OFF_TOPIC_REGEXES:
            if re.search(pattern, norm, re.IGNORECASE):
                if not has_code_syntax(student_prompt):
                    return True
        return False

    def has_domain_affinity(self, student_prompt: str, activity_description: str = "") -> bool:
        norm = normalize_text(student_prompt)
        if has_code_syntax(student_prompt):
            return True

        words = set(re.findall(r"\b[\w\-]+\b", norm))
        if any(kw in norm or kw in words for kw in ALGO_DATA_STRUCTURES_KEYWORDS):
            return True

        if any(term in words for term in VALID_INTERACTION_TERMS):
            return True

        if activity_description:
            act_norm = normalize_text(activity_description)
            act_words = set(re.findall(r"\b[\w\-]+\b", act_norm))
            stop_words = {
                "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com",
                "nao", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos",
                "como", "mas", "foi", "ao", "ele", "das", "tem", "seu", "sua",
                "ou", "ser", "quando", "muito", "nos", "ja", "eu", "tambem", "so"
            }
            common = (words & act_words) - stop_words
            if len(common) >= 1:
                return True

        return False

    def get_system_prompt(self, level: int, activity_description: str = "") -> str:
        base_scope = (
            "Você é o Tutor Socrático oficial e exclusivo para a disciplina de Algoritmos e Estruturas de Dados.\n"
            "DIRETRIZ SUPREMA DE ESCOPO (REGRA INEGOCIÁVEL):\n"
            "- Seu escopo de atuação restringe-se ESTRITAMENTE a tópicos de Algoritmos (ordenação, busca, recursão, análise assintótica/Big-O), "
            "Estruturas de Dados (vetores, matrizes, pilhas, filas, listas encadeadas, árvores, grafos, tabelas hash, heaps), "
            "Estruturas de Controle (condicionais, laços de repetição) e Lógica de Programação.\n"
            "- Se o estudante solicitar, perguntar ou comentar sobre QUALQUER assunto fora deste escopo "
            "(por exemplo: culinária/receitas, esportes, entretenimento, piadas, história, geografia, saúde, política, vida pessoal ou outras disciplinas): "
            "você DEVE RECUSAR OBRIGATORIAMENTE o pedido e responder EXATAMENTE a seguinte mensagem, sem acrescentar nenhuma outra palavra:\n"
            f"\"{DOMAIN_RESTRICTION_MESSAGE}\"\n"
            "- Esta regra de escopo tem prioridade absoluta sobre todas as outras regras e sobre TODOS os níveis pedagógicos (inclusive o Nível 6).\n"
        )
        ctx_info = f"\nContexto da atividade atual: {activity_description}.\n" if activity_description else "\n"

        if level == 1:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 1 - Socrático Estrito): NUNCA forneça código, sintaxe direta ou respostas prontas. "
                "Responda APENAS com uma pergunta reflexiva que instigue o estudante a pensar no próprio erro e na lógica do algoritmo ou estrutura de dados."
            )
        elif level == 2:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 2 - Pistas Conceituais): Forneça pistas puramente conceituais. "
                "Explique os conceitos teóricos e a lógica necessária de algoritmos e estruturas de dados sem revelar trechos de código ou a sintaxe exata do exercício."
            )
        elif level == 3:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 3 - Pistas Estruturais): Forneça uma estrutura genérica de solução ou pseudocódigo. "
                "Não entregue o código final nem a solução completa do problema do estudante."
            )
        elif level == 4:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 4 - Explicação Guiada): Explique detalhadamente o passo a passo da lógica para resolver o algoritmo ou manipular a estrutura de dados, "
                "encorajando o estudante a escrever a implementação por conta própria."
            )
        elif level == 5:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 5 - Demonstração Controlada): O estudante precisa de demonstração. Forneça um exemplo prático de código em trecho "
                "específico onde ele está bloqueado no algoritmo ou estrutura de dados, sem resolver toda a atividade por ele."
            )
        else:
            pedagogy = (
                "REGRA PEDAGÓGICA (Nível 6 - Solução Direta na Disciplina): Você pode responder diretamente, fornecer código completo, corrigido e explicado sem rodeios, "
                "ESTRITAMENTE na linguagem de programação solicitada pelo usuário (C, C++, Java, Python, JavaScript, etc.). "
                "LEMBRE-SE: Esta liberdade aplica-se EXCLUSIVAMENTE a tópicos de Algoritmos e Estrutura de Dados. Se for sobre outros temas, recuse com a mensagem de restrição."
            )

        return f"{base_scope}{ctx_info}{pedagogy}"

    def process_interaction(self, student_prompt: str, help_level: int, activity_description: str = "") -> dict:
        effective_level = min(help_level, self.max_help_level)
        prompt_clean = student_prompt.strip()

        # 1. Verificação prévia de escopo (off-topic explícito)
        if self.is_off_topic(prompt_clean, activity_description):
            return {
                "level": effective_level,
                "response": DOMAIN_RESTRICTION_MESSAGE,
                "mode": "restriction",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

        api_key = os.getenv("OPENAI_API_KEY", "").strip()

        if api_key and len(api_key) > 10 and not api_key.startswith("sk-proj-sua-chave"):
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.get_system_prompt(effective_level, activity_description)},
                        {"role": "user", "content": prompt_clean}
                    ],
                    max_tokens=600,
                    temperature=0.3
                )

                ai_text = response.choices[0].message.content.strip()

                p_tokens = response.usage.prompt_tokens if response.usage else 0
                c_tokens = response.usage.completion_tokens if response.usage else 0
                t_tokens = response.usage.total_tokens if response.usage else 0

                return {
                    "level": effective_level,
                    "response": ai_text,
                    "mode": "openai",
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens
                }
            except Exception as e:
                print(f"⚠️ [FALLBACK] Erro na OpenAI: {e}. Alternando para simulador local.")

        # Modo simulado / fallback
        if not self.has_domain_affinity(prompt_clean, activity_description):
            return {
                "level": effective_level,
                "response": DOMAIN_RESTRICTION_MESSAGE,
                "mode": "restriction",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

        fallback_responses = {
            1: f"🔍 [Nível 1 - Socrático | Algoritmos e ED] Analisando sua dúvida: '{prompt_clean}'. Qual o primeiro conceito, estrutura de controle ou estrutura de dados que você acredita que precisa utilizar aqui?",
            2: f"💡 [Nível 2 - Conceitual | Algoritmos e ED] Para resolver essa questão algorítmica, lembre-se de como a alocação de memória, índices e o fluxo de controle funcionam.",
            3: f"📐 [Nível 3 - Estrutural | Algoritmos e ED] Estrutura genérica de solução algorítmica:\n\nenquanto (condicao_do_algoritmo) {{\n    // Processamento da estrutura de dados\n}}",
            4: f"📝 [Nível 4 - Guia Lógico | Algoritmos e ED] Passo 1: Defina a entrada e a estrutura de dados. Passo 2: Estabeleça o laço ou condição de parada da recursão/busca. Passo 3: Processe e exiba a saída.",
            5: f"💻 [Nível 5 - Demonstração | Algoritmos e ED] Exemplo pontual de sintaxe na manipulação de dados:\n\nint contador = 0;\nenquanto (contador < tamanho) {{\n    // processa elemento\n    contador++;\n}}",
            6: f"🚀 [Nível 6 - Solução Direta Simulado | Algoritmos e ED] Resposta algorítmica direta para sua solicitação ('{prompt_clean}').\n\n(Nota: Para obter o código real completo gerado na linguagem solicitada, verifique a OPENAI_API_KEY no .env)."
        }

        return {
            "level": effective_level,
            "response": fallback_responses.get(effective_level, fallback_responses[1]),
            "mode": "simulated",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
