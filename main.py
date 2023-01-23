import leagueregistrar
import countdownfmt
import collections
import rlstatsdb
import countdown
import textwrap
import operator
import discord
import typing

T = typing.TypeVar("T")
GameType = typing.TypeVar("GameType")
TeamType = typing.TypeVar("TeamType")
PlayerType = typing.TypeVar("PlayerType")


# def _get_nested(obj: object, locs: typing.Iterable[str]):
#     first = locs[0]
#     _obj = getattr(obj, first)
#     if len(locs) == 1:
#         _obj
#     return _get_nested(_obj, locs[1:])


def _list_iadd(l1: list[int | float], l2: list[int | float]) -> None:
    """Add the values of `l2` to the corresponding indecies of `l1`.
    
    """
    print(l1, l2)
    if len(l1) == 0:
        return l1.extend(l2)

    lenl1 = len(l1)
    if len(l2) > len(l1):
        l2 = l2[:lenl1]
    for i, v in enumerate(l2):
        l1[i] += v


class SeriesFormatter(typing.Generic[GameType, TeamType, PlayerType]):
    def __init__(self, default_embed: dict[str, typing.Any] = None) -> None:
        self._default_embed = default_embed or dict()

    @property
    def player_stats_fmt(self) -> str:
        raise NotImplementedError()
    
    @property
    def team_stats_fmt(self) -> str:
        raise NotImplementedError()
    
    @property
    def title_fmt(self) -> str:
        raise NotImplementedError()
    
    @property
    def game_recap_fmt(self) -> str:
        raise NotImplementedError()
    
    @property
    def player_stats_header(self) -> str:
        return "**PLAYER STATISTICS**"
    
    @property
    def team_stats_header(self) -> str:
        return "**TEAM STATISTICS**"
    
    @property
    def notes_header(self) -> str | None:
        return "**NOTES**"
    
    @property
    def notes_fmt(self) -> str:
        raise NotImplementedError()
    
    def get_team_a(self, game: GameType, name: str, **kwargs) -> tuple[TeamType, str]:
        raise NotImplementedError()
    
    def get_team_b(self, game: GameType, name: str, **kwargs) -> tuple[TeamType, str]:
        raise NotImplementedError()
    
    def get_team_stats(self, team: TeamType, **kwargs) -> typing.Iterable[int | float]:
        raise NotImplementedError()
    
    def get_players(self, team: TeamType, **kwargs) -> typing.Iterable[PlayerType]:
        raise NotImplementedError()

    def get_player_stats(self, player: PlayerType, **kwargs) -> typing.Iterable[int | float]:
        raise NotImplementedError()
    
    def get_player_name(self, player: PlayerType, team_name: str, **kwargs) -> str:
        raise NotImplementedError()

    def add_player_stats(self, total_stats: list[int | float], new_stats: list[int | float],
                         **kwargs) -> None:
        _list_iadd(total_stats, new_stats)
    
    def add_team_stats(self, total_stats: list[int | float], new_stats: list[int | float],
                       **kwargs) -> None:
        _list_iadd(total_stats, new_stats)

    def format_title(self, team_a: str, team_b: str, games: typing.Iterable[GameType],
                     **kwargs) -> str:
        return self.title_fmt.format(team_a=team_a, team_b=team_b, games=games, **kwargs)
    
    def format_game_recap(self, game: GameType, team_a: str, team_b: str, **kwargs) -> str:
        raise NotImplementedError()
    
    def format_player_stats(self, total_stats: list[int | float], num_games: int, **kwargs) -> str:
        return self.player_stats_fmt.format(*total_stats)
    
    def format_team_stats(self, total_stats: list[int | float], num_games: int, **kwargs) -> str:
        return self.team_stats_fmt.format(*total_stats)
    
    def format_notes(self, **kwargs) -> str | None:
        return None

    def format(self, team_a: str, team_b: str, games: typing.Iterable[GameType],
               **kwargs) -> discord.Embed:
        game_recaps: list[str] = list()
        total_team_stats: dict[str, list[int | float]] = collections.defaultdict(list)
        total_player_stats: dict[str, list[int | float]] = collections.defaultdict(list)
        
        # process games
        for game in games:
            game_recaps.append(self.format_game_recap(game, team_a, team_b, **kwargs))

            # process each team in game
            teams = (self.get_team_a(game, team_a, **kwargs),
                     self.get_team_b(game, team_b, **kwargs))
            for team, team_name in teams:
                team_stats = self.get_team_stats(team, **kwargs)
                self.add_team_stats(total_team_stats[team_name], team_stats, **kwargs)

                # process each player in team
                players = self.get_players(team, **kwargs)
                for player in players:
                    player_name = self.get_player_name(player, team_name, **kwargs)
                    player_stats = self.get_player_stats(player, **kwargs)
                    self.add_player_stats(total_player_stats[player_name], player_stats, **kwargs)

        # create embed
        embed = discord.Embed.from_dict(self._default_embed)

        # add title
        title = self.format_title(team_a, team_b, games, **kwargs)
        if title:
            embed.title = title
        
        # add description
        formatted_recaps = "\n".join(game_recaps)
        embed.description = f"{formatted_recaps}\n\n{self.player_stats_header}"

        # add player stat data
        num_games = len(games)
        for player_name, player_stats in total_player_stats.items():
            formatted_player_stats = self.format_player_stats(player_stats, num_games, **kwargs)
            embed.add_field(name=player_name, value=formatted_player_stats, inline=True)
        
        # add team stats header
        embed.add_field(name="_ _", value=self.team_stats_header, inline=False)

        # add team stats
        for team_name, team_stats in total_team_stats.items():
            formatted_team_stats = self.format_team_stats(team_stats, num_games, **kwargs)
            embed.add_field(name=team_name, value=formatted_team_stats, inline=True)
        
        notes = self.format_notes(**kwargs)
        if notes:
            notes_header = self.notes_header
            if notes_header is None:
                _notes = notes
            else:
                _notes = f"{self.notes_header}\n{notes}"
            embed.add_field(name="_ _", value=_notes, inline=False)
        
        return embed
