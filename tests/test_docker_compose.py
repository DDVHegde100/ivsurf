"""Validate Docker Compose configuration files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestDockerCompose:
    def test_base_compose_has_ui_and_api(self):
        text = (ROOT / "docker-compose.yml").read_text()
        assert "ui:" in text
        assert "api:" in text
        assert "ivsurf_data:" in text

    def test_postgres_overlay(self):
        text = (ROOT / "docker-compose.postgres.yml").read_text()
        assert "postgres:" in text
        assert "IVSURF_DATABASE_URL" in text

    def test_dockerfile_and_requirements(self):
        assert (ROOT / "Dockerfile").exists()
        assert (ROOT / "requirements-docker.txt").exists()
        dockerfile = (ROOT / "Dockerfile").read_text()
        assert "requirements-docker.txt" in dockerfile

    def test_compose_up_script_exists(self):
        script = ROOT / "scripts" / "compose-up.sh"
        assert script.exists()
        assert "docker compose" in script.read_text()
