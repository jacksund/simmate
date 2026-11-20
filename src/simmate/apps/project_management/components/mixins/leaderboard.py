from functools import cached_property

from ...models import Leaderboard


class LeaderboardInput:
    @cached_property
    def leaderboard_options(self) -> list[tuple[int, str]]:
        # Child leaderboards are shown with their parent (e.g. "Phone
        # Batteries › Gaming Phone Batteries") because short names can repeat
        # across the tree
        leaderboards = Leaderboard.objects.select_related("parent_leaderboard").only(
            "name", "parent_leaderboard__name"
        )
        options = [
            (
                board.id,
                f"{board.parent_leaderboard.name} › {board.name}"
                if board.parent_leaderboard
                else board.name,
            )
            for board in leaderboards
        ]
        return sorted(options, key=lambda option: option[1])
