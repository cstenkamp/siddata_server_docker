import os
from contextlib import nullcontext

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.development")
get_wsgi_application()
from django.conf import settings  # noqa: E402

from apps.backend.util.tf_model_server import TFModelServer  # noqa: E402
from apps.recommenders.RM_professions import BertPredictor  # noqa: E402


def test_machinelearning_ddc():
    goal = "Machine Learning"
    with (
        TFModelServer(8501, "rm_professions", model_base_path=settings.BASE_DIR / "data" / "RM_professions")
        if settings.TF_SERVING_HOST == "localhost"
        else nullcontext()
    ):
        predictor = BertPredictor()
        res = predictor.predict(goal)
        assert int(max(res.items(), key=lambda x: x[1])[0]) == 63
