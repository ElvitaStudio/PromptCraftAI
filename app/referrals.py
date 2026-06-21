REFERRAL_REWARD_DAYS = 3


def build_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username.lstrip('@')}?start=ref_{user_id}"


def parse_referral_payload(payload: str | None) -> int | None:
    if not payload or not payload.startswith("ref_"):
        return None
    try:
        user_id = int(payload.removeprefix("ref_"))
    except ValueError:
        return None
    return user_id if user_id > 0 else None


def invite_message(link: str, language: str = "ru") -> str:
    if language == "en":
        return (
            "🎁 Invite a friend and get Premium for 3 days!\n\n"
            f"Your link:\n{link}\n\n"
            "The friend must be a new user. Each referral is rewarded once."
        )
    return (
        "🎁 Пригласите друга и получите Premium на 3 дня!\n\n"
        f"Ваша ссылка:\n{link}\n\n"
        "Друг должен впервые запустить бота. "
        "Награда начисляется один раз."
    )
