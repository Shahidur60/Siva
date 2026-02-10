from siva_guard.pipeline.next_steps import generate_next_steps


def test_next_steps_request_stronger_proof_contains_action_default():
    steps = generate_next_steps(
        action="REQUEST_STRONGER_PROOF",
        reasons=[{"code": "facebook_numeric_id_profile"}],
    )
    codes = [s["code"] for s in steps]
    assert "stronger_proof_required" in codes


def test_next_steps_reason_mapping_dedup_and_order():
    steps = generate_next_steps(
        action="REQUEST_STRONGER_PROOF",
        reasons=[
            {"code": "facebook_numeric_id_profile"},
            {"code": "facebook_numeric_id_profile"},
            {"code": "no_bio_linkouts"},
        ],
    )
    codes = [s["code"] for s in steps]
    assert len(codes) == len(set(codes))
    assert "request_in_band_confirmation" in codes
    assert "add_bio_linkout" in codes
