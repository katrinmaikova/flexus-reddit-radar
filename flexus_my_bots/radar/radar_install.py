import asyncio
from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_bot_install
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_integrations_db

from flexus_my_bots.radar import radar_bot
from flexus_my_bots.radar import radar_prompts

TOOL_NAMESET = {t.name for t in radar_bot.TOOLS}

# Researcher gets python_execute + web for Reddit scraping, plus all local tools + kanban
RESEARCHER_TOOLS = ",".join(
    TOOL_NAMESET
    | ckit_cloudtool.CLOUDTOOLS_PYTHON
    | ckit_cloudtool.CLOUDTOOLS_WEB
    | ckit_cloudtool.KANBAN_ADVANCED
)

# Default interactive expert: mongo_store to read reports, python_execute for filtering/analysis + kanban
DEFAULT_TOOLS = ",".join(
    TOOL_NAMESET
    | ckit_cloudtool.CLOUDTOOLS_PYTHON
    | ckit_cloudtool.KANBAN_ADVANCED
)

EXPERTS = [
    ("default", ckit_bot_install.FMarketplaceExpertInput(
        fexp_system_prompt=radar_prompts.DEFAULT_SYSTEM_PROMPT,
        fexp_python_kernel="",
        fexp_allow_tools=DEFAULT_TOOLS,
        fexp_nature="NATURE_INTERACTIVE",
        fexp_inactivity_timeout=3600,
        fexp_description="Interactive expert for exploring past CI reports, querying competitor signals, and analyzing trends.",
    )),
    ("researcher", ckit_bot_install.FMarketplaceExpertInput(
        fexp_system_prompt=radar_prompts.RESEARCHER_SYSTEM_PROMPT,
        fexp_python_kernel="",
        fexp_allow_tools=RESEARCHER_TOOLS,
        fexp_nature="NATURE_AUTONOMOUS",
        fexp_inactivity_timeout=7200,
        fexp_description="Autonomous expert that runs the full weekly Reddit research pipeline: fetch, analyze, save, and email the CI report.",
        fexp_model_class="",
    )),
]


async def install(client: ckit_client.FlexusClient):
    r = await ckit_bot_install.marketplace_upsert_dev_bot(
        client,
        ws_id=client.ws_id,
        bot_dir=radar_bot.RADAR_ROOTDIR,
        marketable_accent_color="#1a1a2e",
        marketable_title1="Radar",
        marketable_title2="Weekly competitive intelligence from Reddit, delivered every Monday.",
        marketable_author="Flexus",
        marketable_occupation="Competitive Intelligence Analyst",
        marketable_description=(radar_bot.RADAR_ROOTDIR / "README.md").read_text(),
        marketable_typical_group="Marketing / Strategy",
        marketable_setup_default=radar_bot.RADAR_SETUP_SCHEMA,
        marketable_featured_actions=[
            {"feat_question": "What were the top signals last week?", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Show me all Tidio mentions from the past month", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Run the weekly research now", "feat_expert": "researcher", "feat_depends_on_setup": []},
        ],
        marketable_intro_message=(
            "I'm Radar — your competitive intelligence analyst. "
            "Every Monday I scan Reddit for signals relevant to Flexus and email you a structured report. "
            "You can also ask me about past reports or competitor mentions at any time."
        ),
        marketable_preferred_model_expensive="gpt-5.4",
        marketable_preferred_model_cheap="gpt-5.4-mini",
        marketable_experts=[(name, exp.filter_tools(radar_bot.TOOLS)) for name, exp in EXPERTS],
        add_integrations_into_expert_system_prompt=radar_bot.RADAR_INTEGRATIONS,
        marketable_tags=["Competitive Intelligence", "Research", "Marketing", "Strategy"],
        marketable_auth_supported=["gmail"],
        marketable_auth_scopes={
            "gmail": ckit_integrations_db.GOOGLE_OAUTH_BASE_SCOPES + [
                "https://www.googleapis.com/auth/gmail.compose",
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
        },
        marketable_schedule=[
            {
                "sched_type": "SCHED_ANY",
                "sched_when": "WEEKDAYS:MO/09:00",
                "sched_first_question": (
                    "It's Monday morning. Please run the full weekly competitive intelligence research pipeline: "
                    "fetch top posts from all 14 Reddit subreddits, run the 13 search queries, analyze all signals, "
                    "write the structured CI report, save it to storage, and email it to the recipient address in your setup."
                ),
                "sched_fexp_name": "researcher",
            }
        ],
    )
    return r.marketable_version


if __name__ == "__main__":
    client = ckit_client.FlexusClient("radar_install")
    asyncio.run(install(client))
