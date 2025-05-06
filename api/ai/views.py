from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def ai_trends(request):
    period = request.query_params.get('period', 7)
    return Response({
        "period": period,
        "trends": [
            {"tag": "work", "change": +12},
            {"tag": "family", "change": -5}
        ]
    })

@api_view(['GET'])
def ai_advice(request):
    return Response({
        "advice": "Попробуйте больше времени уделять спорту",
        "confidence": 0.87
    })