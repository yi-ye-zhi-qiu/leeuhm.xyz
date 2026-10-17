import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/player")({
  component: Player,
});

function PlayerData() {
  const { playerId } = Route.useParams();

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
      <p>{data.userName}</p>
    </div>
  );
}

function MatchData() {
  const { isPending, error, data } = useQuery({
    queryKey: ["matchData"],
    queryFn: () => fetch("/api/matchData").then((res) => res.json()),
  });

  if (isPending) return "Loading...";

  if (error) return error.message;

  return (
    <div>
      <p>{data.length} matches from this player</p>
    </div>
  );
}

function MatchDetails() {
  const { isPending, error, data } = useQuery({
    queryKey: ["matchDetails"],
    queryFn: () => fetch("/api/matchDetails").then((res) => res.json()),
  });

  if (isPending) return "Loading...";

  if (error) return error.message;

  return (
    <div>
      <p>match details here</p>
    </div>
  );
}

function Player() {
  return (
    <>
      <PlayerData />
      <MatchData />
      <MatchDetails />
    </>
  );
}

export default Player;
