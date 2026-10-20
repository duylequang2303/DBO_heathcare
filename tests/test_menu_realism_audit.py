from scripts.audit_menu_realism import reasons_for


def test_flags_obvious_non_standalone_items():
    assert "oil_or_shortening" in reasons_for("ALL-VEGETABLE SHORTENING", 100)
    assert "ingredient_or_component" in reasons_for("ARTISAN WOOD-FIRED CRUST", 100)
    assert "sauce_or_seasoning" in reasons_for("BARBECUE SAUCE", 100)


def test_does_not_flag_obvious_normal_food():
    assert reasons_for("Cơm trắng", 150) == []
