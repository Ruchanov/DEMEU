import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.timezone import now
from accounts.models import User
from publications.models import Publication
from donations.models import Donation
from donations.utils import handle_donation_created

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print("❌ Stripe webhook error:", e)
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        metadata = intent.get('metadata', {})

        try:
            user_id = metadata.get('user_id')
            donor_amount = float(metadata.get('donor_amount', 0))
            support_percentage = int(metadata.get('support_percentage', 0))
            publication_id = metadata.get('publication_id')

            donor = User.objects.get(id=user_id)
            publication = Publication.objects.get(id=publication_id)

            donation = Donation.objects.create(
                publication=publication,
                donor=donor,
                donor_amount=donor_amount,
                support_percentage=support_percentage,
                created_at=now()
            )

            # 📬 Запускаем всю бизнес-логику (уведомления, чек и т.д.)
            handle_donation_created(donation)

            print(f"✅ Stripe donation saved and handled: {donation}")

        except Exception as e:
            print("❌ Ошибка при обработке Stripe donation:", e)
            return HttpResponse(status=500)

    return HttpResponse(status=200)
