"""
OpenAI-compatible API routes
Handles /v1/chat/completions and /v1/completions endpoints
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.services.key_rotator import rotator
from backend.services.fireworks_proxy import proxy
from backend.services.monitor_service import monitor
import asyncio
import json

openai_bp = Blueprint("openai", __name__)


@openai_bp.route("/v1/chat/completions", methods=["POST"])
async def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        # Get API key from rotator
        api_key = rotator.get_next_key()

        if not api_key:
            return jsonify({"error": "No API keys available"}), 503

        # Check if streaming
        stream = data.get("stream", False)

        # Get request ID from context
        request_id = getattr(request, "request_id", None)

        # Get API key ID for logging
        api_key_id = rotator._get_key_id(api_key)

        # Make request to Fireworks
        response_data, stream_gen, status_code, error_msg = await proxy.chat_completion(
            api_key=api_key, data=data, stream=stream
        )

        # Handle errors
        if status_code != 200:
            rotator.mark_key_failed(api_key, error_msg)

            # Log failed request
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=status_code,
                    error_message=error_msg,
                )

            return jsonify({"error": error_msg or "Request failed"}), status_code

        # Mark key as successful
        rotator.mark_key_success(api_key)

        # Handle streaming response
        if stream and stream_gen:

            def generate():
                try:
                    for chunk in stream_gen:
                        yield chunk
                except Exception as e:
                    print(f"Streaming error: {e}")

            # Log request (without token info for streaming)
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=200,
                )

            return Response(
                stream_with_context(generate()),
                content_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # Handle non-streaming response
        if response_data:
            # Extract token usage
            input_tokens, output_tokens, total_tokens = proxy.extract_token_usage(
                response_data
            )

            # Log request
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=200,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            return jsonify(response_data), 200

        return jsonify({"error": "Unknown error"}), 500

    except Exception as e:
        print(f"Error in chat_completions: {e}")
        return jsonify({"error": str(e)}), 500


@openai_bp.route("/v1/completions", methods=["POST"])
async def completions():
    """OpenAI-compatible completions endpoint"""
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        # Get API key from rotator
        api_key = rotator.get_next_key()

        if not api_key:
            return jsonify({"error": "No API keys available"}), 503

        # Check if streaming
        stream = data.get("stream", False)

        # Get request ID from context
        request_id = getattr(request, "request_id", None)

        # Get API key ID for logging
        api_key_id = rotator._get_key_id(api_key)

        # Make request to Fireworks
        response_data, stream_gen, status_code, error_msg = await proxy.completion(
            api_key=api_key, data=data, stream=stream
        )

        # Handle errors
        if status_code != 200:
            rotator.mark_key_failed(api_key, error_msg)

            # Log failed request
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=status_code,
                    error_message=error_msg,
                )

            return jsonify({"error": error_msg or "Request failed"}), status_code

        # Mark key as successful
        rotator.mark_key_success(api_key)

        # Handle streaming response
        if stream and stream_gen:

            def generate():
                try:
                    for chunk in stream_gen:
                        yield chunk
                except Exception as e:
                    print(f"Streaming error: {e}")

            # Log request
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=200,
                )

            return Response(
                stream_with_context(generate()),
                content_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # Handle non-streaming response
        if response_data:
            # Extract token usage
            input_tokens, output_tokens, total_tokens = proxy.extract_token_usage(
                response_data
            )

            # Log request
            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=200,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            return jsonify(response_data), 200

        return jsonify({"error": "Unknown error"}), 500

    except Exception as e:
        print(f"Error in completions: {e}")
        return jsonify({"error": str(e)}), 500
