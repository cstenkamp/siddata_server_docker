"""This is only for testing/debugging, in production (and also if you're not explicitly testing tf-models), there is a
docker-container instead!!"""

import os
import signal
import subprocess
import threading
from queue import Queue
from time import sleep


class TFModelServer:
    def __init__(self, port, model_name, model_base_path, silent=True):
        self.comqueue = Queue()
        self.port = port
        self.model_name = model_name
        self.model_base_path = model_base_path
        self.silent = silent
        self.shouldkill = False
        self.killed = False

    def execute(self, cmd, **kwargs):
        self.popen = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, **kwargs
        )
        # for stdout_line in iter(self.popen.stdout.readline, ""):
        #     yield stdout_line
        for stderr_line in iter(self.popen.stderr.readline, ""):
            yield stderr_line
        self.popen.stdout.close()
        return_code = self.popen.wait()
        if return_code:
            if self.shouldkill and return_code == -2:
                self.killed = True
            else:
                raise subprocess.CalledProcessError(return_code, cmd)

    def _run_server(self):
        for line in self.execute(
            f"/usr/bin/env tensorflow_model_server --rest_api_port={self.port} --model_name={self.model_name} "
            f"--model_base_path={self.model_base_path}".split(" "),
            env={"PATH": os.getenv("PATH")},
            shell=False,
        ):
            if not self.silent:
                print(line, end="")
            if "Entering the event loop" in line:
                self.comqueue.put("ready")
            elif self.killed:
                break

    def run_server(self):
        server = threading.Thread(target=self._run_server)
        server.setDaemon(True)
        server.start()
        while self.comqueue.empty():
            sleep(0.1)

    def kill_server(self):
        self.shouldkill = True
        self.popen.send_signal(signal.SIGINT)
        self.popen.wait()

    def __enter__(self):
        self.run_server()

    def __exit__(self, *args, **kwargs):
        self.kill_server()


if __name__ == "__main__":
    # THIS IS ONLY FOR TESTING!
    import time

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.development")
    from django.conf import settings

    with TFModelServer(
        port=8501,
        model_name="rm_professions",
        model_base_path=settings.BASE_DIR / "data" / "RM_professions",
        silent=False,
    ):
        print("ready")
    print("ended")
    time.sleep(1)
    print("ending all")
