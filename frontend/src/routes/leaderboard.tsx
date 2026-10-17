import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/leaderboard")({
  component: Leaderboard,
});

function LeaderboardData() {
  const { region, pageIndex } = Route.useSearch();

  const { isPending, error, data } = useQuery({
    queryKey: ["leaderboard", region, pageIndex],
    queryFn: () =>
      fetch(`/api/leaderboard/${region}/${pageIndex}`).then((res) =>
        res.json(),
      ),
  });

  if (isPending) return "Loading...";

  if (error) return error.message;

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Summoner</th>
            <th>Tier</th>
            <th>LP</th>
            <th>Level</th>
            <th>Win Rate</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((player) => (
            <tr key={player.player_id}>
              <td>
                {player.riot_user_name}#{player.riot_tag_line}
              </td>
              <td>{player.tier}</td>
              <td>{player.lp}</td>
              <td>{player.summoner_level}</td>
              <td>
                {player.wins} / {player.wins + player.losses}
                {player.win_rate}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h1>
        Page {pageIndex} of {Math.max(1, data.total % 100)} ({data.total}{" "}
        summoners)
      </h1>
    </div>
  );
}

function Leaderboard() {
  const { region, pageIndex } = Route.useSearch();

  return (
    <>
      <p>
        Leaderboard data, region = {region} and pageIndex = {pageIndex}
      </p>
      <LeaderboardData />
    </>
  );
}

export default Leaderboard;
