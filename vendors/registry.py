import config
from vendors.base import SecurityProvider
from vendors.mocks import VENDOR_PROFILES, MockSecurityProvider
from vendors.crowdstrike import CrowdStrikeAIDRProvider
from vendors.prisma_airs import PrismaAirsProvider
from vendors.zscaler import ZscalerAIGuardProvider

ALL_PROVIDERS: dict[str, SecurityProvider] = {
    profile.name: MockSecurityProvider(profile) for profile in VENDOR_PROFILES
}

# Vendor names currently backed by a real HTTP-calling provider instead of
# the local heuristic mock. Populated below as each vendor's credentials are
# configured; the Live Vendor Test tab uses this to label vendors in the UI.
LIVE_PROVIDER_NAMES: set[str] = set()

if config.PRISMA_AIRS_API_KEY and config.PRISMA_AIRS_PROFILE_NAME:
    ALL_PROVIDERS["Prisma AIRS"] = PrismaAirsProvider(
        api_key=config.PRISMA_AIRS_API_KEY,
        profile_name=config.PRISMA_AIRS_PROFILE_NAME,
        base_url=config.PRISMA_AIRS_BASE_URL,
        app_name=config.PRISMA_AIRS_APP_NAME,
    )
    LIVE_PROVIDER_NAMES.add("Prisma AIRS")

if config.ZSCALER_AI_GUARD_API_KEY and config.ZSCALER_AI_GUARD_POLICY_ID:
    ALL_PROVIDERS["Zscaler"] = ZscalerAIGuardProvider(
        api_key=config.ZSCALER_AI_GUARD_API_KEY,
        policy_id=config.ZSCALER_AI_GUARD_POLICY_ID,
        base_url=config.ZSCALER_AI_GUARD_BASE_URL,
    )
    LIVE_PROVIDER_NAMES.add("Zscaler")

if config.CROWDSTRIKE_AIDR_TOKEN:
    ALL_PROVIDERS["CrowdStrike AIDR"] = CrowdStrikeAIDRProvider(
        token=config.CROWDSTRIKE_AIDR_TOKEN,
        base_url=config.CROWDSTRIKE_AIDR_BASE_URL,
        app_id=config.CROWDSTRIKE_AIDR_APP_ID,
    )
    LIVE_PROVIDER_NAMES.add("CrowdStrike AIDR")
