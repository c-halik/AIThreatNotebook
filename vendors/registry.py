from vendors.base import SecurityProvider
from vendors.mocks import VENDOR_PROFILES, MockSecurityProvider

ALL_PROVIDERS: dict[str, SecurityProvider] = {
    profile.name: MockSecurityProvider(profile) for profile in VENDOR_PROFILES
}
