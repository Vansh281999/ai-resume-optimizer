import os

icons_dir = r"C:\Users\Asus\Downloads\repo changes\ai-resume-optimizer\frontend\public\icons"
os.makedirs(icons_dir, exist_ok=True)

svgs = {
    "favicon-ai-hat.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#4f46e5"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<path d="M32 14 L20 28 H44 Z" fill="white" opacity="0.9"/>'
        '<rect x="22" y="28" width="20" height="12" rx="3" fill="white" opacity="0.95"/>'
        '<rect x="26" y="40" width="12" height="10" rx="2" fill="white" opacity="0.8"/>'
        '<circle cx="32" cy="19" r="3" fill="#4f46e5"/>'
        "</svg>"
    ),
    "favicon-resume-ai.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#4f46e5"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<rect x="16" y="10" width="32" height="44" rx="4" fill="white" opacity="0.95"/>'
        '<rect x="22" y="18" width="20" height="2" rx="1" fill="#4f46e5"/>'
        '<rect x="22" y="24" width="20" height="2" rx="1" fill="#4f46e5"/>'
        '<rect x="22" y="30" width="16" height="2" rx="1" fill="#4f46e5"/>'
        '<circle cx="44" cy="42" r="8" fill="white"/>'
        '<path d="M44 38v8M40 42h8" stroke="#4f46e5" stroke-width="2" stroke-linecap="round"/>'
        "</svg>"
    ),
    "favicon-career-growth.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#10b981"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<path d="M14 50 L26 38 L34 44 L50 24" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="26" cy="38" r="3" fill="white"/>'
        '<circle cx="34" cy="44" r="3" fill="white"/>'
        '<circle cx="50" cy="24" r="4" fill="#10b981" stroke="white" stroke-width="2"/>'
        "</svg>"
    ),
    "favicon-ats-optimize.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#f59e0b"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<path d="M20 44 L28 28 L36 36 L44 20" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="28" cy="28" r="3" fill="white"/>'
        '<circle cx="36" cy="36" r="3" fill="white"/>'
        '<circle cx="44" cy="20" r="4" fill="#f59e0b" stroke="white" stroke-width="2"/>'
        '<path d="M12 52h40" stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
        "</svg>"
    ),
    "favicon-abstract-ai.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#8b5cf6"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<circle cx="24" cy="28" r="6" fill="none" stroke="white" stroke-width="2"/>'
        '<circle cx="40" cy="28" r="6" fill="none" stroke="white" stroke-width="2"/>'
        '<path d="M20 44c0-6 4-10 12-10s12 4 12 10" fill="none" stroke="white" stroke-width="2" stroke-linecap="round"/>'
        '<path d="M30 10v4M34 10v4" stroke="white" stroke-width="2" stroke-linecap="round"/>'
        "</svg>"
    ),
    "favicon.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#4f46e5"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="64" height="64" rx="14" fill="url(#g)"/>'
        '<path d="M32 14 L20 28 H44 Z" fill="white" opacity="0.9"/>'
        '<rect x="22" y="28" width="20" height="12" rx="3" fill="white" opacity="0.95"/>'
        '<rect x="26" y="40" width="12" height="10" rx="2" fill="white" opacity="0.8"/>'
        '<circle cx="32" cy="19" r="3" fill="#4f46e5"/>'
        "</svg>"
    ),
    "icon-192.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#4f46e5"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="192" height="192" rx="42" fill="url(#g)"/>'
        '<path d="M96 42 L60 84 H132 Z" fill="white" opacity="0.9"/>'
        '<rect x="66" y="84" width="60" height="36" rx="9" fill="white" opacity="0.95"/>'
        '<rect x="78" y="120" width="36" height="30" rx="6" fill="white" opacity="0.8"/>'
        '<circle cx="96" cy="57" r="9" fill="#4f46e5"/>'
        "</svg>"
    ),
    "icon-512.svg": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        "<defs>"
        '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#111827"/>'
        '<stop offset="1" stop-color="#4f46e5"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="512" height="512" rx="112" fill="url(#g)"/>'
        '<path d="M256 112 L160 224 H352 Z" fill="white" opacity="0.9"/>'
        '<rect x="176" y="224" width="160" height="96" rx="24" fill="white" opacity="0.95"/>'
        '<rect x="208" y="320" width="96" height="80" rx="16" fill="white" opacity="0.8"/>'
        '<circle cx="256" cy="152" r="24" fill="#4f46e5"/>'
        "</svg>"
    ),
}

for name, content in svgs.items():
    path = os.path.join(icons_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", name)
