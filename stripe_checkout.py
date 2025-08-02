import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def checkout_39():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "Документ стандарт",
                },
                "unit_amount": 3900,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("SUCCESS_URL"),
        cancel_url=os.getenv("CANCEL_URL"),
    )
    return session.url

def checkout_49():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "Документ премиум",
                },
                "unit_amount": 4900,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("SUCCESS_URL"),
        cancel_url=os.getenv("CANCEL_URL"),
    )
    return session.url

def checkout_59():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": "Документ юридический",
                },
                "unit_amount": 5900,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("SUCCESS_URL"),
        cancel_url=os.getenv("CANCEL_URL"),
    )
    return session.url
