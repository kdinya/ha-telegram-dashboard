"""Test localization dictionary parity and default language configuration."""
import json
import re
import subprocess
from pathlib import Path
from telegram_dashboard.src.config_manager import DEFAULT_CONFIG


def test_default_config_language():
    assert "language" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["language"] == "en"


def test_i18n_dictionary_parity_and_completeness():
    ui_dir = Path(__file__).resolve().parent.parent / "telegram_dashboard" / "src" / "ui"
    i18n_path = ui_dir / "i18n.js"
    assert i18n_path.exists(), "i18n.js must exist"

    # Use node to extract TRANSLATIONS object as JSON
    script = """
    const fs = require('fs');
    const content = fs.readFileSync(process.argv[1], 'utf8');
    const sandbox = { window: {}, document: {}, localStorage: { getItem: () => null, setItem: () => {} } };
    const vm = require('vm');
    vm.createContext(sandbox);
    vm.runInContext(content, sandbox);
    const trans = sandbox.window.I18N.TRANSLATIONS;
    console.log(JSON.stringify(trans));
    """
    res = subprocess.run(
        ["node", "-e", script, str(i18n_path)],
        capture_output=True,
        text=True,
        check=True
    )
    translations = json.loads(res.stdout)

    assert "en" in translations, "English dictionary must exist"
    assert "uk" in translations, "Ukrainian dictionary must exist"

    en_keys = set(translations["en"].keys())
    uk_keys = set(translations["uk"].keys())

    missing_in_uk = en_keys - uk_keys
    missing_in_en = uk_keys - en_keys

    assert not missing_in_uk, f"Keys missing in UK: {missing_in_uk}"
    assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
    assert len(en_keys) >= 60, "Must have comprehensive localization dictionary"

    # Ensure no empty strings
    for lang, dict_data in translations.items():
        for k, v in dict_data.items():
            assert v and isinstance(v, str) and v.strip(), f"Empty translation for {lang}.{k}"


def test_html_includes_i18n_and_language_selector():
    index_path = Path(__file__).resolve().parent.parent / "telegram_dashboard" / "src" / "ui" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    assert "ui/i18n.js" in html
    assert 'id="setting-language"' in html
    assert 'value="en"' in html
    assert 'value="uk"' in html
