import asyncio
import sys

from rbs_tui_dom.dom import VERTICAL
from rbs_tui_dom.extra.terminal import DOMShell


class DOMNyanSatShell(DOMShell):
    async def _run_command(
            self,
            command: str,
    ):
        await super()._run_command(command)
        sys.exit(0)

    def start_shell(self):
        asyncio.ensure_future(self._run_command("python3 -m nyansat.host.shell"))
        self._input.enable_task_mode(render=False)
        self._input.set_value("", render=True)
        self.move_min(VERTICAL)