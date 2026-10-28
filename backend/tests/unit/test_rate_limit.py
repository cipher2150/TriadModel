from app.api.middleware import RateLimitMiddleware


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def limiter(per_minute: int, clock: Clock) -> RateLimitMiddleware:
    return RateLimitMiddleware(app=None, per_minute=per_minute, clock=clock)  # type: ignore[arg-type]


def test_requests_over_the_limit_are_blocked_until_the_window_slides() -> None:
    clock = Clock()
    rl = limiter(2, clock)
    assert rl._check("a") is None
    assert rl._check("a") is None
    assert rl._check("a") == 60
    clock.now += 30
    assert rl._check("a") == 30
    clock.now += 31
    assert rl._check("a") is None


def test_clients_are_limited_independently() -> None:
    rl = limiter(1, Clock())
    assert rl._check("a") is None
    assert rl._check("b") is None
    assert rl._check("a") is not None


def test_stale_clients_are_swept_to_bound_memory() -> None:
    clock = Clock()
    rl = limiter(5, clock)
    rl.MAX_TRACKED_CLIENTS = 3
    for name in "abcd":
        rl._check(name)
    clock.now += 120
    rl._check("fresh")
    assert set(rl.hits) == {"fresh"}
