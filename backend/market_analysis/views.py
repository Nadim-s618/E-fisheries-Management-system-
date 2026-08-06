from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_market_dashboard


class MarketAnalysisDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        force_refresh = request.query_params.get('refresh') in {'1', 'true', 'yes'}
        return Response(build_market_dashboard(force_refresh=force_refresh))
