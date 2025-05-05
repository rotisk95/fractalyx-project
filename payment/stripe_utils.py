import os
import logging
import stripe
from flask import request, session

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Stripe with API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def create_default_plans():
    """
    Create default subscription plans in Stripe if they don't exist.
    
    Returns:
        dict: Dictionary mapping plan names to their Stripe price IDs
    """
    try:
        # Default plans configuration
        default_plans = [
            {
                'name': 'Basic',
                'price': 49.99,
                'interval': 'month',
                'description': 'Perfect for individuals and small teams',
                'features': [
                    'Up to 5 projects',
                    '3 fractal agents',
                    'Basic adaptive intelligence',
                    'Email support'
                ]
            },
            {
                'name': 'Professional',
                'price': 99.99,
                'interval': 'month',
                'description': 'Ideal for growing businesses',
                'features': [
                    'Unlimited projects',
                    'Full fractal network',
                    'Advanced adaptive intelligence',
                    'Priority support',
                    'Project analytics'
                ]
            },
            {
                'name': 'Enterprise',
                'price': 199.99,
                'interval': 'month',
                'description': 'For large organizations with complex needs',
                'features': [
                    'Unlimited projects',
                    'Custom fractal network',
                    'Premium adaptive intelligence',
                    'Dedicated support',
                    'Advanced analytics',
                    'Custom integrations',
                    'Team management'
                ]
            }
        ]
        
        # Check existing products
        products = stripe.Product.list(limit=100)
        existing_products = {product.name: product.id for product in products.data}
        
        # Create products and prices if needed
        plan_ids = {}
        for plan in default_plans:
            # Create or retrieve product
            product_id = None
            if plan['name'] in existing_products:
                product_id = existing_products[plan['name']]
                # Update product
                stripe.Product.modify(
                    product_id,
                    description=plan['description'],
                    metadata={'features': ','.join(plan['features'])}
                )
            else:
                # Create new product
                product = stripe.Product.create(
                    name=plan['name'],
                    description=plan['description'],
                    metadata={'features': ','.join(plan['features'])}
                )
                product_id = product.id
            
            # Check existing prices for this product
            prices = stripe.Price.list(product=product_id, active=True)
            price_id = None
            for price in prices.data:
                if (price.recurring.interval == plan['interval'] and 
                    price.unit_amount == int(plan['price'] * 100)):
                    price_id = price.id
                    break
            
            if not price_id:
                # Create new price
                price = stripe.Price.create(
                    product=product_id,
                    unit_amount=int(plan['price'] * 100),
                    currency='usd',
                    recurring={'interval': plan['interval']}
                )
                price_id = price.id
            
            plan_ids[plan['name']] = price_id
        
        return plan_ids
    except Exception as e:
        logger.exception(f"Error creating default plans: {str(e)}")
        return {}

def get_subscription_plans():
    """
    Get subscription plans from Stripe.
    If no plans exist, create default ones.
    
    Returns:
        list: List of plan dictionaries with details
    """
    try:
        # Fetch prices from Stripe
        prices = stripe.Price.list(
            active=True,
            expand=['data.product'],
            limit=100
        )
        
        # Check if we need to create default plans
        if not prices.data:
            logger.info("No plans found in Stripe. Creating default plans...")
            create_default_plans()
            
            # Fetch prices again
            prices = stripe.Price.list(
                active=True,
                expand=['data.product'],
                limit=100
            )
        
        # Format plans
        plans = []
        for price in prices.data:
            if price.type == 'recurring' and hasattr(price, 'product') and price.product:
                product = price.product
                
                # Get features from product metadata or description
                features = []
                if hasattr(product, 'metadata') and 'features' in product.metadata:
                    features = product.metadata['features'].split(',')
                
                plans.append({
                    'name': product.name,
                    'price_id': price.id,
                    'price': price.unit_amount / 100,  # Convert from cents
                    'interval': price.recurring.interval,
                    'description': product.description or '',
                    'features': features
                })
        
        # Sort plans in the correct order: Basic, Professional, Enterprise
        plan_order = {"Basic": 1, "Professional": 2, "Enterprise": 3}
        plans.sort(key=lambda x: plan_order.get(x['name'], 999))
        
        return plans
    except Exception as e:
        logger.exception(f"Error fetching plans from Stripe: {str(e)}")
        return []

def create_checkout_session(price_id, success_path, cancel_path):
    """
    Create a Stripe checkout session.
    
    Args:
        price_id (str): The Stripe price ID
        success_path (str): URL path for success redirect
        cancel_path (str): URL path for cancel redirect
        
    Returns:
        str: The checkout URL or None if failed
    """
    try:
        # Get the customer from the session
        user_id = session.get('user_id')
        if not user_id:
            return None
            
        from app import db
        from models import Customer
        
        customer = Customer.query.get(user_id)
        if not customer:
            return None
            
        # Create or retrieve Stripe customer
        stripe_customer = None
        if customer.stripe_customer_id:
            # Retrieve existing customer
            try:
                stripe_customer = stripe.Customer.retrieve(customer.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                # Customer doesn't exist in Stripe, create a new one
                stripe_customer = None
                customer.stripe_customer_id = None
                db.session.commit()
                
        if not stripe_customer or not customer.stripe_customer_id:
            # Create new Stripe customer
            stripe_customer = stripe.Customer.create(
                email=customer.email,
                name=customer.username,
                metadata={'user_id': user_id}
            )
            customer.stripe_customer_id = stripe_customer.id
            db.session.commit()
            
        # Create checkout session
        domain = request.host_url.rstrip('/')
        
        # Add detailed logging
        logger.info(f"Creating checkout session for customer ID: {customer.stripe_customer_id}")
        logger.info(f"Using price ID: {price_id}")
        logger.info(f"Success URL: {domain}{success_path}")
        logger.info(f"Cancel URL: {domain}{cancel_path}")
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                mode='subscription',
                success_url=f"{domain}{success_path}",
                cancel_url=f"{domain}{cancel_path}",
                automatic_tax={'enabled': True}
            )
            
            logger.info(f"Checkout session created successfully: {checkout_session.id}")
            return checkout_session.url
        except stripe.error.StripeError as se:
            # Specific Stripe error handling
            logger.error(f"Stripe API error: {se.__class__.__name__}: {str(se)}")
            return None
    except Exception as e:
        logger.exception(f"Error creating checkout session: {str(e)}")
        return None
        
def create_portal_session(return_path):
    """
    Create a Stripe customer portal session.
    
    Args:
        return_path (str): URL path to return to after portal session
        
    Returns:
        str: The portal URL or None if failed
    """
    try:
        # Get the customer from the session
        user_id = session.get('user_id')
        if not user_id:
            return None
            
        from models import Customer
        
        customer = Customer.query.get(user_id)
        if not customer or not customer.stripe_customer_id:
            return None
            
        # Create portal session
        domain = request.host_url.rstrip('/')
        portal_session = stripe.billing_portal.Session.create(
            customer=customer.stripe_customer_id,
            return_url=f"{domain}{return_path}"
        )
        
        return portal_session.url
    except Exception as e:
        logger.exception(f"Error creating portal session: {str(e)}")
        return None
