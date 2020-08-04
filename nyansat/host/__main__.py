import asyncio
import logging

import argparse
from typing import Optional

from rbs_tui_dom.dom import DOMWindow
from rbs_tui_dom.dom.layout import DOMStackLayout
from rbs_tui_dom.dom.style import DOMStyle, Color, Alignment, Margin, Display
from rbs_tui_dom.dom.text import DOMText, DOMTextFill
from rbs_tui_dom.dom.types import HORIZONTAL, FULL_WIDTH, FULL_SIZE, VERTICAL

from nyansat.host.client import NyanSatTelemetryClient
from nyansat.host.dom.dom_shell import DOMNyanSatShell
from nyansat.host.view.root import RootView
from nyansat.host.view.telemetry import TelemetryView

ASCII_HEADER = r"""
:    * .        :   .              :    (  \                   ,--——.’.       .                 ,—‘’’——,  *                 *   :  .   *  +  
      .      +             :           * )  )                / /\__/|\           +     :       /___/c/___\       :     ..     +              
       .          .    . *              (  (   .——— ‘’’’———.| | o_o | |     /////////////////||/  / |\    |//////////////////          .    :
     *          :   .                  * \  \/               \ \_^_/_/     //////////////////| \\ / | \   ///////////////////  *   +         
 :      .      +     .         +    :     \    \                /         //////////////////|| ‘\__| _\///////////////////           .  *    
                 :         :              /    | ‘’’————.      /                             |   /::::://         :       .      . *         
        .            .                  */   //          |    |]      :         ..           “, / ::::// :   .   .  +                        
:    * .            .         .         /___,))          |___,))       .  +                    /_ ,,//        .     +         :    :         
"""

ASCII_DISCONNECTED = r"""

___  ___      ___       ___ ___  __ _   ,         __  ___    ___        _    __       ___  __
 |  |__  |   |__  |\/| |__   |  |_/  \ /    |\ | /  \  |    |__  |\ |  /_\  |_/  |   |__  |  \
 |  |___ |__ |___ |  | |___  |  | \   |     | \| \__/  |    |___ | \| /   \ |_\  |__ |___ |__/
 
 ----------------- Run `setup config.json` in the shell and enable Telemetry -----------------

"""


def create_dom_terminal_help_item(shortcut: str, description: str):
    return DOMStackLayout(orientation=HORIZONTAL, style=DOMStyle(size=(FULL_WIDTH, 1)), children=[
        DOMText(shortcut, style=DOMStyle(
            size=(2, 1),
            margin=Margin(right=1),
            color=Color.BLACK,
            background_color=Color.WHITE,
        )),
        DOMText(description, style=DOMStyle(size=(FULL_WIDTH, 1)))
    ])


def create_dom(shell: DOMNyanSatShell):
    return DOMStackLayout(id="window", style=DOMStyle(background_color=Color.BLACK), children=[
        DOMStackLayout(
            orientation=HORIZONTAL,
            style=DOMStyle(size=(FULL_WIDTH, 9)),
            id="header_container",
            children=[
                DOMText(
                    ASCII_HEADER.split("\n"),
                    style=DOMStyle(size=FULL_SIZE, text_align=Alignment.CENTER)
                ),
            ]
        ),
        DOMTextFill("═", style=DOMStyle(size=(FULL_WIDTH, 1))),
        DOMStackLayout(style=DOMStyle(size=FULL_SIZE), children=[
            DOMStackLayout(
                orientation=VERTICAL,
                style=DOMStyle(size=FULL_SIZE, display=Display.NONE, text_align=Alignment.CENTER),
                id="disconnected_container",
                children=[
                    DOMTextFill(" ", style=DOMStyle(size=(FULL_WIDTH, 5))),
                    DOMText(
                        ASCII_DISCONNECTED.split("\n"),
                        style=DOMStyle(size=FULL_SIZE)
                    )
                ]
            ),
            DOMStackLayout(
                orientation=VERTICAL,
                style=DOMStyle(size=FULL_SIZE, display=Display.NONE),
                id="telemetry_container",
                children=[
                    DOMText(
                        "Network",
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1))
                    ),
                    DOMTextFill("-", style=DOMStyle(size=(FULL_WIDTH, 1))),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "IP Address",
                                style=DOMStyle(text_align=Alignment.LEFT, size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="ip_value",
                                style=DOMStyle(text_align=Alignment.RIGHT,
                                               size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "UDP Port",
                                style=DOMStyle(text_align=Alignment.LEFT, size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="port_value",
                                style=DOMStyle(text_align=Alignment.RIGHT,
                                               size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMTextFill("═", style=DOMStyle(size=(FULL_WIDTH, 1))),
                    DOMText(
                        "GPS",
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1))
                    ),
                    DOMTextFill("-", style=DOMStyle(size=(FULL_WIDTH, 1))),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "Coordinates",
                                style=DOMStyle(text_align=Alignment.LEFT, size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="gps_coordinates_value",
                                style=DOMStyle(text_align=Alignment.RIGHT, size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "Altitude",
                                style=DOMStyle(text_align=Alignment.LEFT, size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="gps_altitude_value",
                                style=DOMStyle(text_align=Alignment.RIGHT, size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "Speed",
                                style=DOMStyle(text_align=Alignment.LEFT,
                                               size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="gps_speed_value",
                                style=DOMStyle(text_align=Alignment.RIGHT,
                                               size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMTextFill("═", style=DOMStyle(size=(FULL_WIDTH, 1))),
                    DOMText("Antenna", style=DOMStyle(text_align=Alignment.CENTER,
                                                      size=(FULL_WIDTH, 1))),
                    DOMTextFill("-", style=DOMStyle(size=(FULL_WIDTH, 1))),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "Azimuth",
                                style=DOMStyle(text_align=Alignment.LEFT,
                                               size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="antenna_azimuth",
                                style=DOMStyle(text_align=Alignment.RIGHT,
                                               size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                    DOMStackLayout(
                        orientation=HORIZONTAL,
                        style=DOMStyle(text_align=Alignment.CENTER, size=(FULL_WIDTH, 1)),
                        children=[
                            DOMText(
                                "Elevation",
                                style=DOMStyle(text_align=Alignment.LEFT,
                                               size=(FULL_WIDTH, 1))
                            ),
                            DOMText(
                                "",
                                id="antenna_elevation",
                                style=DOMStyle(text_align=Alignment.RIGHT, size=(FULL_WIDTH, 1))
                            )
                        ]
                    ),
                ]
            ),
        ]),
        DOMTextFill("-", style=DOMStyle(size=(FULL_WIDTH, 1))),
        shell
   ])


async def run(server_port: int):
    logging.basicConfig(
        filename='hacksat_ui.log',
        level=logging.getLevelName("INFO"),
        format="%(asctime)s.%(msecs)03d:%(levelname)s:%(name)s:%(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
    )
    try:
        loop = asyncio.get_event_loop()
        client = NyanSatTelemetryClient(loop, server_port)

        shell = DOMNyanSatShell(id="shell", style=DOMStyle(size=(FULL_WIDTH, 15)))
        window = DOMWindow(disable_click=True)
        await window.run(create_dom(shell))
        dom_console = window.get_element_by_id("shell")
        dom_console.focus()
        shell.start_shell()

        RootView(window, client)
        TelemetryView(window, client)
        await client.start()
    except:
        logging.error("Failed to launch", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A TUI for the nyansat station.')
    parser.add_argument(
        '--port',
        type=int,
        default=31337,
        help='The port on which the UDP server should be listening'
    )
    args = parser.parse_args()

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(run(args.port))
    event_loop.run_forever()
