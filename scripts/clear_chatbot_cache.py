import redis

# Match the URLs used in app/api/v1/chatbot.py
MAIN_REDIS_URL = "redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884"
LOG_REDIS_URL = "redis://default:ENRwPubGW1VmpdNmr5kSJG7jqW7IdyKG@redis-16098.crce185.ap-seast-1-1.ec2.redns.redis-cloud.com:16098"


def clear_pattern(r: redis.Redis, pattern: str) -> int:
    count = 0
    for key in r.scan_iter(match=pattern, count=500):
        r.delete(key)
        count += 1
    return count


def main():
    main_r = redis.Redis.from_url(MAIN_REDIS_URL)
    log_r = redis.Redis.from_url(LOG_REDIS_URL)

    deleted = 0
    deleted += clear_pattern(main_r, "chatbot:*")
    deleted += clear_pattern(main_r, "chatbot_history:*")
    deleted += clear_pattern(log_r, "chatbotlog:*")

    print(f"Deleted {deleted} Redis keys across chatbot caches")


if __name__ == "__main__":
    main()


