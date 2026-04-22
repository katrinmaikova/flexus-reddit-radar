import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_bot_exec
from flexus_client_kit import ckit_shutdown
from flexus_client_kit import ckit_integrations_db
from flexus_client_kit import ckit_bot_version
from flexus_client_kit.integrations import fi_mongo_store

logger = logging.getLogger("bot_radar")

BOT_NAME = ckit_bot_version.bot_name_from_file(__file__)
RADAR_ROOTDIR = Path(__file__).parent
RADAR_SETUP_SCHEMA = json.loads((RADAR_ROOTDIR / "setup_schema.json").read_text())

RADAR_INTEGRATIONS: list[ckit_integrations_db.IntegrationRecord] = ckit_integrations_db.static_integrations_load(
    RADAR_ROOTDIR,
    allowlist=["gmail"],
    builtin_skills=[],
)

TOOLS = [
    fi_mongo_store.MONGO_STORE_TOOL,
    *[t for rec in RADAR_INTEGRATIONS for t in rec.integr_tools],
]


async def radar_main_loop(fclient: ckit_client.FlexusClient, rcx: ckit_bot_exec.RobotContext) -> None:
    setup = ckit_bot_exec.official_setup_mixing_procedure(RADAR_SETUP_SCHEMA, rcx.persona.persona_setup)
    await ckit_integrations_db.main_loop_integrations_init(RADAR_INTEGRATIONS, rcx, setup, need_mongo=True)

    @rcx.on_tool_call(fi_mongo_store.MONGO_STORE_TOOL.name)
    async def toolcall_mongo_store(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await fi_mongo_store.handle_mongo_store(rcx, toolcall, model_produced_args)

    try:
        while not ckit_shutdown.shutdown_event.is_set():
            await rcx.unpark_collected_events(sleep_if_no_work=10.0)
    finally:
        logger.info("%s exit" % (rcx.persona.persona_id,))


def main():
    from flexus_my_bots.radar import radar_install
    scenario_fn = ckit_bot_exec.parse_bot_args()
    bot_version = ckit_bot_version.read_version_file(__file__)
    fclient = ckit_client.FlexusClient(
        ckit_client.bot_service_name(BOT_NAME, bot_version),
        endpoint="/v1/jailed-bot",
    )
    asyncio.run(ckit_bot_exec.run_bots_in_this_group(
        fclient,
        bot_main_loop=radar_main_loop,
        inprocess_tools=TOOLS,
        scenario_fn=scenario_fn,
        install_func=radar_install.install,
    ))


if __name__ == "__main__":
    main()
