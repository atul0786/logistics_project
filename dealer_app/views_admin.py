import json
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from .models import CNotes, Dealer


@staff_member_required
def admin_dashboard(request):
    # ── Basic Stats ──────────────────────────────
    total_cnotes  = CNotes.objects.count()
    total_revenue = CNotes.objects.aggregate(t=Sum('grand_total'))['t'] or 0
    total_dealers = Dealer.objects.count()

    booked     = CNotes.objects.filter(status='booked').count()
    dispatched = CNotes.objects.filter(status='dispatched').count()
    delivered  = CNotes.objects.filter(status='delivered').count()
    cancelled  = CNotes.objects.filter(status='cancelled').count()
    received   = CNotes.objects.filter(status='received').count()

    # ── Monthly Revenue — Last 6 Months ──────────
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_qs = (
        CNotes.objects
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=Sum('grand_total'), count=Count('id'))
        .order_by('month')
    )
    months_labels  = [m['month'].strftime('%b %Y') for m in monthly_qs]
    months_revenue = [float(m['revenue'] or 0) for m in monthly_qs]
    months_count   = [m['count'] for m in monthly_qs]

    # ── Top 5 Dealers by CNotes ───────────────────
    top_dealers = (
        CNotes.objects
        .values('dealer__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    dealer_names  = [d['dealer__name'] or 'Unknown' for d in top_dealers]
    dealer_counts = [d['total'] for d in top_dealers]

    # ── Payment Type Breakdown ────────────────────
    payment_qs = (
        CNotes.objects
        .values('payment_type')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    payment_labels = [p['payment_type'] or 'N/A' for p in payment_qs]
    payment_counts = [p['total'] for p in payment_qs]

    context = {
        # Stats cards
        'total_cnotes':  total_cnotes,
        'total_revenue': total_revenue,
        'total_dealers': total_dealers,
        'booked':        booked,
        'dispatched':    dispatched,
        'delivered':     delivered,
        'cancelled':     cancelled,
        'received':      received,

        # Chart data (JSON strings)
        'months_labels':   json.dumps(months_labels),
        'months_revenue':  json.dumps(months_revenue),
        'months_count':    json.dumps(months_count),
        'dealer_names':    json.dumps(dealer_names),
        'dealer_counts':   json.dumps(dealer_counts),
        'payment_labels':  json.dumps(payment_labels),
        'payment_counts':  json.dumps(payment_counts),
    }
    return render(request, 'admin/custom_dashboard.html', context)
