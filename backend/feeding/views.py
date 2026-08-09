from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ponds.views import get_user_pond

from .models import FeedingRecommendation, FeedingSession
from .serializers import (
    FeedingRecommendationEditSerializer,
    FeedingRecommendationSerializer,
    FeedingSessionCompleteSerializer,
    FeedingSessionSerializer,
)
from .services.notifications import create_feeding_notification
from .services.recommendations import (
    create_sessions,
    get_or_create_draft_recommendation,
    update_recommendation_from_edit,
)


def user_recommendations(user):
    queryset = FeedingRecommendation.objects.select_related('pond', 'pond__owner').prefetch_related('sessions')
    if user.is_staff:
        return queryset.all()
    return queryset.filter(pond__owner=user)


def user_sessions(user):
    queryset = FeedingSession.objects.select_related(
        'pond',
        'pond__owner',
        'recommendation',
    )
    if user.is_staff:
        return queryset.all()
    return queryset.filter(pond__owner=user)


def get_pond_from_query(request):
    pond_id = request.query_params.get('pond')
    if not pond_id:
        raise ValidationError({'pond': 'This query parameter is required.'})
    if not pond_id.isdigit():
        raise ValidationError({'pond': 'Pond must be a valid numeric id.'})

    pond = get_user_pond(request.user, pond_id)
    if not pond:
        raise ValidationError({'pond': 'Pond not found.'})

    return pond


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feeding_dashboard(request):
    pond = get_pond_from_query(request)
    active_plan = user_recommendations(request.user).filter(
        pond=pond,
        status__in=[
            FeedingRecommendation.Status.ACCEPTED,
            FeedingRecommendation.Status.EDITED,
        ],
        sessions__status=FeedingSession.Status.PENDING,
    ).distinct().order_by('-recommendation_date', '-created_at').first()

    if active_plan:
        recommendation = user_recommendations(request.user).filter(
            pond=pond,
            status=FeedingRecommendation.Status.DRAFT,
            recommendation_date__gte=timezone.localdate(),
        ).order_by('-recommendation_date', '-created_at').first() or active_plan
        generated = False
    else:
        recommendation = user_recommendations(request.user).filter(
            pond=pond,
            status=FeedingRecommendation.Status.DRAFT,
            recommendation_date__gte=timezone.localdate(),
        ).order_by('recommendation_date', '-created_at').first()
        if recommendation:
            generated = False
        else:
            recommendation, generated = get_or_create_draft_recommendation(pond)

    pending_sessions = user_sessions(request.user).filter(
        pond=pond,
        status=FeedingSession.Status.PENDING,
    ).order_by('scheduled_at')[:10]
    history = user_recommendations(request.user).filter(
        pond=pond,
        status__in=[
            FeedingRecommendation.Status.ACCEPTED,
            FeedingRecommendation.Status.EDITED,
            FeedingRecommendation.Status.COMPLETED,
        ],
    ).order_by('-recommendation_date', '-created_at')[:30]

    return Response({
        'recommendation': FeedingRecommendationSerializer(recommendation).data,
        'generated': generated,
        'active_plan': FeedingRecommendationSerializer(active_plan).data if active_plan else None,
        'pending_sessions': FeedingSessionSerializer(pending_sessions, many=True).data,
        'history': FeedingRecommendationSerializer(history, many=True).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def accept_recommendation(request, pk):
    recommendation = user_recommendations(request.user).filter(pk=pk).first()
    if not recommendation:
        return Response({'detail': 'Feeding recommendation not found.'}, status=status.HTTP_404_NOT_FOUND)

    if recommendation.status == FeedingRecommendation.Status.DRAFT:
        recommendation.status = FeedingRecommendation.Status.ACCEPTED
        recommendation.save(update_fields=['status', 'updated_at'])

    create_sessions(recommendation)
    create_feeding_notification(
        pond=recommendation.pond,
        parameter='Feeding schedule',
        current_value=f'{recommendation.recommended_feed_kg} kg',
        reason=f'{recommendation.meals} feeding session(s) scheduled for {recommendation.pond.name}.',
    )

    return Response(FeedingRecommendationSerializer(recommendation).data)


@api_view(['PATCH', 'POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def edit_recommendation(request, pk):
    recommendation = user_recommendations(request.user).filter(pk=pk).first()
    if not recommendation:
        return Response({'detail': 'Feeding recommendation not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FeedingRecommendationEditSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    recommendation = update_recommendation_from_edit(recommendation, serializer.validated_data)
    create_feeding_notification(
        pond=recommendation.pond,
        parameter='Feeding schedule edited',
        current_value=f'{recommendation.recommended_feed_kg} kg',
        reason=f'Edited feeding plan is ready to track for {recommendation.pond.name}.',
    )

    return Response(FeedingRecommendationSerializer(recommendation).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def complete_session(request, pk):
    session = user_sessions(request.user).filter(pk=pk).first()
    if not session:
        return Response({'detail': 'Feeding session not found.'}, status=status.HTTP_404_NOT_FOUND)

    if session.status == FeedingSession.Status.COMPLETED:
        return Response(FeedingSessionSerializer(session).data)

    serializer = FeedingSessionCompleteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    session.actual_feed_kg = serializer.validated_data.get('actual_feed_kg') or session.planned_feed_kg
    session.notes = serializer.validated_data.get('notes', session.notes)
    session.status = FeedingSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=['actual_feed_kg', 'notes', 'status', 'completed_at', 'updated_at'])

    recommendation = session.recommendation
    next_session = recommendation.sessions.filter(status=FeedingSession.Status.PENDING).order_by('scheduled_at').first()
    next_recommendation = None

    create_feeding_notification(
        pond=session.pond,
        parameter='Feeding completed',
        current_value=f'{session.actual_feed_kg} kg',
        reason=f'Meal {session.meal_number} completed for {session.pond.name}.',
    )

    if next_session is None:
        recommendation.status = FeedingRecommendation.Status.COMPLETED
        recommendation.save(update_fields=['status', 'updated_at'])
        next_date = max(timezone.localdate(), recommendation.recommendation_date + timedelta(days=1))
        next_recommendation, _ = get_or_create_draft_recommendation(
            session.pond,
            recommendation_date=next_date,
            force_new=True,
        )
    else:
        create_feeding_notification(
            pond=session.pond,
            parameter='Next feeding session',
            current_value=f'{next_session.planned_feed_kg} kg',
            reason=f'Meal {next_session.meal_number} is scheduled next for {session.pond.name}.',
        )

    return Response({
        'session': FeedingSessionSerializer(session).data,
        'recommendation': FeedingRecommendationSerializer(recommendation).data,
        'next_session': FeedingSessionSerializer(next_session).data if next_session else None,
        'next_recommendation': FeedingRecommendationSerializer(next_recommendation).data if next_recommendation else None,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feeding_history(request):
    pond = get_pond_from_query(request)
    history = user_recommendations(request.user).filter(
        pond=pond,
        status__in=[
            FeedingRecommendation.Status.ACCEPTED,
            FeedingRecommendation.Status.EDITED,
            FeedingRecommendation.Status.COMPLETED,
        ],
    ).order_by('-recommendation_date', '-created_at')[:50]

    return Response(FeedingRecommendationSerializer(history, many=True).data)
