import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis registradas no .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

print("\n==========================================")
print("   TESTADOR DE CONEXÃO - OPENAI API")
print("==========================================\n")

if not api_key or api_key == "sk-proj-sua-chave-aqui-123456789":
    print("❌ ERRO: Nenhuma chave válida foi encontrada no arquivo .env!")
    print(" Verifique se criou o arquivo '.env' na raiz e definiu OPENAI_API_KEY=sk-...")
else:
    # Exibe apenas os primeiros e últimos caracteres por segurança
    masked_key = f"{api_key[:7]}...{api_key[-4:]}"
    print(f"🔑 Chave encontrada no .env: {masked_key}")
    print("📡 Testando comunicação com a OpenAI...\n")

    try:
        client = OpenAI(api_key=api_key)
        
        # Envia uma chamada mínima para testar saldo e validade da chave
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente de teste."},
                {"role": "user", "content": "Responda apenas com a palavra: 'CONECTADO'"}
            ],
            max_tokens=10
        )
        
        resultado = response.choices[0].message.content.strip()
        print("✅ SUCESSO! A chave da OpenAI está funcionando perfeitamente!")
        print(f"🤖 Resposta da API: {resultado}\n")

    except Exception as e:
        print("❌ ERRO AO COMUNICAR COM A OPENAI:")
        print(f"   {e}\n")
        print("💡 Dicas para solução:")
        print("   1. Verifique se a chave foi copiada por completo sem espaços extras.")
        print("   2. Verifique se sua conta da OpenAI possui créditos ativos na plataforma (billing).")