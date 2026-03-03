import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from dealer_app.models import CNotes, Dealer


@login_required
def transporter_dashboard_stats(request):
    """
    Transporter ke liye CNotes stats API.
    Agar user transporter hai → sirf uske dealers ke CNotes dikhao.
    Agar superuser/staff hai → sab dikhao.
    """
    try:
        # Base queryset — transporter ke hisaab se filter
        if request.user.is_superuser or request.user.is_staff:
            qs = CNotes.objects.all()
        else:
            # Transporter ke saare dealers find karo
            transporter_dealers = Dealer.objects.filter(
                transporter__user=request.user
            )
            if not transporter_dealers.exists():
                # Fallback: dealer_name match karo
                transporter_dealers = Dealer.objects.filter(
                    user=request.user
                )
            qs = CNotes.objects.filter(dealer__in=transporter_dealers)

        # ── Basic counts ──────────────────────────────
        total_cnotes  = qs.count()
        total_revenue = float(qs.aggregate(t=Sum('grand_total'))['t'] or 0)
        total_dealers = qs.values('dealer').distinct().count()

        booked     = qs.filter(status='booked').count()
        dispatched = qs.filter(status='dispatched').count()
        delivered  = qs.filter(status='delivered').count()
        cancelled  = qs.filter(status='cancelled').count()
        received   = qs.filter(status='received').count()

        # ── Monthly Revenue — Last 6 Months ──────────
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        monthly_qs = (
            qs.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(revenue=Sum('grand_total'), count=Count('id'))
            .order_by('month')
        )
        months_labels  = [m['month'].strftime('%b %Y') for m in monthly_qs]
        months_revenue = [float(m['revenue'] or 0) for m in monthly_qs]
        months_count   = [m['count'] for m in monthly_qs]

        # ── Top 5 Dealers ─────────────────────────────
        top_dealers = (
            qs.values('dealer__name')
            .annotate(total=Count('id'))
            .order_by('-total')[:5]
        )
        dealer_names  = [d['dealer__name'] or 'Unknown' for d in top_dealers]
        dealer_counts = [d['total'] for d in top_dealers]

        # ── Payment Type Breakdown ────────────────────
        payment_qs = (
            qs.values('payment_type')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        payment_labels = [p['payment_type'] or 'N/A' for p in payment_qs]
        payment_counts = [p['total'] for p in payment_qs]

        # ── Today's CNotes ────────────────────────────
        today_count = qs.filter(
            created_at__date=timezone.now().date()
        ).count()

        return JsonResponse({
            'success': True,
            'total_cnotes':   total_cnotes,
            'total_revenue':  total_revenue,
            'total_dealers':  total_dealers,
            'booked':         booked,
            'dispatched':     dispatched,
            'delivered':      delivered,
            'cancelled':      cancelled,
            'received':       received,
            'today_count':    today_count,
            'months_labels':  months_labels,
            'months_revenue': months_revenue,
            'months_count':   months_count,
            'dealer_names':   dealer_names,
            'dealer_counts':  dealer_counts,
            'payment_labels': payment_labels,
            'payment_counts': payment_counts,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
