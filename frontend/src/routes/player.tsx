import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/player")({
  component: Player,
});

function PlayerData() {
  const { playerId } = Route.useSearch();
  const { isPending, error, data } = useQuery({
    queryKey: ["player", playerId],
    queryFn: () =>
      fetch(`/api/player/${encodeURIComponent(playerId)}`).then((res) =>
        res.json(),
      ),
  });
  if (isPending) return "Loading...";
  if (error) return error.message;
  return (
    <div>
      <p>
        {data.riot_user_name}#{data.riot_tag_line}
      </p>
    </div>
  );
}

function MatchData() {
  const { playerId } = Route.useSearch();
  const { isPending, error, data } = useQuery({
    queryKey: ["matches", playerId],
    queryFn: () =>
      fetch(`/api/match/${encodeURIComponent(playerId)}`).then((res) =>
        res.json(),
      ),
  });
  if (isPending) return "Loading...";
  if (error) return error.message;
  return (
    <div className="flex flex-col gap-y-4">
      <div>
        <p>{data.length} matches</p>
      </div>
      <div>
        {data.map((match) => (
          <div
            key={match.match_id}
            className="flex flex-row mb-4 border-2 border-slate-400 "
          >
            <div className="flex flex-col">
              <span>
                {new Date(match.match_creation_time).toLocaleDateString(
                  "en-GB",
                  {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  },
                )}
              </span>
              <span>
                {Math.floor(match.match_duration_seconds / 60)}m{" "}
                {match.match_duration_seconds % 60}s
              </span>
              <span>{match.queue_type}</span>
            </div>
            <MatchDetail matchId={match.match_id} />
            <div className="grid grid-cols-2">
              {match.player_ids.map((i) => (
                <span className="max-w-32 truncate">{i}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MatchDetail({ matchId }) {
  const { playerId } = Route.useSearch();
  const { isPending, error, data } = useQuery({
    queryKey: ["matchDetails", matchId, playerId],
    queryFn: () =>
      fetch(
        `/api/match_detail/${matchId}/${encodeURIComponent(playerId)}`,
      ).then((res) => res.json()),
  });
  if (isPending) return "Loading...";
  if (error) return error.message;
  return (
    <div className="flex flex-grow max-w-xl">
      <div className="items-center h-24 flex">
        <div className="relative">
          <img
            src={`${import.meta.env.VITE_ASSETS_URL}/champion/${data.champion_id}.png`}
            alt=""
            width={64}
            loading="lazy"
          />
          <span className="absolute bottom-0 right-0 text-white backdrop-blur-sm">
            {data.level}
          </span>
        </div>
        <div className="h-16 grid grid-cols-2">
          <img
            src={`${import.meta.env.VITE_ASSETS_URL}/summoner-spell/${data.summoner_spells[0]}.png`}
            width={32}
          />
          <img
            src={`${import.meta.env.VITE_ASSETS_URL}/rune-style/${data.primary_style}.png`}
            width={32}
          />
          <img
            src={`${import.meta.env.VITE_ASSETS_URL}/summoner-spell/${data.summoner_spells[1]}.png`}
            width={32}
          />
          <img
            src={`${import.meta.env.VITE_ASSETS_URL}/rune-style/${data.sub_style}.png`}
            width={32}
          />
        </div>
      </div>
      <div className="flex flex-col">
        <span>
          {data.kills} / {data.deaths} / {data.assists}
        </span>
        <span>
          {(data.kills + data.assists) / Math.max(data.deaths, 1)} KDA
        </span>
        <div className="grid grid-cols-7 max-w-fit">
          {data.items.map((item) => (
            <img
              src={`${import.meta.env.VITE_ASSETS_URL}/item/${item}.png`}
              width={32}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Player() {
  return (
    <div className="flex flex-col border-2 gap-y-10">
      <PlayerData />
      <MatchData />
    </div>
  );
}

export default Player;
