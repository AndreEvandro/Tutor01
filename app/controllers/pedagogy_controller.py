import os
from openai import OpenAI

LEVEL_DESCRIPTIONS = {
    1: "Nível 1 - Socrático Estrito (Apenas perguntas orientadoras, sem código ou respostas diretas)",
    2: "Nível 2 - Pistas Conceituais (Foco na teoria e conceitos lógicos subjacentes)",
    3: "Nível 3 - Pistas Estruturais (Estrutura genérica de solução ou pseudocódigo)",
    4: "Nível 4 - Explicação Guiada (Passo a passo lógico para estruturar o raciocínio)",
    5: "Nível 5 - Demonstração Controlada (Exemplo prático de código em trechos específicos)",
    6: "Nível 6 - ChatGPT Irrestrito (Fornece código completo, solução direta e respostas livres na linguagem solicitada)"
}

class PedagogyController:
    def __init__(self, max_help_level: int = 6):
        self.max_help_level = min(max(max_help_level, 1), 6)

    def get_system_prompt(self, level: int, activity_description: str = "") -> str:
        base_prompt = "Você é um Tutor Pedagógico especialista em programação e ciência da computação."
        ctx_info = f" Contexto da atividade: {activity_description}." if activity_description else ""

        if level == 1:
            return (
                f"{base_prompt}{ctx_info} "
                "REGRA RÍGIDA: NUNCA forneça código, sintaxe direta ou respostas completas. "
                "Responda APENAS com uma pergunta reflexiva que instigue o estudante a pensar no próprio erro e na lógica."
            )
        elif level == 2:
            return (
                f"{base_prompt}{ctx_info} "
                "Forneça pistas puramente conceituais. Explique os conceitos teóricos e a lógica necessária "
                "sem revelar trechos de código ou a sintaxe exata do exercício."
            )
        elif level == 3:
            return (
                f"{base_prompt}{ctx_info} "
                "Forneça uma estrutura genérica de solução ou pseudocódigo. "
                "Não entregue o código final nem a solução completa do problema do estudante."
            )
        elif level == 4:
            return (
                f"{base_prompt}{ctx_info} "
                "Explique detalhadamente o passo a passo da lógica para resolver o problema, "
                "encorajando o estudante a escrever a implementação por conta própria."
            )
        elif level == 5:
            return (
                f"{base_prompt}{ctx_info} "
                "O estudante precisa de demonstração. Forneça um exemplo prático de código em trecho "
                "específico onde ele está bloqueado, sem resolver toda a atividade por ele."
            )
        else:
            return (
                "Você é um assistente de programação ilimitado (estilo ChatGPT livre). "
                "Responda diretamente, forneça o código completo, corrigido e explicado sem rodeios. "
                "REGRA FUNDAMENTAL DE LINGUAGEM: Responda ESTRITAMENTE na linguagem de programação solicitada pelo usuário "
                "(por exemplo: C, C++, Java, Python, JavaScript, SQL, C#, Rust, etc.). "
                "Se o usuário pedir em C, responda exclusivamente em C."
            )

    def process_interaction(self, student_prompt: str, help_level: int, activity_description: str = "") -> dict:
        effective_level = min(help_level, self.max_help_level)
        api_key = os.getenv("OPENAI_API_KEY", "").strip()

        if api_key and len(api_key) > 10 and not api_key.startswith("sk-proj-sua-chave"):
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.get_system_prompt(effective_level, activity_description)},
                        {"role": "user", "content": student_prompt}
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

        fallback_responses = {
            1: f"🔍 [Nível 1 - Socrático] Analisando sua mensagem: '{student_prompt}'. Qual o primeiro conceito ou estrutura de controle que você acredita que precisa utilizar aqui?",
            2: f"💡 [Nível 2 - Conceitual] Para resolver essa questão, lembre-se de como a alocação de variáveis e o fluxo de controle funcionam na memória.",
            3: f"📐 [Nível 3 - Estrutural] Pista de estrutura genérica:\n\nenquanto (condicao) {{\n    // Execução\n}}",
            4: f"📝 [Nível 4 - Guia Lógico] Passo 1: Defina a entrada de dados. Passo 2: Estabeleça o laço ou condição. Passo 3: Processe e exiba a saída.",
            5: f"💻 [Nível 5 - Demonstração] Exemplo pontual de sintaxe:\n\nint contador = 0;\nenquanto (contador < 5) {{\n    // incrementa\n}}",
            6: f"🚀 [Nível 6 - Modo Livre Simulado] Resposta direta para sua solicitação ('{student_prompt}').\n\n(Nota: Para obter o código real gerado na linguagem solicitada, verifique se a OPENAI_API_KEY está configurada no .env)."
        }

        return {
            "level": effective_level,
            "response": fallback_responses.get(effective_level, fallback_responses[1]),
            "mode": "simulated",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }