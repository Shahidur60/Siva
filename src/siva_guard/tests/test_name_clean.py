from siva_guard.pipeline.name_clean import clean_display_name


def test_clean_display_name_splits_on_marker():
    assert clean_display_name("John Doe | Facebook", platform="facebook") == "John Doe"


def test_clean_display_name_handles_bullets():
    assert clean_display_name("Jane • Instagram", platform="instagram") == "Jane"


def test_clean_display_name_empty_safe():
    assert clean_display_name(None, platform="instagram") == ""
