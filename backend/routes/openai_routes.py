"""
OpenAI-compatible API routes
Handles /v1/chat/completions and /v1/completions endpoints
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.services.key_rotator import rotator
from backend.services.fireworks_proxy import proxy
from backend.services.monitor_service import monitor

openai_bp = Blueprint("openai", __name__)


@openai_bp.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """OpenAI-compatible chat completions endpoint"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        api_key = rotator.get_next_key()

        if not api_key:
            return jsonify({"error": "No API keys available"}), 503

        request_id = getattr(request, "request_id", None)
        api_key_id = rotator._get_key_id(api_key)

        response_data, status_code, error_msg = proxy.chat_completion_sync(
            api_key=api_key, data=data
        )

        if status_code != 200:
            rotator.mark_key_failed(api_key, error_msg)

            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=status_code,
                    error_message=error_msg,
                )

            return jsonify({"error": error_msg or "Request failed"}), status_code

        rotator.mark_key_success(api_key)

        if response_data:
            input_tokens, output_tokens, total_tokens = proxy.extract_token_usage(
                response_data
            )

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
def completions():
    """OpenAI-compatible completions endpoint"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        api_key = rotator.get_next_key()

        if not api_key:
            return jsonify({"error": "No API keys available"}), 503

        request_id = getattr(request, "request_id", None)
        api_key_id = rotator._get_key_id(api_key)

        response_data, status_code, error_msg = proxy.completion_sync(
            api_key=api_key, data=data
        )

        if status_code != 200:
            rotator.mark_key_failed(api_key, error_msg)

            if request_id:
                monitor.end_request(
                    request_id=request_id,
                    api_key_id=api_key_id,
                    model=data.get("model"),
                    status_code=status_code,
                    error_message=error_msg,
                )

            return jsonify({"error": error_msg or "Request failed"}), status_code

        rotator.mark_key_success(api_key)

        if response_data:
            input_tokens, output_tokens, total_tokens = proxy.extract_token_usage(
                response_data
            )

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
