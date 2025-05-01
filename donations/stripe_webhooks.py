import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Donation
from publications.models import Publication
from accounts.models import User
from django.utils.timezone import now

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        metadata = intent.get('metadata', {})

        # Извлекаем данные
        user_id = metadata.get('user_id')
        donor_amount = float(metadata.get('donor_amount', 0))
        support_percentage = int(metadata.get('support_percentage', 0))
        publication_id = metadata.get('publication_id')

        try:
            from .models import Donation
            donor = User.objects.get(id=user_id)
            publication = Publication.objects.get(id=publication_id)
            donation = Donation.objects.create(
                publication=publication,
                donor=donor,
                donor_amount=donor_amount,
                support_percentage=support_percentage,
                created_at=now()
            )
        except Exception as e:
            # логируй или обрабатывай
            print("Ошибка при создании Donation:", e)

    return HttpResponse(status=200)
