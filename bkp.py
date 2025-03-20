import os
from pydantic import BaseModel, Field
from httpx import AsyncClient
from pathlib import Path
from pydantic_ai import Agent, BinaryContent, RunContext

# Configure API key
os.environ["GEMINI_API_KEY"] = "AIzaSyD_lv5K7yHUDFR0A8da9IoSV0AYVVrBHIE"

# Model configuration
model_name = "google-gla:gemini-2.0-flash"
BASE_SYSTEM_PROMPT = """
Você é um especialista de documentos requeridos para os diversos serviços do Departamento Estadual de Trânsito (Detran). 
Sua tarefa é analisar o documento PDF de entrada de forma minuciosa e detalhada.
"""

pdf_path = Path('42024066454.pdf')

# Data models
class Empresa(BaseModel):
    nome: str
    cnpj: str | None = None
    description: str = Field(description="Resumo de informações da empresa")


class Pessoa(BaseModel):
    nome: str
    cpf: str | None = None
    description: str = Field(description="Resumo de informações da pessoa")
    cargo: str | None = Field(None, description="Cargo ou função na empresa, se aplicável")


class Documento(BaseModel):
    nome: str = Field(description="Nome do documento")
    description: str = Field(description="Resumo de informações do documento")
    tipo: str | None = Field(None, description="Tipo de documento (ex: contrato social, ata, etc)")


class ResumoEnvolvidos(BaseModel):
    pessoas: list[Pessoa] = Field(description="Lista de pessoas mencionadas nos documentos")
    empresas: list[Empresa] = Field(description="Lista de empresas mencionadas nos documentos")
    documentos: list[Documento] = Field(description="Lista de documentos contidos no PDF")


class DocumentoConstituicao(BaseModel):
    nome: str = Field(description="Nome do documento de constituição")
    tipo: str = Field(description="Tipo de documento (contrato social, ata, estatuto, etc)")
    data: str | None = Field(None, description="Data do documento")
    resumo: str = Field(description="Resumo do conteúdo")


class AnaliseGestao(BaseModel):
    empresa: Empresa = Field(description="Dados da empresa analisada")
    documentos_constituicao: list[DocumentoConstituicao] = Field(description="Documentos de constituição encontrados")
    socios_gestores: list[Pessoa] = Field(description="Sócios que respondem pela empresa")
    poderes: str = Field(description="Descrição dos poderes de gestão conforme documentos")
    conclusao: str = Field(description="Conclusão sobre a gestão da empresa")


# Prompts
PROMPT_IDENTIFICACAO = """
Faça um resumo detalhado das pessoas e empresas envolvidas, e os documentos contidos no PDF.
Identifique especificamente quaisquer documentos que sejam contratos sociais, alterações contratuais, 
estatutos, atas ou termos de posse.
"""

PROMPT_VERIFICACAO = """
Com base nos documentos identificados, existe documento de constituição da pessoa jurídica 
(como contrato social, alterações contratuais, estatuto, ata ou termo de posse) 
que permita identificar os responsáveis pela gestão?
Responda apenas com "Sim" ou "Não".
"""

PROMPT_ANALISE_DETALHADA = """
Analise detalhadamente os documentos de constituição da pessoa jurídica identificados.
Extraia as seguintes informações:
1. Quais sócios respondem pela empresa e quais seus poderes específicos
2. Eventuais limitações de poderes dos sócios
3. Regras de administração da empresa
4. Qualquer cláusula relevante sobre responsabilidade administrativa ou financeira

Forneça uma conclusão clara sobre quem são os administradores/gestores da empresa conforme estes documentos.
"""


async def main():
    pdf_bytes = pdf_path.read_bytes()
    
    # Etapa 1: Identificação de todos os elementos no PDF
    agent_identificacao = Agent(model_name, system_prompt=BASE_SYSTEM_PROMPT)
    resultado_identificacao = await agent_identificacao.run(
        [
            PROMPT_IDENTIFICACAO,
            BinaryContent(data=pdf_bytes, media_type='application/pdf'),
        ],
        result_type=ResumoEnvolvidos,
    )
    
    print(f"Resultado da identificação inicial:")
    print(f"Pessoas: {[p.nome for p in resultado_identificacao.data.pessoas]}")
    print(f"Empresas: {[e.nome for e in resultado_identificacao.data.empresas]}")
    print(f"Documentos: {[d.nome for d in resultado_identificacao.data.documentos]}")
    print("=" * 80)
    
    # Etapa 2: Verificação da existência de documentos de constituição
    agent_verificacao = Agent(model_name, system_prompt=BASE_SYSTEM_PROMPT)
    resultado_verificacao = await agent_verificacao.run(
        [
            PROMPT_VERIFICACAO,
        ],
        message_history=resultado_identificacao.all_messages()
    )
    
    possui_doc_constituicao = resultado_verificacao.data == "Sim"
    print(f"Possui documentos de constituição: {possui_doc_constituicao}")
    print("=" * 80)
    
    # Etapa 3: Análise detalhada dos documentos de constituição (se existirem)
    if possui_doc_constituicao:
        # Criar um system prompt dinâmico que incorpore informações já identificadas
        empresa_principal = None
        if resultado_identificacao.data.empresas:
            empresa_principal = resultado_identificacao.data.empresas[0]
            
        # Agent para análise detalhada com system prompt adaptado
        system_prompt_analise = f"""
        {BASE_SYSTEM_PROMPT}
        
        Com base na análise inicial, foi identificada a empresa {empresa_principal.nome if empresa_principal else 'mencionada no documento'} 
        {f'com CNPJ {empresa_principal.cnpj}' if empresa_principal and empresa_principal.cnpj else ''}.
        
        Agora, sua tarefa é analisar detalhadamente os documentos de constituição desta pessoa jurídica
        (contratos sociais, alterações, estatutos, atas ou termos de posse) para determinar:
        
        1. Quem são os sócios que respondem oficialmente pela empresa
        2. Quais são seus poderes e limitações conforme os documentos
        3. Como está estruturada a administração da empresa
        
        Forneça uma análise minuciosa e conclusiva sobre a gestão da empresa com base apenas nos documentos presentes.
        """
        
        agent_analise = Agent(model_name, system_prompt=system_prompt_analise)
        resultado_analise = await agent_analise.run(
            [
                PROMPT_ANALISE_DETALHADA,
            ],
            result_type=AnaliseGestao,
            message_history=resultado_identificacao.all_messages() + resultado_verificacao.all_messages()
        )
        
        print("Resultado da análise detalhada:")
        print(f"Empresa: {resultado_analise.data.empresa.nome}")
        print(f"Documentos analisados: {[d.nome for d in resultado_analise.data.documentos_constituicao]}")
        print(f"Sócios gestores: {[s.nome for s in resultado_analise.data.socios_gestores]}")
        print(f"Poderes: {resultado_analise.data.poderes}")
        print(f"Conclusão: {resultado_analise.data.conclusao}")
    else:
        print("Não foram encontrados documentos de constituição suficientes para análise de gestão.")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
