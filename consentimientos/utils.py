import json
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers import (
    bytes_to_base64url,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment,
    UserVerificationRequirement,
)
from .models import WebAuthnCredential

RP_NAME = "AlexaTotal Informed Consent"

def get_rp_id(request):
    # Obtener el host sin el puerto
    return request.get_host().split(':')[0]

def get_origin(request):
    # WebAuthn requiere el protocolo exacto
    protocol = "https" if request.is_secure() else "http"
    return f"{protocol}://{request.get_host()}"

def get_registration_options(user, request):
    try:
        rp_info = {
            'id': get_rp_id(request),
            'name': RP_NAME,
        }
        print(f"[DEBUG] RP INFO: {rp_info}")
        options = generate_registration_options(
            rp_id=rp_info['id'],
            rp_name=rp_info['name'],
            user_id=str(user.id).encode(),
            user_name=user.username,
            exclude_credentials=[
                {"id": base64url_to_bytes(c.credential_id), "type": "public-key"}
                for c in user.webauthn_credentials.all()
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                user_verification=UserVerificationRequirement.DISCOURAGED,
            ),
        )
        return json.loads(options_to_json(options))
    except Exception as e:
        print(f"[ERROR] generate_registration_options: {traceback.format_exc()}")
        raise e


def verify_registration(user, registration_response, expected_challenge, request):
    rp_id = get_rp_id(request)
    origin = get_origin(request)
    
    verification = verify_registration_response(
        credential=registration_response,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_origin=origin,
        expected_rp_id=rp_id,
        require_user_verification=False,
    )
    
    WebAuthnCredential.objects.create(
        user=user,
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=bytes_to_base64url(verification.credential_public_key),
        sign_count=verification.sign_count,
    )
    return True

def get_auth_options(user, request):
    rp_id = get_rp_id(request)
    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=[
            {"id": base64url_to_bytes(c.credential_id), "type": "public-key"}
            for c in user.webauthn_credentials.all()
        ],
        user_verification=UserVerificationRequirement.DISCOURAGED,
    )
    return json.loads(options_to_json(options))

def verify_auth(user, auth_response, expected_challenge, request):
    rp_id = get_rp_id(request)
    origin = get_origin(request)
    
    credential = user.webauthn_credentials.get(
        credential_id=auth_response["id"]
    )
    
    verification = verify_authentication_response(
        credential=auth_response,
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_origin=origin,
        expected_rp_id=rp_id,
        credential_public_key=base64url_to_bytes(credential.public_key),
        credential_current_sign_count=credential.sign_count,
        require_user_verification=False,
    )
    
    credential.sign_count = verification.new_sign_count
    credential.save()
    return True
