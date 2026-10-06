class PedagogyController:
    def __init__(self, max_help_level: int = 5):
        self.max_help_level = max_help_level

    def validate_anti_direct_answer(self, ai_text: str) -> bool:
        """Impede que a resposta contenha respostas diretas ou código finalizado."""
        blocked_keywords = ["a resposta correta é", "código completo:", "aqui está a solução:"]
        for keyword in blocked_keywords:
            if keyword in ai_text.lower():
                return False
        return True

    def generate_socratic_response(self, student_input: str, current_level: int) -> dict:
        """
        Simulador local de IA Socrática (Fallback sem necessidade de chave de API no momento).
        Aplica os níveis de ajuda pedagógica progressivos.
        """
        input_lower = student_input.lower()
        
        # Nível 1: Identificação e Questionamento
        if current_level == 1:
            reply = f"O que você já tentou ou qual conceito acredita estar por trás de '{student_input}'?"
            level_name = "Questionamento"

        # Nível 2: Orientação
        elif current_level == 2:
            reply = "Observe bem a estrutura do problema. Qual é o primeiro passo lógico para resolver essa questão?"
            level_name = "Orientação"

        # Nível 3: Pista
        elif current_level == 3:
            reply = "Dica: Tente dividir o problema em partes menores. O que a primeira parte precisa processar?"
            level_name = "Pista Objetiva"

        # Nível 4: Explicação Conceitual
        elif current_level == 4:
            reply = "Conceitualmente, este tipo de problema exige entender como os dados fluem passo a passo antes da implementação."
            level_name = "Explicação Conceitual"

        # Nível 5: Demonstração Controlada
        else:
            reply = "Exemplo de referência: Se tivéssemos um caso similar com números, faríamos o cálculo passo a passo."
            level_name = "Demonstração Controlada"

        return {
            "response": reply,
            "level": current_level,
            "level_name": level_name
        }