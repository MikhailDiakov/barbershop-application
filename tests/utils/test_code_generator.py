def test_generate_verification_code():
    from app.utils.code_generator import generate_verification_code

    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()

    code8 = generate_verification_code(8)
    assert len(code8) == 8
    assert code8.isdigit()
