
from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import Agent, BinaryContent

from schemas import AnaliseGestao, DocumentoConstituicao, Empresa, NoAnaliseGestao, NoDocumentoConstituicao, ResultadoAnalise, ResumoEnvolvidos


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
        return f"{self.empresa_alvo.nome} (CNPJ: {self.empresa_alvo.cnpj})"
        
    def _get_base_system_prompt(self) -> str:
        return """
        Você é um especialista em análise de documentos jurídicos e empresariais. 
        Analise o documento PDF fornecido e identifique todas as entidades relevantes, 
        incluindo empresas, documentos jurídicos e pessoas mencionadas.
        """
    
    def _get_identificacao_prompt(self) -> str:
        return """
        Analise o documento PDF e identifique:

        1. Todas as pessoas mencionadas, seus papéis e relações com outras entidades
        2. Todas as empresas ou organizações presentes, direta ou indiretamente
        3. Tipos de documentos encontrados (contratos sociais, atas, estatutos, etc.)

        Não se limite apenas a menções diretas. Procure identificar:
        - Relações entre pessoas e empresas que precisem ser inferidas do contexto
        - Estruturas organizacionais implícitas
        - Responsabilidades e poderes que possam ser deduzidos dos documentos
        """
    
    def _get_verificacao_prompt(self) -> str:
        return f"""
        Com base nos documentos identificados, encontre documentos que comprovem a constituição da pessoa jurídica {self.get_empresa_info()}.

        Documentos considerados válidos para essa análise incluem:
        - Contrato Social
        - Estatuto Social
        - Ata de Constituição
        - Termo de Posse de Administrador
        - Alterações Contratuais
        """
    
    def _get_analise_prompt(self) -> str:
        return f"""
        Analise APENAS os documentos de constituição da empresa {self.get_empresa_info()} 
        para determinar sua estrutura administrativa e identificar quais sócios podem assinar 
        documentos e procurações em nome da empresa. A atividade que a empresa está prestando nesse serviço é de **Transferência de Propriedade Veicular**.
        
        ### Passo 1: Informe os dados da empresa.
        
        ### Passo2: Liste todos os documentos de constituição jurídica.
        
        ### Passo 3: Identifique os sócios que podem assinar documentos e procurações em nome da empresa.

        ### Passo 4: Identifique as cláusulas que condicionam a assinatura de documentos ou procurações.
            1. **Limitações de Valor**:
            - Há restrições quanto ao valor máximo de documentos que um sócio pode assinar individualmente?

            2. **Assinatura Conjunta**:
            - É necessária a assinatura de dois ou mais sócios para determinados atos?

            3. **Autorização Prévia**:
            - Há exigência de aprovação prévia da assembleia de sócios ou do conselho administrativo para a assinatura de documentos ou procurações?

            4. **Poderes Específicos**:
            - Há menção a poderes específicos para determinados sócios ou administradores?

            5. **Restrições de Escopo**:
            - Há limitações quanto ao tipo de documento ou ato que pode ser assinado?

            6. **Registro ou Publicação**:
            - É necessário registrar ou publicar atos de representação para que sejam válidos?

            7. **Prazos de Validade**:
            - Há prazos de validade para os poderes de representação ou procurações?

            8. **Penalidades por Descumprimento**:
            - Há menção a penalidades ou consequências por violação das condições de assinatura?

        ### Observações:
        - Caso o documento de constituição não contenha informações suficientes, indique a necessidade de consulta a documentos complementares, como atas de reuniões ou procurações anteriores.
        - Se houver ambiguidade nas cláusulas, sugira a consulta a um advogado especializado em direito societário para interpretação precisa.
        """
    
    def _get_analise_system_prompt(self) -> str:
        return """
        Você é um assistente especializado em análise jurídica e documental de empresas. Sua função é examinar documentos de constituição empresarial (contratos sociais, estatutos e atas) para extrair informações precisas sobre estruturas administrativas e poderes de representação.

        Ao analisar documentos:
        - Mantenha-se estritamente aos fatos presentes nos documentos
        - Seja preciso, objetivo e metódico
        - Quando houver limitações nos documentos para chegar a uma conclusão, indique claramente
        - Não faça suposições ou inferências além do que está explicitamente declarado
        - Não ofereça recomendações jurídicas ou opiniões pessoais

        Use uma estrutura clara e organizada em suas respostas, priorizando a precisão factual sobre opinião ou interpretação expansiva.
        """
    
    def _empresa_esta_presente(self, empresas_identificadas: list[Empresa]) -> bool:
        """Verifica se a empresa alvo está presente na lista de empresas identificadas"""
        for empresa in empresas_identificadas:
            # Verifica se o nome da empresa alvo está presente no nome da empresa identificada (comparação case-insensitive)
            if self.empresa_alvo.nome.lower() in empresa.nome.lower() or empresa.nome.lower() in self.empresa_alvo.nome.lower():
                return True
            
            # Se ambas tiverem CNPJ, verifica se são iguais
            if self.empresa_alvo.cnpj and empresa.cnpj and self.empresa_alvo.cnpj == empresa.cnpj:
                return True
                
        return False
    
    async def analisar_documento(self) -> ResultadoAnalise:        
        # Etapa 1: Identificação de todos os elementos no PDF
        # agent_identificacao = Agent(self.model_name, system_prompt=self._get_base_system_prompt())
        # resultado_identificacao = await agent_identificacao.run(
        #     [
        #         self._get_identificacao_prompt(),
        #         BinaryContent(data=self.pdf_bytes, media_type='application/pdf'),
        #     ],
        #     result_type=ResumoEnvolvidos,
        # )

        # # Verifica se a empresa alvo está presente nos resultados identificados
        # if not self._empresa_esta_presente(resultado_identificacao.data.empresas):
        #     return ResultadoAnalise(
        #         sucesso=False,
        #         mensagem=f"A empresa {self.get_empresa_info()} não foi encontrada nos documentos analisados.",
        #         identificacao=resultado_identificacao.data
        #     )

        # print("Resultado da identificação inicial:")
        # print(f"Pessoas: {[p for p in resultado_identificacao.data.pessoas]}")
        # print(f"Empresas: {[e for e in resultado_identificacao.data.empresas]}")
        # print(f"Documentos: {[d for d in resultado_identificacao.data.documentos]}")
        # print("=" * 80)
        
        # Etapa 2: Verificação da existência de documentos de constituição
        agent_verificacao = Agent(
            self.model_name,
            system_prompt=self._get_analise_system_prompt(),
            result_type=list[DocumentoConstituicao] | NoDocumentoConstituicao
        )
    
        resultado_verificacao = await agent_verificacao.run(
            [
                self._get_verificacao_prompt(),
                BinaryContent(data=self.pdf_bytes, media_type='application/pdf'),
            ],
            # message_history=resultado_identificacao.all_messages()
        )
        
        if isinstance(resultado_verificacao.data, NoDocumentoConstituicao):
            return ResultadoAnalise(
                sucesso=True,
                mensagem=f"Não foram encontrados documentos de constituição suficientes para análise de gestão da empresa {self.get_empresa_info()}.",
                # identificacao=resultado_identificacao.data,
                possui_doc_constituicao=False
            )
        
        docs_constituicao = resultado_verificacao.data
        print(f"Possui documentos de constituição para {self.get_empresa_info()}: {docs_constituicao}")
        print("=" * 80)

        # Etapa 3: Análise detalhada dos documentos de constituição
        agent_analise = Agent(
            self.model_name, 
            # system_prompt=self._get_analise_system_prompt()
        )
        
        @agent_analise.system_prompt
        async def analise_system_prompt() -> str:
            return self._get_analise_system_prompt()

        resultado_analise = await agent_analise.run(
            [
                self._get_analise_prompt(),
            ],
            result_type=AnaliseGestao | NoAnaliseGestao,
            message_history=resultado_verificacao.new_messages()
        )
        
        if isinstance(resultado_analise.data, NoAnaliseGestao):
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"Não foi possível analisar os documentos de constituição da empresa {self.get_empresa_info()}.",
                # identificacao=resultado_identificacao.data,
                possui_doc_constituicao=False
            )
        
        print("Resultado da análise detalhada:")
        print(f"Empresa: {resultado_analise.data.empresa.nome}")
        print(f"Documentos analisados: {[d.nome for d in resultado_analise.data.documentos_constituicao]}")
        print(f"Sócios da Empresa: {[s.nome for s in resultado_analise.data.socios_com_poder_assinatura]}")
        print(f"Clásulas: {resultado_analise.data.clausulas_restritivas}")

        if len(resultado_analise.data.socios_com_poder_assinatura) == 0:
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"Não foi possível identificar sócios gestores na empresa {self.get_empresa_info()}.",
                # identificacao=resultado_identificacao.data,
                possui_doc_constituicao=True,
                analise=resultado_analise.data
        )
        
        if len(resultado_analise.data.clausulas_restritivas) > 0:
            return ResultadoAnalise(
                sucesso=False,
                mensagem=f"A análise detalhada da empresa {self.get_empresa_info()} requer revisão manual.",
                # identificacao=resultado_identificacao.data,
                possui_doc_constituicao=True,
                analise=resultado_analise.data
            )

        return ResultadoAnalise(
            sucesso=True,
            mensagem="Análise concluída com sucesso.",
            # identificacao=resultado_identificacao.data,
            possui_doc_constituicao=True,
            analise=resultado_analise.data
        )
