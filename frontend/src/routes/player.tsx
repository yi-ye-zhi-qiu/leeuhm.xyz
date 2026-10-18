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
    <div>
      <p>{data.length} matches</p>
      <table>
        <thead>
          <tr>
            <th>Match Id</th>
          </tr>
        </thead>
        <tbody>
          {data.map((match) => (
            <tr key={match.match_id}>
              {match.match_id}
              <MatchDetail matchId={match.match_id} />
            </tr>
          ))}
        </tbody>
      </table>
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
    <div>
      <p>match details: {JSON.stringify(data)}</p>
    </div>
  );
}

function Player() {
  return (
    <>
      <PlayerData />
      <MatchData />
    </>
  );
}

export default Player;
