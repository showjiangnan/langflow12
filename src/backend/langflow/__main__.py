import multiprocessing
import platform
from pathlib import Path

import typer
from fastapi.staticfiles import StaticFiles

from langflow.main import create_app
from langflow.settings import settings
from langflow.utils.logger import configure

app = typer.Typer()


def get_number_of_workers(workers=None):
    if workers == -1:
        workers = (multiprocessing.cpu_count() * 2) + 1
    return workers


def update_settings(config: str):
    """Update the settings from a config file."""
    if config:
        settings.update_from_yaml(config)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to."),
    workers: int = typer.Option(1, help="Number of worker processes."),
    timeout: int = typer.Option(60, help="Worker timeout in seconds."),
    port: int = typer.Option(7860, help="Port to listen on."),
    config: str = typer.Option("config.yaml", help="Path to the configuration file."),
    log_level: str = typer.Option("info", help="Logging level."),
    log_file: Path = typer.Option("logs/langflow.log", help="Path to the log file."),
):
    """
    Run the Langflow server.
    """

    configure(log_level=log_level, log_file=log_file)
    update_settings(config)
    app = create_app()
    # get the directory of the current file
    path = Path(__file__).parent
    static_files_dir = path / "frontend"
    app.mount(
        "/",
        StaticFiles(directory=static_files_dir, html=True),
        name="static",
    )
    options = {
        "bind": f"{host}:{port}",
        "workers": get_number_of_workers(workers),
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout": timeout,
    }

    if platform.system() in ["Darwin", "Windows"]:
        # Run using uvicorn on MacOS and Windows
        # Windows doesn't support gunicorn
        # MacOS requires an env variable to be set to use gunicorn
        import uvicorn

        uvicorn.run(app, host=host, port=port, log_level=log_level)
    else:
        from langflow.server import LangflowApplication

        LangflowApplication(app, options).run()


def main():
    app()


if __name__ == "__main__":
    main()
