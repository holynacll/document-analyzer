from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import Agent, BinaryContent

from schemas import (AnaliseGestao, ConclusaoAnalise, DocumentoConstituicao, 
                    Empresa, NoAnaliseGestao, NoDocumentoConstituicao, ResultadoAnalise)


@dataclass
class DocumentAnalyzer:
    pdf_path: Path
    model_name: str
    logfire_api_key: str
    empresa_alvo: Empresa
    pdf_bytes: bytes = field(init=False)
    
    def __post_init__(self):
        self.pdf_bytes = self.pdf_path.read_bytes()
        # configure logfire
        import logfire
        logfire.configure(token=self.logfire_api_key)
        Agent.instrument_all()

    def get_empresa_info(self) -> str:
        return f"{self.empresa_alvo.nome} (CNPJ: {self.empresa_alvo.cnpj or 'não informado'})"

    def _get_base_system_prompt(self) -> str:
        return """
        Você é um assistente especializado em análise jurídica e documental de empresas. Sua função é examinar documentos de constituição empresarial para extrair informações precisas sobre estruturas administrativas e poderes de representação.

        Ao analisar documentos:
        - Mantenha-se estritamente aos fatos presentes nos documentos
        - Seja preciso, objetivo e metódico
        - Quando houver limitações nos documentos para chegar a uma conclusão, indique claramente
        - Não faça suposições ou inferências além do que está explicitamente declarado
        """

    def _get_verificacao_prompt(self) -> str:
        return f"""
        Encontre documentos que comprovem a constituição da pessoa jurídica {self.get_empresa_info()}.

        Documentos considerados válidos para essa análise incluem:
        - Contrato Social
        - Estatuto Social
        - Ata de Constituição
        - Termo de Posse de Administrador
        - Alterações Contratuais
        """

    def _get_analise_prompt(self) -> str:
        return f"""
        Analise os documentos de constituição jurídica da empresa {self.get_empresa_info()} para extrair:
        
        1. Informações da empresa
        2. Estrutura administrativa e de representação
        3. Identificação de todos os sócios e administradores
        4. Regras e limitações para representação da empresa
        
        Baseie-se apenas em informações explicitamente mencionadas nos documentos.
        """

    def _get_conclusao_prompt(self) -> str:
        return f"""
        Com base na análise dos documentos de constituição jurídica da empresa {self.get_empresa_info()}, forneça uma conclusão objetiva sobre:
        
        1. Quais sócios podem assinar documentos e procurações representando a empresa
        2. Se existem cláusulas restritivas que condicionam a representação da empresa
        
        Se houver cláusulas restritivas complexas, ambiguidades ou informações insuficientes, indique claramente que é necessária análise de profissional especializado.
        """
    
    async def analisar_documento(self) -> ResultadoAnalise:               
        # Etapa 1: Verificação da existência de documentos de constituição
        agent_verificacao = Agent(
            self.model_name,
            system_prompt=self._get_base_system_prompt(),
            result_type=list[DocumentoConstituicao] | NoDocumentoConstituicao
        )
    
        resultado_verificacao = await agent_verificacao.run(
            [
                self._get_verificacao_prompt(),
                BinaryContent(data=self.pdf_bytes, media_type='application/pdf'),
            ],
        )
        
        if isinstance(resultado_verificacao.data, NoDocumentoConstituicao):
            return ResultadoAnalise(
                sucesso=True,
                mensagem=f"Não foram encontrados documentos de constituição suficientes para análise de gestão da empresa {self.get_empresa_info()}.",
            )
        
        docs_constituicao = resultado_verificacao.data
        print(f"Documentos de constituição encontrados: {len(docs_constituicao)}")
        
        # Etapa 2: Análise detalhada dos documentos de constituição
        agent_analise = Agent(self.model_name)
        resultado_analise = await agent_analise.run(
            [
                self._get_analise_prompt(),
            ],
            result_type=AnaliseGestao,
            message_history=resultado_verificacao.all_messages()
        )

        if isinstance(resultado_analise.data, NoAnaliseGestao):
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"Não foi possível analisar os documentos de constituição da empresa {self.get_empresa_info()}.",
            )

        # Etapa 3: Conclusão sobre poderes de representação
        agent_conclusao = Agent(self.model_name)

        resultado_conclusao = await agent_conclusao.run(
            [
                self._get_conclusao_prompt(),
            ],
            result_type=ConclusaoAnalise,
            message_history=resultado_analise.all_messages()
        )
        
        print("Resultado da análise detalhada:")
        print(f"Empresa: {resultado_analise.data.empresa.nome}")
        print(
            f"Documentos analisados: {[d for d in resultado_verificacao.data]}"
        )
        print(
            f"Sócios com poder de assinatura: {[s.nome for s in resultado_conclusao.data.socios_com_poder_assinatura]}"
        )
        print(f"Cláusulas restritivas: {resultado_conclusao.data.clausulas_restritivas}")
        print(
            f"Requer análise especializada: {resultado_conclusao.data.requer_analise_especializada}"
        )
        print(f"Conclusão: {resultado_conclusao.data.conclusao}")


        # Lógica de decisão baseada na conclusão
        if len(resultado_conclusao.data.socios_com_poder_assinatura) == 0:
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"Não foi possível identificar sócios com poder de assinatura na empresa {self.get_empresa_info()}.",
            )
        
        if resultado_conclusao.data.requer_analise_especializada or resultado_conclusao.data.clausulas_restritivas:
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"A análise da empresa {self.get_empresa_info()} requer revisão por profissional especializado devido a cláusulas complexas ou ambiguidades.",
            )

        return ResultadoAnalise(
            sucesso=True,
            mensagem="Análise concluída com sucesso.",
            conclusao=resultado_conclusao.data,
        )
