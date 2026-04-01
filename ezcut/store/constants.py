"""ezcut 전역에서 사용되는 상수 정의."""

# Mattermost UI Selectors (Selenium)
MM_BROWSER_VIEW_XPATH = "//a[normalize-space()='브라우저에서 보기']"
MM_LOGIN_EMAIL_SELECTOR = "input#input_loginId"
MM_LOGIN_PASSWORD_SELECTOR = "input#input_password-input"
MM_LOGIN_SUBMIT_SELECTOR = "button#saveSetting"

# Mattermost API / URL
MM_BASE_URL = "https://meeting.ssafy.com"
MM_ADD_PATH = "s14public/emoji/add"

# Gallery API (Cloudflare Worker 프록시)
GALLERY_API_BASE = "https://ezcut-proxy.kangseunghun9927.workers.dev"
GALLERY_API_KEY = "ezcut-public-gallery-v1"
GALLERY_PAGES_BASE = "https://{owner}.github.io/{repo}"
DEFAULT_GALLERY_REPO = "S-P-A-N/ezcut-gallery"

# History & Config
DEFAULT_TILE_SIZE = 128
DEFAULT_MAX_FILE_SIZE_KB = 512
