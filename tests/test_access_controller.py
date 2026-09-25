from telegram_dashboard.src.access_controller import AccessController


def test_access_controller_roles():
    users = [
        {"telegram_id": 1, "name": "Admin User", "role": "admin"},
        {"telegram_id": 2, "name": "Member User", "role": "member"},
    ]
    ac = AccessController(users, default_role="guest")

    assert ac.role_of(1) == "admin"
    assert ac.role_of(2) == "member"
    assert ac.role_of(999) == "guest"

    # Admin section
    admin_section = {"roles": ["admin"]}
    assert ac.check_section(1, "system", admin_section).allowed is True
    assert ac.check_section(2, "system", admin_section).allowed is False
    assert ac.check_section(999, "system", admin_section).allowed is False

    # Member action check
    reboot_action = {"id": "reboot", "min_role": "admin"}
    assert ac.check_action(1, reboot_action).allowed is True
    assert ac.check_action(2, reboot_action).allowed is False


def test_access_controller_fail_closed_whitelist():
    user = {
        "telegram_id": 50,
        "name": "Restricted User",
        "role": "member",
        "allowed_domains": ["light"],
        "allowed_areas": ["living_room"],
        "allowed_labels": ["guest_safe"],
    }
    ac = AccessController([user])

    # Domain mismatch / missing
    res = ac.check_entity(50, "switch.boiler", domain="switch", area="living_room", labels=["guest_safe"])
    assert res.allowed is False

    # Domain inferred from entity_id when domain is None
    res = ac.check_entity(50, "switch.boiler", domain=None, area="living_room", labels=["guest_safe"])
    assert res.allowed is False

    # Domain matches, but area is None -> must be DENIED (fail-closed)
    res = ac.check_entity(50, "light.kitchen", domain="light", area=None, labels=["guest_safe"])
    assert res.allowed is False

    # Area mismatch
    res = ac.check_entity(50, "light.kitchen", domain="light", area="kitchen", labels=["guest_safe"])
    assert res.allowed is False

    # Labels missing when allowed_labels is set -> must be DENIED (fail-closed)
    res = ac.check_entity(50, "light.lamp", domain="light", area="living_room", labels=None)
    assert res.allowed is False

    # All match -> allowed
    res = ac.check_entity(50, "light.lamp", domain="light", area="living_room", labels=["guest_safe"])
    assert res.allowed is True


def test_access_controller_reload_replaces_roles_and_restrictions():
    ac = AccessController([{"telegram_id": 7, "role": "admin"}])
    assert ac.role_of(7) == "admin"
    ac.reload([{"telegram_id": 7, "role": "guest", "blocked_entities": ["light.secret"]}])
    assert ac.role_of(7) == "guest"
    assert ac.check_entity(7, "light.secret", domain="light").allowed is False
