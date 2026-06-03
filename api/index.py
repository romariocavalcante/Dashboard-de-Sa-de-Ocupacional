import os
import sys
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "occupational_health.settings")


def bootstrap_vercel_sqlite() -> None:
    if not os.getenv("VERCEL"):
        return

    import django
    from django.conf import settings
    from django.core.management import call_command

    django.setup()

    db_path = Path(settings.DATABASES["default"]["NAME"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    seed_path = BASE_DIR / "db.sqlite3"
    if not db_path.exists() and seed_path.exists():
        shutil.copy2(seed_path, db_path)

    marker_path = db_path.with_suffix(".bootstrapped")
    if marker_path.exists():
        return

    call_command("collectstatic", interactive=False, verbosity=0, clear=False)
    call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)
    marker_path.write_text("ok", encoding="utf-8")


bootstrap_vercel_sqlite()

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
application = app
