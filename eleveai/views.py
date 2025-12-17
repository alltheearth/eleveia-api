# eleveai/views.py

# ==========================================
# VIEWSET - ESCOLA
# ==========================================




# ==========================================
# VIEWSETS - RECURSOS OPERACIONAIS
# ==========================================









class LeadViewSet(UsuarioEscolaMixin, viewsets.ModelViewSet):
    """
    ViewSet para Leads
    Gestor e Operador podem CRUD completo
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [GestorOuOperadorPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nome', 'email', 'telefone']
    ordering_fields = ['nome', 'criado_em', 'status']

    def get_queryset(self):
        """Aplica filtros adicionais"""
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')
        origem = self.request.query_params.get('origem')

        if status_filter and status_filter != 'todos':
            queryset = queryset.filter(status=status_filter)
        if origem:
            queryset = queryset.filter(origem=origem)

        return queryset

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas dos leads"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'novo': queryset.filter(status='novo').count(),
            'contato': queryset.filter(status='contato').count(),
            'qualificado': queryset.filter(status='qualificado').count(),
            'conversao': queryset.filter(status='conversao').count(),
            'perdido': queryset.filter(status='perdido').count(),
        }

        stats['por_origem'] = dict(
            queryset.values('origem')
            .annotate(total=Count('id'))
            .values_list('origem', 'total')
        )

        hoje = timezone.now().date()
        stats['novos_hoje'] = queryset.filter(criado_em__date=hoje).count()

        if stats['total'] > 0:
            stats['taxa_conversao'] = round(
                (stats['conversao'] / stats['total']) * 100, 2
            )
        else:
            stats['taxa_conversao'] = 0

        return Response(stats)

    @action(detail=True, methods=['post'])
    def mudar_status(self, request, pk=None):
        """Mudar status do lead"""
        lead = self.get_object()
        novo_status = request.data.get('status')

        if novo_status not in dict(Lead.STATUS_CHOICES):
            return Response(
                {'erro': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lead.status = novo_status

        if novo_status == 'contato' and not lead.contatado_em:
            lead.contatado_em = timezone.now()
        elif novo_status == 'conversao' and not lead.convertido_em:
            lead.convertido_em = timezone.now()

        lead.save()
        serializer = self.get_serializer(lead)
        return Response(serializer.data)





