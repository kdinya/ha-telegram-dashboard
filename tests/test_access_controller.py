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
