"""
Seedance API Webhook Handler - Vercel Serverless Function (FastAPI)
Receives generation events (image/video complete/failed) and posts to Meta + Shopify
"""

import hmac
import hashlib
import json
import os
import logging

from fastapi import FastAPI, Request, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables (set as Project Environment Variables in Vercel -- no vercel.json mapping needed)
SEEDANCE_WEBHOOK_SECRET = os.getenv('SEEDANCE_WEBHOOK_SECRET', '')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN', '')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
SHOPIFY_STORE_DOMAIN = os.getenv('SHOPIFY_STORE_DOMAIN', '')

app = FastAPI()


def verify_webhook_signature(payload_bytes, signature_header):
    """Verify HMAC-SHA256 signature using constant-time comparison"""
    if not signature_header or not SEEDANCE_WEBHOOK_SECRET:
        logger.warning("Missing signature header or webhook secret")
        return False

    expected_signature = hmac.new(
        SEEDANCE_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature_header, expected_signature)


def post_to_meta(image_url, video_url, caption):
    """Post generated content to Meta (Instagram/Facebook)"""
    try:
        import requests

        if image_url:
            endpoint = "https://graph.instagram.com/v21.0/me/media"
            data = {'image_url': image_url, 'caption': caption, 'access_token': META_ACCESS_TOKEN}
        elif video_url:
            endpoint = "https://graph.instagram.com/v21.0/me/media"
            data = {'video_url': video_url, 'caption': caption, 'access_token': META_ACCESS_TOKEN}
        else:
            return False

        response = requests.post(endpoint, data=data, timeout=10)

        if response.status_code in [200, 201]:
            logger.info("Meta post successful")
            return True
        else:
            logger.error(f"Meta post failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Meta posting error: {str(e)}")
        return False


def update_shopify_product(product_id, new_image_url):
    """Update Shopify product with generated image"""
    try:
        import requests

        endpoint = f"https://{SHOPIFY_STORE_DOMAIN}/admin/api/2023-10/products/{product_id}.json"
        headers = {'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN, 'Content-Type': 'application/json'}
        payload = {"product": {"images": [{"src": new_image_url}]}}

        response = requests.put(endpoint, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            logger.info("Shopify update successful")
            return True
        else:
            logger.error(f"Shopify update failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Shopify update error: {str(e)}")
        return False


@app.get("/")
def health_check():
    """Health check endpoint -- GET /api/seedance"""
    return {"status": "operational"}


@app.post("/")
async def handle_webhook(request: Request):
    """Webhook receiver -- POST /api/seedance"""
    body = await request.body()

    signature = request.headers.get('x-seedance-signature', '')
    if not verify_webhook_signature(body, signature):
        logger.error("Invalid webhook signature")
        return Response(
            content=json.dumps({'error': 'Invalid signature'}),
            status_code=401,
            media_type='application/json',
        )

    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError:
        return Response(
            content=json.dumps({'error': 'Invalid JSON body'}),
            status_code=400,
            media_type='application/json',
        )

    logger.info(f"Webhook: {payload.get('event_type')}")

    event_type = payload.get('event_type')
    success = True

    try:
        if event_type == 'image.generation.complete':
            image_url = payload.get('output', {}).get('url')
            product_id = payload.get('metadata', {}).get('shopify_product_id')
            caption = payload.get('metadata', {}).get('caption', 'Generated')

            if caption and image_url:
                success = post_to_meta(image_url, None, caption)
            if product_id and image_url:
                success = update_shopify_product(product_id, image_url) and success

        elif event_type == 'video.generation.complete':
            video_url = payload.get('output', {}).get('url')
            caption = payload.get('metadata', {}).get('caption', 'Generated')

            if caption and video_url:
                success = post_to_meta(None, video_url, caption)

        return {
            'status': 'success' if success else 'partial',
            'event_id': payload.get('generation_id'),
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response(
            content=json.dumps({'error': 'Internal error'}),
            status_code=500,
            media_type='application/json',
        )
