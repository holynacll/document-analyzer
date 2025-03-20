import os
from pathlib import Path

from document_analyzer import DocumentAnalyzer
from schemas import Empresa


# Configure API key
os.environ["GEMINI_API_KEY"] = "AIzaSyD_lv5K7yHUDFR0A8da9IoSV0AYVVrBHIE"

# Model configuration
model_name = "google-gla:gemini-2.0-flash"
logfire_api_key = "pylf_v1_us_79YtXC4nTYCPhr8008KMzQzQVtqnB6b0rPq2cfRPl0Z3"
pdf_path = Path("42024066454.pdf")


async def main():
    # Exemplo de uso com uma empresa-alvo específica
    target_empresa = Empresa(
        nome="Point Veículos LTDA",
        cnpj="04.168.812/0001-00",
        resumo="Empresa de veículos",
    )

    # Criar o analisador
    analyzer = DocumentAnalyzer(
        pdf_path=pdf_path,
        model_name=model_name,
        logfire_api_key=logfire_api_key,
        empresa_alvo=target_empresa,
    )

    # Executar a análise com a empresa-alvo
    resultado = await analyzer.analisar_documento()

    if not resultado.sucesso:
        print(f"\nAnálise interrompida: {resultado.mensagem}")
        return

    # Verificar se a análise foi bem-sucedida
    if resultado.sucesso:
        socios_gestores = [
            s for s in resultado.conclusao.socios_com_poder_assinatura
        ]
        print(
            f"\nResumo final: A empresa {target_empresa.nome} é representado pelo(s) sócio(s) com poder(es) representativo(s): {', '.join(socios_gestores)}"
        )
    else:
        print(f"\nNão foi possível completar a análise detalhada: {resultado.mensagem}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
