"""
URLs per API Fascicoli
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FascicoloViewSet, TitolarioVoceViewSet
from archivio_fisico.models import UnitaFisica
from .serializers import UnitaFisicaSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models

router = DefaultRouter()
router.register(r'fascicoli', FascicoloViewSet, basename='fascicolo')
router.register(r'titolario-voci', TitolarioVoceViewSet, basename='titolario-voce')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unita_fisiche_list(request):
    """Lista unità fisiche"""
    search = request.query_params.get('search', '')
    queryset = UnitaFisica.objects.all()
    
    if search:
        queryset = queryset.filter(
            models.Q(codice__icontains=search) | 
            models.Q(nome__icontains=search)
        )
    
    queryset = queryset.order_by('codice')
    serializer = UnitaFisicaSerializer(queryset, many=True)
    return Response({'results': serializer.data})


urlpatterns = [
    path('', include(router.urls)),
    path('archivio-fisico/unita/', unita_fisiche_list, name='unita-fisiche'),
]
