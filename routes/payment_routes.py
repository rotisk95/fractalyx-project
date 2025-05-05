import os
import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from models import Customer, Subscription, SubscriptionTier
from payment.stripe_utils import get_subscription_plans, create_checkout_session, create_portal_session
from routes.auth_routes import login_required

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/pricing')
def pricing():
    """Pricing page with subscription plans"""
    try:
        # Get plans from Stripe
        plans = get_subscription_plans()
        
        # If no plans from Stripe, create them
        if not plans:
            # Create default plans and get them again
            from payment.stripe_utils import create_default_plans
            logger.info("Creating default subscription plans in Stripe")
            try:
                create_default_plans()
                # Try to fetch plans again
                plans = get_subscription_plans()
            except Exception as e:
                logger.exception(f"Error creating plans: {str(e)}")
        
        return render_template('pricing.html', plans=plans)
    except Exception as e:
        logger.exception(f"Error in pricing route: {str(e)}")
        flash(f"An error occurred while loading pricing plans: {str(e)}", "danger")
        return render_template('pricing.html', plans=[])

@payment_bp.route('/create-checkout-session/<price_id>')
@login_required
def create_checkout_session_route(price_id):
    """Create a Stripe checkout session"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash("You must be logged in to subscribe", "danger")
            return redirect(url_for('auth_bp.login'))
        
        customer = Customer.query.get(user_id)
        if not customer:
            flash("User not found", "danger")
            return redirect(url_for('auth_bp.login'))
        
        # Create checkout session
        logger.info(f"Attempting to create checkout session for price_id: {price_id}")
        checkout_url = create_checkout_session(
            price_id=price_id,
            success_path=url_for('payment_bp.success'),
            cancel_path=url_for('payment_bp.cancel')
        )
        
        if not checkout_url:
            error_msg = "Failed to create checkout session. Please try again or contact support."
            logger.error(f"Checkout session creation failed for user {user_id}, price_id: {price_id}")
            flash(error_msg, "danger")
            return redirect(url_for('payment_bp.pricing'))
        
        return redirect(checkout_url)
    except Exception as e:
        logger.exception(f"Error creating checkout session: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('payment_bp.pricing'))

@payment_bp.route('/success')
@login_required
def success():
    """Payment success page"""
    return render_template('success.html')

@payment_bp.route('/cancel')
def cancel():
    """Payment cancelled page"""
    return render_template('cancel.html')

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook endpoint"""
    try:
        event = None
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        try:
            import stripe
            webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
            if webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            else:
                # For testing without webhook signature verification
                data = json.loads(payload)
                event = {'type': data.get('type'), 'data': data.get('data')}
        except Exception as e:
            logger.exception(f"Error verifying webhook signature: {str(e)}")
            return jsonify({'error': str(e)}), 400
        
        event_type = event['type']
        data = event['data']['object']
        
        # Handle different webhook events
        if event_type == 'checkout.session.completed':
            handle_checkout_completed(data)
        elif event_type == 'customer.subscription.updated':
            handle_subscription_updated(data)
        elif event_type == 'customer.subscription.deleted':
            handle_subscription_deleted(data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 400

def handle_checkout_completed(data):
    """Handle checkout.session.completed event"""
    try:
        customer_id = data.get('customer')
        subscription_id = data.get('subscription')
        
        if not customer_id or not subscription_id:
            return
        
        # Check if customer exists in our database
        customer = Customer.query.filter_by(stripe_customer_id=customer_id).first()
        
        if not customer:
            logger.warning(f"Customer with Stripe ID {customer_id} not found in database")
            return
        
        # Create new subscription
        subscription = Subscription(
            customer_id=customer.id,
            stripe_subscription_id=subscription_id,
            tier=SubscriptionTier.PROFESSIONAL,  # Default tier, will be updated
            active=True
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        logger.info(f"Created new subscription {subscription_id} for customer {customer_id}")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error handling checkout completed: {str(e)}")

def handle_subscription_updated(data):
    """Handle customer.subscription.updated event"""
    try:
        subscription_id = data.get('id')
        status = data.get('status')
        
        if not subscription_id:
            return
        
        # Update subscription in our database
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found in database")
            return
        
        # Update status
        subscription.active = status in ['active', 'trialing']
        
        db.session.commit()
        
        logger.info(f"Updated subscription {subscription_id} status to {status}")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error handling subscription updated: {str(e)}")

def handle_subscription_deleted(data):
    """Handle customer.subscription.deleted event"""
    try:
        subscription_id = data.get('id')
        
        if not subscription_id:
            return
        
        # Update subscription in our database
        subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
        
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found in database")
            return
        
        # Mark as inactive
        subscription.active = False
        
        db.session.commit()
        
        logger.info(f"Marked subscription {subscription_id} as inactive")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error handling subscription deleted: {str(e)}")
