# apps/contacts/services/guardian_enrichment_service.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import requests
from django.utils import timezone

logger = logging.getLogger(__name__)


class GuardianEnrichmentService:
    """
    Service responsável por enriquecer dados de responsáveis com:
    - Boletos dos filhos (busca paralela)
    - Situação agregada (boletos abertos, docs faltando)
    - Ordenação alfabética

    Performance:
    - Paralelização: 10 threads simultâneas
    - Timeout por request: 10s
    - Cache: 1-2 horas (controlado pela view)
    """

    def __init__(self, token: str):
        """
        Args:
            token: Token de autenticação SIGA da escola
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.max_workers = 10  # Threads paralelas

    def enrich_guardians_with_invoices(
            self,
            guardians: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enriquece lista de responsáveis com boletos dos filhos.

        Para cada responsável:
        1. Identifica todos os filhos
        2. Busca boletos de cada filho (PARALELO)
        3. Calcula situação agregada
        4. Ordena alfabeticamente

        Args:
            guardians: Lista de responsáveis já agregados

        Returns:
            Lista enriquecida e ordenada
        """
        logger.info(f"Enriching {len(guardians)} guardians with invoices")

        enriched_guardians = []

        # Processar cada responsável
        for guardian in guardians:
            try:
                enriched = self._enrich_single_guardian(guardian)
                enriched_guardians.append(enriched)
            except Exception as e:
                logger.error(
                    f"Error enriching guardian {guardian.get('id')}: {str(e)}"
                )
                # Adiciona guardian sem enriquecimento se falhar
                enriched_guardians.append(self._add_empty_enrichment(guardian))

        # Ordenar alfabeticamente por nome
        enriched_guardians.sort(key=lambda g: g.get('nome', '').upper())

        logger.info(f"Successfully enriched {len(enriched_guardians)} guardians")
        return enriched_guardians

    def _enrich_single_guardian(
            self,
            guardian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enriquece um único responsável.

        Args:
            guardian: Dados do responsável

        Returns:
            Responsável enriquecido
        """
        filhos = guardian.get('filhos', [])

        if not filhos:
            return self._add_empty_enrichment(guardian)

        # Buscar boletos de todos os filhos em PARALELO
        student_ids = [filho.get('id') for filho in filhos if filho.get('id')]
        invoices_by_student = self._fetch_invoices_parallel(student_ids)

        # Enriquecer cada filho com seus boletos
        enriched_filhos = []
        all_invoices = []

        for filho in filhos:
            student_id = filho.get('id')
            student_invoices = invoices_by_student.get(student_id, [])

            enriched_filho = {
                **filho,
                'boletos': student_invoices,
                'documentos_faltantes': []  # Vazio por enquanto (alunos)
            }
            enriched_filhos.append(enriched_filho)
            all_invoices.extend(student_invoices)

        # Calcular situação agregada
        situacao = self._calculate_situacao(all_invoices, guardian)

        # Adicionar documentos do responsável (já vem do aggregator)
        documentos_estruturados = {
            'responsavel': guardian.get('documentos', []),
            'aluno': []  # Vazio por hora
        }

        return {
            **guardian,
            'filhos': enriched_filhos,
            'documentos': documentos_estruturados,
            'situacao': situacao
        }

    def _fetch_invoices_parallel(
            self,
            student_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Busca boletos de múltiplos alunos em PARALELO.

        Args:
            student_ids: Lista de IDs dos alunos

        Returns:
            Dict {student_id: [invoices]}
        """
        invoices_by_student = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Criar futures
            future_to_student = {
                executor.submit(
                    self._fetch_student_invoices,
                    student_id
                ): student_id
                for student_id in student_ids
            }

            # Processar resultados conforme completam
            for future in as_completed(future_to_student):
                student_id = future_to_student[future]
                try:
                    invoices = future.result()
                    invoices_by_student[student_id] = invoices
                except Exception as exc:
                    logger.error(
                        f"Error fetching invoices for student {student_id}: {exc}"
                    )
                    invoices_by_student[student_id] = []

        return invoices_by_student

    def _fetch_student_invoices(
            self,
            student_id: int
    ) -> List[Dict[str, Any]]:
        """
        Busca boletos de um único aluno.

        Args:
            student_id: ID do aluno

        Returns:
            Lista de boletos formatados
        """
        url = "https://siga.activesoft.com.br/api/v0/informacoes_boleto/"
        params = {'id_aluno': student_id}

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                raw_invoices = data.get('resultados', [])

                # Formatar boletos
                return [
                    self._format_invoice(invoice)
                    for invoice in raw_invoices
                ]
            else:
                logger.warning(
                    f"Non-200 status for student {student_id}: "
                    f"{response.status_code}"
                )
                return []

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching invoices for student {student_id}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request error for student {student_id}: {str(e)}"
            )
            return []

    def _format_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata boleto do SIGA para resposta da API.

        Args:
            invoice: Boleto raw do SIGA

        Returns:
            Boleto formatado
        """
        status_code = invoice.get("situacao_titulo", "")

        # Mapear status para display
        status_map = {
            "ABE": "Aberto",
            "LIQ": "Liquidado",
            "CAN": "Cancelado",
            "VEN": "Vencido"
        }

        return {
            "invoice_number": invoice.get("titulo"),
            "bank": invoice.get("nome_banco"),
            "due_date": invoice.get("dt_vencimento"),
            "payment_date": invoice.get("dt_pagamento"),
            "total_amount": invoice.get("valor_documento"),
            "received_amount": invoice.get("valor_recebido_total"),
            "status_code": status_code,
            "status_display": status_map.get(status_code, status_code),
            "installment": invoice.get("parcela_cobranca"),
            "digitable_line": invoice.get("linha_digitavel"),
            "payment_url": invoice.get("link_pagamento"),
        }

    def _calculate_situacao(
            self,
            all_invoices: List[Dict[str, Any]],
            guardian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula situação agregada do responsável.

        Args:
            all_invoices: Todos os boletos dos filhos
            guardian: Dados do responsável

        Returns:
            Dict com situação calculada
        """
        # Filtrar boletos abertos (ABE = Aberto, não LIQ ou CAN)
        boletos_abertos = [
            inv for inv in all_invoices
            if inv.get('status_code') == 'ABE'
        ]

        # Calcular valor total aberto
        valor_total_aberto = sum(
            float(inv.get('total_amount', 0) or 0)
            for inv in boletos_abertos
        )

        # Documentos faltantes (status != entregue ou data_entrega = None)
        documentos = guardian.get('documentos', [])
        docs_faltando = [
            doc for doc in documentos
            if not doc.get('data_entrega') or doc.get('status') == 'pendente'
        ]

        return {
            "tem_boleto_aberto": len(boletos_abertos) > 0,
            "tem_doc_faltando": len(docs_faltando) > 0,
            "total_boletos_abertos": len(boletos_abertos),
            "valor_total_aberto": f"{valor_total_aberto:.2f}",
            "total_docs_faltando": len(docs_faltando)
        }

    def _add_empty_enrichment(
            self,
            guardian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adiciona enriquecimento vazio quando falha ou não há filhos.

        Args:
            guardian: Dados do responsável

        Returns:
            Responsável com campos vazios
        """
        documentos_estruturados = {
            'responsavel': guardian.get('documentos', []),
            'aluno': []
        }

        return {
            **guardian,
            'filhos': guardian.get('filhos', []),
            'documentos': documentos_estruturados,
            'situacao': {
                "tem_boleto_aberto": False,
                "tem_doc_faltando": False,
                "total_boletos_abertos": 0,
                "valor_total_aberto": "0.00",
                "total_docs_faltando": 0
            }
        }