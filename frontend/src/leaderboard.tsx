import { useQuery } from "@tanstack/react-query"

function LeaderboardData() {
  const { isPending, error, data } = useQuery({
    queryKey: ["leaderboard"],
    queryFn: () => fetch("/api/leaderboard").then((res) => res.json()),
  });

  if (isPending) return "Loading...";

  if (error) return error.message;

  return <p>Got {data.length} matches</p>;
}

function Leaderboard() {
  return <>
    <LeaderboardData />
  </>
}

export default function Leaderboard;
